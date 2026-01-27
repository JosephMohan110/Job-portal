import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .voice_core import VoiceAssistantCore

# Global voice assistant instance
voice_assistant = VoiceAssistantCore()

@csrf_exempt
@require_POST
def process_voice_command(request):
    """API endpoint to process voice commands"""
    try:
        data = json.loads(request.body)
        command_text = data.get('command', '').strip()
        current_url = data.get('current_url', request.build_absolute_uri('/'))
        
        if not command_text:
            return JsonResponse({
                'success': False,
                'error': 'No command provided'
            })
        
        # Process command directly
        response = voice_assistant.process_command(command_text, current_url)
        
        return JsonResponse({
            'success': True,
            'response': response
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_POST
def start_voice_session(request):
    """API endpoint to start voice assistant session (Client-side init)"""
    # Simply acknowledge receipt; the client handles the actual listening
    return JsonResponse({
        'success': True,
        'message': 'Voice session ready'
    })

@csrf_exempt
@require_POST
def stop_voice_session(request):
    """API endpoint to stop voice assistant"""
    return JsonResponse({
        'success': True,
        'message': 'Voice assistant stopped'
    })
