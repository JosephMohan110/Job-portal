from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .chatbot import get_chat_response, chatbot

def chat_bot(request):
    """Render the chatbot page"""
    return render(request, 'chat_bot/chat_bot.html')

@csrf_exempt
@require_POST
def chat_api(request):
    """API endpoint for chatbot responses"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'No message provided'
            })
        
        # Get response from chatbot
        response = get_chat_response(user_message)
        
        # Get suggestions for similar questions
        suggestions = chatbot.get_suggestions(user_message, n_suggestions=3)
        
        return JsonResponse({
            'success': True,
            'response': response,
            'user_message': user_message,
            'suggestions': suggestions if response.startswith("I'm sorry") else []
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })