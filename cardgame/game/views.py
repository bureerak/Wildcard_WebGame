from django.shortcuts import render

# Create your views here.

def in_game(request):
    return render(request, 'board/lobby.html')

def home_page(request):
    return render(request, 'home/main.html')