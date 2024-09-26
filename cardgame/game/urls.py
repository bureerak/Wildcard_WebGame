from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home'),
    path('<str:room_name>/<str:username>/', views.in_game, name='in_game')
]
