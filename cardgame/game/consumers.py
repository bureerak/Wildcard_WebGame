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
        # ส่งข้อมูลการ์ดไปยัง WebSocket ของผู้เล่น
        await self.send(text_data=json.dumps({
            "type": "hands_update",
            "hands": hands
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
