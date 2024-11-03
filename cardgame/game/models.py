from django.db import models
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
# Create your models here.

class Room(models.Model):
    room_name = models.CharField(max_length=50)
    data = models.JSONField(default=dict)
    deck = models.JSONField(default=list)  # เก็บการ์ดทั้งหมดในสำรับ
    discard_pile = models.JSONField(default=list)  # เก็บการ์ดที่เล่นแล้ว

    last_joined = models.DateTimeField(auto_now=True)

    def initialize_deck(self):
        """ฟังก์ชันสำหรับสร้างการ์ดใน Deck"""
        deck = []
        colors = ["red", "blue", "green", "yellow"]
        
        for color in colors:
            # การ์ด 0 มี 1 ใบต่อสี
            deck.append({'color': color, 'number': 0})
            # การ์ด 1-9 มีอย่างละ 2 ใบต่อสี
            for number in range(1, 13):
                deck.append({'color': color, 'number': number})
                deck.append({'color': color, 'number': number})
        
        random.shuffle(deck)
        self.deck = deck
        self.save()

    def deal_cards(self, num_cards=7):
        """ฟังก์ชันสำหรับแจกการ์ดให้ผู้เล่นแต่ละคนเมื่อมีผู้เล่นครบ 4 คน"""
        players = self.data.get("players", [])
        if len(players) < 4:
            return  # รอจนกว่าจะมีผู้เล่นครบ 4 คน
        for player in players:
            player_hand = []
            for _ in range(num_cards):
                card = self.deck.pop()
                player_hand.append(card)
            self.data[player] = player_hand
        self.save()

    def __str__(self):
        return self.room_name

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    sender = models.CharField(max_length=50)
    message = models.TextField()

    def __str__(self):
        return f"{self.room} - {self.sender}"
