import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Message
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_name']}"
        self.user_name = self.scope['session'].get("username")

        # ดึงห้องจากฐานข้อมูลแล้วเพิ่มชื่อผู้เล่น
        await self.add_player_to_room()
        await self.update_players()

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        room = await sync_to_async(Room.objects.get)(room_name=self.room_name[5:])
        players = room.data.get("players", [])
        # ตรวจสอบว่าผู้เล่นครบ 4 คนหรือยัง
        if len(players) == 4 and not room.data.get(self.user_name, []):
            # เรียกใช้ deal_cards เมื่อผู้เล่นครบ 4 คน
            await sync_to_async(room.deal_cards)()

            # ส่งข้อมูลการ์ดให้ผู้เล่นผ่าน WebSocket
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "send_hand",
                    "hands": room.data,
                    "fst":room.turn_list[room.current_turn]
                }
            )


    async def disconnect(self, code):
        await self.remove_player_from_room()
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        await self.update_players()
        # เริ่มตั้งเวลา 3 วินาทีเพื่อตรวจสอบการลบห้อง
        await self.wait_and_delete_room_if_empty()
        self.close(code)

    async def receive(self, text_data):
        data_json = json.loads(text_data)
        if data_json.get("message",None) != None:
            event = {
                "type": "send_message",
                "message": data_json,
            }
            await self.channel_layer.group_send(self.room_name, event)

        elif data_json.get("cardid",None) != None:
            room = await database_sync_to_async(Room.objects.get)(room_name=self.room_name[5:])
            cardid = data_json["cardid"]
            cardtype = data_json["cardtype"]
            username = data_json["username"]

            playerid = room.turn_list
            playerid = playerid.index(username)

            success = await sync_to_async(room.play_card)(playerid, username, cardtype)
            room = await database_sync_to_async(Room.objects.get)(room_name=self.room_name[5:])
            if success:
                # ส่งข้อมูลอัปเดตไปยังผู้เล่นทุกคน
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'update_game_state',
                        'cardid': cardid,
                        'current_turn': room.turn_list[room.current_turn],
                        'username':username,
                        'center':room.center['prob']
                    }
                )
            else:
                await self.channel_layer.group_send(self.room_name,{'type': 'error','spec':'card','username':username,'cardid': cardid,})

        elif data_json.get("action",None) != None:
            username = data_json["username"]
            room = await database_sync_to_async(Room.objects.get)(room_name=self.room_name[5:])

            playerid = room.turn_list
            playerid = playerid.index(username)
            success = await sync_to_async(room.draw_card)(playerid, username)
            room = await database_sync_to_async(Room.objects.get)(room_name=self.room_name[5:])
            if success:
                await self.channel_layer.group_send(
                    self.room_name,
                    {
                        'type': 'update_card_by_user',
                        'username': username,
                        'hand': room.data.get(username,[]),
                        'current_turn': room.turn_list[room.current_turn],
                    }
                )
            else:
                await self.channel_layer.group_send(self.room_name,{'type': 'error','spec':'not_turn','username':username})

    async def error(self,event):
        """ Error send """
        cardid = event.get('cardid',[])
        await self.send(text_data=json.dumps({
            'type': 'error',
            'spec': event['spec'],
            'username': event['username'],
            'cardid': cardid
        }))

    async def update_card_by_user(self,event):
        """ function นี้เพื่ออัพเดทการ์ดบนมือคนจั่ว """
        await self.send(text_data=json.dumps({
            'type': 'draw_update',
            'username': event['username'],
            'hand' : event['hand'],
            'current_turn' : event['current_turn'],
        }))

    async def update_game_state(self, event):
        # ส่งข้อมูลอัปเดตไปยัง frontend
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'cardid': event['cardid'],
            'current_turn': event['current_turn'],
            'username': event['username'],
            "center": event["center"],
        }))

    async def update_players(self):
        room = await database_sync_to_async(Room.objects.get)(room_name=self.room_name[5:])
        players = room.data.get("players", [])

        # ส่งข้อมูลรายชื่อผู้เล่นไปยังทุกคนในห้อง
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "player_list",
                "players": players
            }
        )

    # ฟังก์ชัน handler สำหรับการส่งรายชื่อผู้เล่นไปยัง frontend
    async def player_list(self, event):
        players = event["players"]
        await self.send(text_data=json.dumps({
            "type": "player_list",
            "players": players
        }))

    async def send_hand(self, event):
        hands = event["hands"]
        fst = event["fst"]
        # ส่งข้อมูลการ์ดไปยัง WebSocket ของผู้เล่น
        await self.send(text_data=json.dumps({
            "type": "hands_update",
            "hands": hands,
            "fst": fst,
        }))

    async def send_message(self, event):
        data = event["message"]
        await self.create_message(data=data)
        response = {
            "sendman": data["sendman"],
            "message": data["message"],
        }
        await self.send(text_data=json.dumps({
            "type": "send_message",
            "message": response
        }))
    
    async def wait_and_delete_room_if_empty(self):
        """รอ 3 วินาที แล้วตรวจสอบว่าห้องว่างหรือไม่ ถ้าว่างก็ลบห้อง"""
        await asyncio.sleep(5)  # รอ 5 วินาที
        await self.delete_room_if_empty()

    @database_sync_to_async
    def create_message(self, data):
        get_room = Room.objects.get(room_name=data['room_name'])
        if not Message.objects.filter(message=data['message'], sender=data["sendman"]).exists():
            new_message = Message.objects.create(room=get_room, message=data["message"], sender=data["sendman"])

    @database_sync_to_async
    def remove_player_from_room(self):
        """ลบชื่อผู้เล่นออกจากฟิลด์ JSON ของห้อง"""
        try:
            room = Room.objects.get(room_name=self.room_name[5:])
            players = room.data.get("players", [])
            if self.user_name in players:
                players.remove(self.user_name)
                room.data["players"] = players
                room.save()
        except Room.DoesNotExist:
            pass

    @database_sync_to_async
    def delete_room_if_empty(self):
        """ลบห้องออกหากไม่มีผู้เล่นเหลืออยู่"""
        try:
            room = Room.objects.get(room_name=self.room_name[5:])
            if not room.data.get("players"):  # ตรวจสอบว่าไม่มีผู้เล่นเหลืออยู่
                room.delete()
        except Room.DoesNotExist:
            pass

    @database_sync_to_async
    def add_player_to_room(self):
        """เพิ่มชื่อผู้เล่นลงในฟิลด์ JSON ของห้อง"""
        room = Room.objects.get(room_name=self.room_name[5:])
        players = room.data.get("players", [])
        if self.user_name not in players:
            players.append(self.user_name)
            room.data["players"] = players
            room.save()
