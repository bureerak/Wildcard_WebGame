from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home'),
    path('rule', views.rule_page, name='rule'),
    path('project', views.project_page, name='project'),
    path('<str:room_name>/<str:username>/', views.in_game, name='in_game')
]
