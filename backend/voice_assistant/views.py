from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .command_handler import process_voice_command, start_voice_session, stop_voice_session
from .voice_core import VoiceAssistantCore

def voice_assistant_widget(request):
    """Render the voice assistant widget"""
    return render(request, 'voice_assistant/voice_widget.html')

@csrf_exempt
def voice_api(request):
    """Main API endpoint for voice assistant"""
    if request.method == 'POST':
        action = request.GET.get('action', 'process')
        
        if action == 'start':
            return start_voice_session(request)
        elif action == 'stop':
            return stop_voice_session(request)
        else:
            return process_voice_command(request)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def get_available_commands(request):
    """Get list of available voice commands"""
    assistant = VoiceAssistantCore()
    
    # Group commands by category
    categories = {
        'Navigation': ['go to [page]', 'open [page]', 'take me to [page]', 'show [page]'],
        'Forms': ['enter [value] in [field]', 'my [field] is [value]', 'username is [value]'],
        'Explanations': ['explain [page]', 'what is [page]', 'tell me about [page]'],
        'Actions': ['submit', 'login', 'register', 'search for [term]', 'click [button]'],
        'General': ['hello', 'help', 'stop', 'what can you do']
    }
    
    # Get all page names
    pages = list(assistant.url_mappings.keys())
    
    return JsonResponse({
        'categories': categories,
        'pages': pages,
        'examples': [
            "Say 'go to login page'",
            "Say 'my username is john' then 'submit'",
            "Say 'explain the dashboard'",
            "Say 'help' for more options"
        ]
    })