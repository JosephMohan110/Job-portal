from django.apps import AppConfig

class VoiceAssistantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'voice_assistant'
    
    def ready(self):
        # Initialize voice assistant when app starts
        try:
            from .voice_core import VoiceAssistantCore
            assistant = VoiceAssistantCore()
            print("Voice Assistant initialized successfully")
        except Exception as e:
            print(f"Voice Assistant initialization failed: {e}")