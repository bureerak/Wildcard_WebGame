from django.urls import path
from .consumers import ChatConsumer
from channels.sessions import SessionMiddlewareStack
from channels.auth import AuthMiddlewareStack
from . import consumers

wsPattern = [
    path("ws/messages/<str:room_name>/", SessionMiddlewareStack(AuthMiddlewareStack(consumers.ChatConsumer.as_asgi())))
]