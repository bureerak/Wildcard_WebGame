from django.db import models
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.utils import timezone
# Create your models here.

def default_rule():
    return {
        "Green":[1,2,3,4,5],
        "Gray":[1,6,7,8,9],
        "Orange":[2,6,10,11,12],
        "Yellow":[3,7,10,13,14],
        "Purple":[4,8,11,13,15],
        "Blue":[5,9,12,14,15]
        }

class Room(models.Model):
    room_name = models.CharField(max_length=50)
    problem_card = models.JSONField(default=list)
    center = models.JSONField(default=list) #เก็บ card ตรงกลาง
    data = models.JSONField(default=dict)  # ข้อมูลรายชื่อ และ ข้อมูลการถือไพ่ของแต่ละคน
    deck = models.JSONField(default=list)  # เก็บการ์ดทั้งหมดในสำรับ
    discard_pile = models.JSONField(default=list)  # เก็บการ์ดที่เล่นแล้ว
    last_joined = models.DateTimeField(auto_now=True) # เวลา join ครั้งล่าสุด
    turn_list = models.JSONField(default=list) # ลำดับรายชื่อ 
    current_turn = models.IntegerField(default=0)  # ลำดับผู้เล่นที่ถึงตา
    rule = models.JSONField(default=default_rule)
    score = models.JSONField(default=dict)

    def draw_card(self, player_id, username):
        if self.current_turn == player_id:
            self.data[username].append(self.deck.pop())
            self.current_turn = (self.current_turn + 1) % 4 # เปลี่ยนเทิร์น
            self.save()
            return True
        return False


    def play_card(self, player_id, username, card):
        card = int(card)
        center_card = self.center
        center_card = center_card['prob']
        rule_use = self.rule
        rule_use = rule_use[center_card]
        if self.current_turn == player_id and card in rule_use: #เงื่อนไขว่าตรงกับกองตรงกลางมั้ยใส่ตรงนี้
            self.data[username].remove({"type":card}) #ลบไพ่ออกจากมือผู้เล่น
            self.score[username] += 2
            self.current_turn = (self.current_turn + 1) % 4 # เปลี่ยนเทิร์น
            if self.problem_card:
                self.center = self.problem_card.pop()
            else:
                self.center = {'prob':'end'}
            self.save()
            return True  # เพื่อบอกว่าการลงไพ่สำเร็จ
        return False  # หากยังไม่ถึงตาผู้เล่น

    def initialize_deck(self):
        """ฟังก์ชันสำหรับสร้างการ์ดใน Deck"""
        color, deck, prop_deck = ["Green","Gray","Orange","Yellow","Purple","Blue"], [], []
        for i in range(1,16):
            deck.append({'type': i})
            deck.append({'type': i})
        for i in color:
            prop_deck.append({'prob':i})
            prop_deck.append({'prob':i})
        random.shuffle(prop_deck)
        random.shuffle(deck)
        self.center = prop_deck.pop()
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
            self.score[player] = 0
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
    time = models.DateTimeField(auto_now=True)

    def formatted_time(self):
        local_time = timezone.localtime(self.time)
        return local_time.strftime('%H:%M')

    def __str__(self):
        return f"{self.room} - {self.sender}"
