import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_name']}"
        self.user_name = self.scope['session'].get("username")
        await self.channel_layer.group_add(self.room_name, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        await self.remove_player_from_room()
        await self.delete_room_if_empty()
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        self.close(code)

    async def receive(self, text_data):
        data_json = json.loads(text_data)

        event = {
            "type" : "send_message",
            "message" : data_json,
        }

        await self.channel_layer.group_send(self.room_name, event)
    
    async def send_message(self, event):
        data = event["message"]
        await self.create_message(data = data)

        response = {
            "sendman":data["sendman"],
            "message":data["message"],
        }

        await self.send(text_data=json.dumps({"message":response}))
    
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