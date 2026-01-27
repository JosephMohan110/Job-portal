from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_bot, name='chat_bot'),
    path('api/', views.chat_api, name='chat_api'),
]