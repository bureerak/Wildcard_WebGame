from django.shortcuts import render, redirect, HttpResponse
from .models import Room, Message

# Create your views here.

def rule_page(request):
    return render(request, 'stream/rule.html')

def project_page(request):
    return render(request, 'stream/project.html')

def home_page(request):
    if request.method == "POST":
        username = request.POST["username"]
        room = request.POST["room"]

        try:
            existing_room = Room.objects.get(room_name=room)
        except Room.DoesNotExist:
            # สร้างห้องใหม่ถ้าไม่มีห้องนี้อยู่
            existing_room = Room.objects.create(room_name=room)
            existing_room.initialize_deck()

        # ตรวจสอบจำนวนผู้เล่นและชื่อซ้ำกัน
        players = existing_room.data.get("players", [])
        if len(players) >= 4:
            # ส่งข้อความแจ้งเตือนเมื่อห้องเต็ม
            return render(request, 'stream/index.html', {
                "message": {
                    "icon": "error",
                    "title": "ห้องเต็ม",
                    "text": "ห้องนี้เต็มแล้ว ไม่สามารถเข้าร่วมได้"
                }
            })
        elif username in players:
            # ส่งข้อความแจ้งเตือนเมื่อชื่อซ้ำ
            return render(request, 'stream/index.html', {
                "message": {
                    "icon": "error",
                    "title": "ชื่อซ้ำ",
                    "text": "มีผู้ใช้ชื่อนี้ในห้องแล้ว กรุณาใช้ชื่ออื่น"
                }
            })

        request.session["username"] = username # บันทึกชื่อผู้เล่นลงใน session

        # เปลี่ยนเส้นทางไปยัง in_game view
        return redirect("in_game", room_name=room, username=username)
        
    return render(request, 'stream/index.html')

def in_game(request, room_name, username):
    existing_room = Room.objects.get(room_name=room_name)
    get_message = Message.objects.filter(room=existing_room)
    players = existing_room.data.get("players", [])
    context = {
        "messages":get_message,
        "username":username,
        "room_name":existing_room.room_name,
        "players":players,
    }
    return render(request, 'stream/game.html', context)
