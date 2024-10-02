from django.shortcuts import render, redirect
from .models import Room, Message

# Create your views here.

def home_page(request):
    if request.method == "POST":
        username = request.POST["username"]
        room = request.POST["room"]
        try:
            existing_room = Room.objects.get(room_name=room)
        except Room.DoesNotExist:
            r = Room.objects.create(room_name=room)
        return redirect("in_game", room_name = room, username = username)
    return render(request, 'stream/index.html')

def in_game(request, room_name, username):
    existing_room = Room.objects.get(room_name=room_name)
    get_message = Message.objects.filter(room=existing_room)
    context = {
        "messages":get_message,
        "username":username,
        "room_name":existing_room.room_name,
    }
    return render(request, 'stream/game.html', context)
