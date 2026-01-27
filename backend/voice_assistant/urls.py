from django.urls import path
from . import views

urlpatterns = [
    path('widget/', views.voice_assistant_widget, name='voice_assistant_widget'),
    path('api/', views.voice_api, name='voice_api'),
    path('api/commands/', views.get_available_commands, name='voice_commands'),
]