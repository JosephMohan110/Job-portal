# message_system/urls.py

from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [

    path('', views.message_dashboard, name='message_dashboard'),
    
    # Chat room
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    
    # Start new chat
    path('start/', views.start_chat, name='start_chat'),
    
    # Message actions
    path('delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('edit/<int:message_id>/', views.edit_message, name='edit_message'),
    
    # Notifications
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    
    # Chat management
    path('close/<int:room_id>/', views.close_chat, name='close_chat'),
    path('clear/<int:room_id>/', views.clear_chat, name='clear_chat'),
    
    # AJAX endpoints
    path('send/', views.send_message, name='send_message'),
    path('get-new/<int:room_id>/', views.get_new_messages, name='get_new_messages'),


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)