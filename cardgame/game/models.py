from django.db import models
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
# Create your models here.

class Room(models.Model):
    room_name = models.CharField(max_length=50)
    problem_card = models.JSONField(default=list)
    data = models.JSONField(default=dict)  # ข้อมูลรายชื่อ และ ข้อมูลการถือไพ่ของแต่ละคน
    deck = models.JSONField(default=list)  # เก็บการ์ดทั้งหมดในสำรับ
    discard_pile = models.JSONField(default=list)  # เก็บการ์ดที่เล่นแล้ว
    last_joined = models.DateTimeField(auto_now=True) # เวลา join ครั้งล่าสุด
    turn_list = models.JSONField(default=list) # ลำดับรายชื่อ 
    current_turn = models.IntegerField(default=0)  # ลำดับผู้เล่นที่ถึงตา

    def initialize_deck(self):
        """ฟังก์ชันสำหรับสร้างการ์ดใน Deck"""
        color = ["Green","Gray","Orange","Yellow","Purple","Blue"]
        color_pairs = [
        ("Green", "Gray"),
        ("Green", "Orange"),
        ("Green", "Yellow"),
        ("Green", "Purple"),
        ("Green", "Blue"),
        ("Gray", "Orange"),
        ("Gray", "Yellow"),
        ("Gray", "Purple"),
        ("Gray", "Blue"),
        ("Orange", "Yellow"),
        ("Orange", "Purple"),
        ("Orange", "Blue"),
        ("Yellow", "Purple"),
        ("Yellow", "Blue"),
        ("Purple", "Blue")]
        deck = []
        prop_deck = []
        for color1,color2 in color_pairs:
            deck.append({'color1': color1, 'color2': color2})
            deck.append({'color1': color1, 'color2': color2})
        for i in color:
            prop_deck.append({'prob':i})
            prop_deck.append({'prob':i})
        random.shuffle(prop_deck)
        random.shuffle(deck)
        self.deck = deck
        self.problem_card = prop_deck
        self.save()

    def deal_cards(self, num_cards=3):
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
        turn = players.copy()
        random.shuffle(turn)
        self.turn_list = turn
        self.save()

    def __str__(self):
        return self.room_name

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    sender = models.CharField(max_length=50)
    message = models.TextField()

    def __str__(self):
        return f"{self.room} - {self.sender}"
