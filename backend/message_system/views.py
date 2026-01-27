# message_system/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import json

from .models import ChatRoom, Message, ChatNotification
from employer.models import Employer
from employee.models import Employee, JobRequest

# Custom decorator to check user session
def check_user_session(view_func):
    """Custom decorator to check user session instead of Django auth"""
    def wrapper(request, *args, **kwargs):
        # Check if user is logged in (has session)
        if not (request.session.get('employer_id') or request.session.get('employee_id')):
            messages.info(request, 'Please login to access messages')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


@check_user_session
def message_dashboard(request):
    """Main messaging dashboard view"""
    try:
        # Get user info from session
        user_info = {}
        chat_rooms_list = []
        
        # Check if employer is logged in
        employer_id = request.session.get('employer_id')
        if employer_id:
            employer = get_object_or_404(Employer, employer_id=employer_id)
            user_info = {
                'type': 'employer',
                'name': f"{employer.first_name} {employer.last_name}",
                'id': employer.employer_id,
                'avatar': employer.profile_image.url if employer.profile_image else None
            }
            
            # Get chat rooms for employer
            chat_rooms = ChatRoom.objects.filter(
                employer=employer
            ).select_related(
                'employee', 'job'
            ).prefetch_related(
                'messages'
            ).order_by('-last_message_time')
            
            # Process chat rooms for template
            for room in chat_rooms:
                last_message = room.messages.order_by('-created_at').first()
                room_data = {
                    'room': room,
                    'room_id': room.room_id,  # Explicitly include room_id
                    'last_message_content': last_message.content[:50] if last_message else "No messages yet",
                    'last_activity': last_message.created_at if last_message else room.created_at,
                    'employee': room.employee,
                    'employer': room.employer,
                    'subject': room.subject,
                    'unread_employer': room.unread_employer,
                    'unread_employee': room.unread_employee,
                }
                chat_rooms_list.append(room_data)
                    
        # Check if employee is logged in
        employee_id = request.session.get('employee_id')
        if employee_id:
            employee = get_object_or_404(Employee, employee_id=employee_id)
            user_info = {
                'type': 'employee',
                'name': f"{employee.first_name} {employee.last_name}",
                'id': employee.employee_id,
                'avatar': employee.profile_image.url if employee.profile_image else None
            }
            
            # Get chat rooms for employee
            chat_rooms = ChatRoom.objects.filter(
                employee=employee
            ).select_related(
                'employer', 'job'
            ).prefetch_related(
                'messages'
            ).order_by('-last_message_time')
            
            # Process chat rooms for template
            for room in chat_rooms:
                last_message = room.messages.order_by('-created_at').first()
                room_data = {
                    'room': room,
                    'room_id': room.room_id,  # Explicitly include room_id
                    'last_message_content': last_message.content[:50] if last_message else "No messages yet",
                    'last_activity': last_message.created_at if last_message else room.created_at,
                    'employee': room.employee,
                    'employer': room.employer,
                    'subject': room.subject,
                    'unread_employer': room.unread_employer,
                    'unread_employee': room.unread_employee,
                }
                chat_rooms_list.append(room_data)
        
        if not user_info:
            messages.error(request, "Please login to access messages")
            return redirect('index')
        
        context = {
            'user_info': user_info,
            'chat_rooms': chat_rooms_list,
            'active_room': request.GET.get('room_id')
        }
        
        return render(request, 'message_system/message_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading messages: {str(e)}")
        return redirect('index')


@check_user_session
def chat_room(request, room_id):
    """Individual chat room view"""
    try:
        # Get chat room
        chat_room_obj = get_object_or_404(ChatRoom, room_id=room_id)
        
        # Check if user has access to this chat
        user_has_access = False
        other_user_info = {}
        user_info = {}
        
        employer_id = request.session.get('employer_id')
        employee_id = request.session.get('employee_id')
        
        if employer_id:
            employer = get_object_or_404(Employer, employer_id=employer_id)
            if chat_room_obj.employer == employer:
                user_has_access = True
                employee = chat_room_obj.employee
                other_user_info = {
                    'id': employee.employee_id,
                    'full_name': f"{employee.first_name} {employee.last_name}",
                    'first_name': employee.first_name,
                    'last_name': employee.last_name,
                    'profile_image': employee.profile_image,
                    'user_type': 'employee'
                }
                user_info = {
                    'type': 'employer',
                    'id': employer.employer_id,
                    'name': f"{employer.first_name} {employer.last_name}",
                    'full_name': f"{employer.first_name} {employer.last_name}",
                }
                # Mark employer messages as read
                chat_room_obj.mark_as_read('employer')
                
        elif employee_id:
            employee = get_object_or_404(Employee, employee_id=employee_id)
            if chat_room_obj.employee == employee:
                user_has_access = True
                employer = chat_room_obj.employer
                other_user_info = {
                    'id': employer.employer_id,
                    'full_name': f"{employer.first_name} {employer.last_name}",
                    'first_name': employer.first_name,
                    'last_name': employer.last_name,
                    'profile_image': employer.profile_image,
                    'user_type': 'employer'
                }
                user_info = {
                    'type': 'employee',
                    'id': employee.employee_id,
                    'name': f"{employee.first_name} {employee.last_name}",
                    'full_name': f"{employee.first_name} {employee.last_name}",
                }
                # Mark employee messages as read
                chat_room_obj.mark_as_read('employee')
        
        if not user_has_access:
            messages.error(request, "You don't have permission to access this chat")
            return redirect('message_dashboard')
        
        # Get messages with date grouping
        all_messages = chat_room_obj.messages.filter(is_deleted=False).order_by('created_at')
        
        # Format messages for template
        messages_list = []
        current_date = None
        
        for msg in all_messages:
            msg_date = msg.created_at.date()
            
            # Add date separator if date changed
            if msg_date != current_date:
                current_date = msg_date
                if msg_date == timezone.now().date():
                    date_str = "Today"
                elif msg_date == timezone.now().date() - timedelta(days=1):
                    date_str = "Yesterday"
                else:
                    date_str = msg_date.strftime("%B %d, %Y")
                
                messages_list.append({
                    'date_separator': date_str,
                    'is_separator': True
                })
            
            # Determine if message is sent by current user
            is_sent = False
            sender_name = ""
            
            if msg.sender_type == 'employer' and msg.sender_employer:
                sender_name = f"{msg.sender_employer.first_name} {msg.sender_employer.last_name}"
                if employer_id and msg.sender_employer.employer_id == employer_id:
                    is_sent = True
            elif msg.sender_type == 'employee' and msg.sender_employee:
                sender_name = f"{msg.sender_employee.first_name} {msg.sender_employee.last_name}"
                if employee_id and msg.sender_employee.employee_id == employee_id:
                    is_sent = True
            
            # Add message
            messages_list.append({
                'id': msg.message_id,
                'content': msg.content,
                'sender_id': msg.sender_employer.employer_id if msg.sender_type == 'employer' else msg.sender_employee.employee_id,
                'sender_type': msg.sender_type,
                'sender_name': sender_name,
                'timestamp': msg.created_at,
                'is_edited': msg.is_edited,
                'is_deleted': msg.is_deleted,
                'message_type': msg.message_type,
                'is_sent': is_sent
            })
        
        # Get job details if exists
        job = None
        if chat_room_obj.job:
            job = {
                'id': chat_room_obj.job.job_id,
                'title': chat_room_obj.job.title,
                'category': getattr(chat_room_obj.job.category, 'name', "General") if chat_room_obj.job.category else "General",
                'budget': chat_room_obj.job.budget,
                'status': chat_room_obj.job.status
            }
        
        # Calculate chat duration
        chat_duration = "Ongoing"
        if chat_room_obj.created_at:
            duration = timezone.now() - chat_room_obj.created_at
            if duration.days > 0:
                chat_duration = f"{duration.days} days"
            elif duration.seconds // 3600 > 0:
                chat_duration = f"{duration.seconds // 3600} hours"
            else:
                chat_duration = f"{duration.seconds // 60} minutes"
        
        context = {
            'chat_room': chat_room_obj,
            'messages': messages_list,
            'other_user': other_user_info,
            'user_info': user_info,
            'job': job,
            'total_messages': all_messages.count(),
            'chat_duration': chat_duration
        }
        
        return render(request, 'message_system/chat_room.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading chat: {str(e)}")
        return redirect('message_dashboard')


@check_user_session
def start_chat(request):
    """Start a new chat view"""
    try:
        user_info = {}
        suggestions = []
        
        employer_id = request.session.get('employer_id')
        employee_id = request.session.get('employee_id')
        
        if employer_id:
            employer = get_object_or_404(Employer, employer_id=employer_id)
            user_info = {
                'type': 'employer',
                'name': f"{employer.first_name} {employer.last_name}",
                'id': employer.employer_id,
                'avatar': employer.profile_image.url if employer.profile_image else None
            }
            
            # Get recent employees from chat history
            recent_chats = ChatRoom.objects.filter(
                employer=employer
            ).select_related('employee').order_by('-last_message_time')[:10]
            
            for chat in recent_chats:
                suggestions.append({
                    'id': chat.employee.employee_id,
                    'name': f"{chat.employee.first_name} {chat.employee.last_name}",
                    'avatar': chat.employee.profile_image.url if chat.employee.profile_image else None,
                    'job_title': "Previous contact"
                })
            
            # If no recent chats, get all active employees
            if not suggestions:
                employees = Employee.objects.filter(is_active=True)[:10]
                for emp in employees:
                    suggestions.append({
                        'id': emp.employee_id,
                        'name': f"{emp.first_name} {emp.last_name}",
                        'avatar': emp.profile_image.url if emp.profile_image else None,
                        'job_title': "Available for work"
                    })
            
        elif employee_id:
            employee = get_object_or_404(Employee, employee_id=employee_id)
            user_info = {
                'type': 'employee',
                'name': f"{employee.first_name} {employee.last_name}",
                'id': employee.employee_id,
                'avatar': employee.profile_image.url if employee.profile_image else None
            }
            
            # Get recent employers from chat history
            recent_chats = ChatRoom.objects.filter(
                employee=employee
            ).select_related('employer').order_by('-last_message_time')[:10]
            
            for chat in recent_chats:
                suggestions.append({
                    'id': chat.employer.employer_id,
                    'name': f"{chat.employer.first_name} {chat.employer.last_name}",
                    'avatar': chat.employer.profile_image.url if chat.employer.profile_image else None,
                    'job_title': "Previous contact"
                })
            
            # If no recent chats, get all active employers
            if not suggestions:
                employers = Employer.objects.filter(is_active=True)[:10]
                for emp in employers:
                    suggestions.append({
                        'id': emp.employer_id,
                        'name': f"{emp.first_name} {emp.last_name}",
                        'avatar': emp.profile_image.url if emp.profile_image else None,
                        'job_title': "Looking for workers"
                    })
        
        else:
            messages.error(request, "Please login to start a chat")
            return redirect('index')
        
        # Handle form submission
        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            subject = request.POST.get('subject', 'New Chat')
            initial_message = request.POST.get('initial_message', 'Hello!')
            
            if not user_id:
                messages.error(request, "Please select a user to chat with")
                return redirect('start_chat')
            
            try:
                if employer_id:
                    # Start chat with employee
                    employer = get_object_or_404(Employer, employer_id=employer_id)
                    employee = get_object_or_404(Employee, employee_id=user_id)
                    
                    # Check if chat room already exists
                    existing_room = ChatRoom.objects.filter(
                        employer=employer,
                        employee=employee
                    ).first()
                    
                    if existing_room:
                        # Use existing room
                        chat_room = existing_room
                        chat_room.status = 'active'
                        chat_room.subject = subject if subject else chat_room.subject
                        chat_room.save()
                    else:
                        # Create new chat room
                        chat_room = ChatRoom.objects.create(
                            employer=employer,
                            employee=employee,
                            subject=subject,
                            room_type='general'
                        )
                    
                    # Create initial message
                    Message.objects.create(
                        room=chat_room,
                        sender_type='employer',
                        sender_employer=employer,
                        content=initial_message,
                        status='sent'
                    )
                    
                    # Update chat room stats
                    chat_room.message_count = chat_room.messages.count()
                    chat_room.unread_employee += 1
                    chat_room.last_message_time = timezone.now()
                    chat_room.save()
                    
                    messages.success(request, "Chat started successfully!")
                    return redirect('chat_room', room_id=chat_room.room_id)
                    
                elif employee_id:
                    # Start chat with employer
                    employee = get_object_or_404(Employee, employee_id=employee_id)
                    employer_obj = get_object_or_404(Employer, employer_id=user_id)
                    
                    # Check if chat room already exists
                    existing_room = ChatRoom.objects.filter(
                        employer=employer_obj,
                        employee=employee
                    ).first()
                    
                    if existing_room:
                        # Use existing room
                        chat_room = existing_room
                        chat_room.status = 'active'
                        chat_room.subject = subject if subject else chat_room.subject
                        chat_room.save()
                    else:
                        # Create new chat room
                        chat_room = ChatRoom.objects.create(
                            employer=employer_obj,
                            employee=employee,
                            subject=subject,
                            room_type='general'
                        )
                    
                    # Create initial message
                    Message.objects.create(
                        room=chat_room,
                        sender_type='employee',
                        sender_employee=employee,
                        content=initial_message,
                        status='sent'
                    )
                    
                    # Update chat room stats
                    chat_room.message_count = chat_room.messages.count()
                    chat_room.unread_employer += 1
                    chat_room.last_message_time = timezone.now()
                    chat_room.save()
                    
                    messages.success(request, "Chat started successfully!")
                    return redirect('chat_room', room_id=chat_room.room_id)
                    
            except Exception as e:
                messages.error(request, f"Error starting chat: {str(e)}")
                return redirect('start_chat')
        
        context = {
            'user_info': user_info,
            'suggestions': suggestions
        }
        
        return render(request, 'message_system/start_chat.html', context)
        
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('message_dashboard')


# Message actions
@check_user_session
def delete_message(request, message_id):
    """Delete a message (soft delete)"""
    try:
        message = get_object_or_404(Message, message_id=message_id)
        
        employer_id = request.session.get('employer_id')
        employee_id = request.session.get('employee_id')
        
        # Check if user owns the message
        if employer_id:
            employer = get_object_or_404(Employer, employer_id=employer_id)
            if message.sender_type == 'employer' and message.sender_employer == employer:
                message.is_deleted = True
                message.save()
                return JsonResponse({'success': True, 'message': 'Message deleted'})
                
        elif employee_id:
            employee = get_object_or_404(Employee, employee_id=employee_id)
            if message.sender_type == 'employee' and message.sender_employee == employee:
                message.is_deleted = True
                message.save()
                return JsonResponse({'success': True, 'message': 'Message deleted'})
        
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@check_user_session
def edit_message(request, message_id):
    """Edit a message"""
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            new_content = data.get('content')
            
            if not new_content:
                return JsonResponse({'success': False, 'error': 'Content required'})
            
            message = get_object_or_404(Message, message_id=message_id)
            
            employer_id = request.session.get('employer_id')
            employee_id = request.session.get('employee_id')
            
            # Check if user owns the message
            if employer_id:
                employer = get_object_or_404(Employer, employer_id=employer_id)
                if message.sender_type == 'employer' and message.sender_employer == employer:
                    message.content = new_content
                    message.is_edited = True
                    message.save()
                    return JsonResponse({'success': True, 'message': 'Message updated'})
                    
            elif employee_id:
                employee = get_object_or_404(Employee, employee_id=employee_id)
                if message.sender_type == 'employee' and message.sender_employee == employee:
                    message.content = new_content
                    message.is_edited = True
                    message.save()
                    return JsonResponse({'success': True, 'message': 'Message updated'})
            
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@check_user_session  
def mark_notifications_read(request):
    """Mark all notifications as read"""
    try:
        employer_id = request.session.get('employer_id')
        employee_id = request.session.get('employee_id')
        
        if employer_id:
            employer = get_object_or_404(Employer, employer_id=employer_id)
            ChatNotification.objects.filter(
                user_type='employer',
                user_employer=employer,
                is_read=False
            ).update(is_read=True)
            
        elif employee_id:
            employee = get_object_or_404(Employee, employee_id=employee_id)
            ChatNotification.objects.filter(
                user_type='employee',
                user_employee=employee,
                is_read=False
            ).update(is_read=True)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@check_user_session
def close_chat(request, room_id):
    """Close a chat room"""
    try:
        chat_room = get_object_or_404(ChatRoom, room_id=room_id)
        
        employer_id = request.session.get('employer_id')
        employee_id = request.session.get('employee_id')
        
        # Check if user has access
        if employer_id:
            employer = get_object_or_404(Employer, employer_id=employer_id)
            if chat_room.employer == employer:
                chat_room.status = 'closed'
                chat_room.save()
                messages.success(request, "Chat closed successfully")
                
        elif employee_id:
            employee = get_object_or_404(Employee, employee_id=employee_id)
            if chat_room.employee == employee:
                chat_room.status = 'closed'
                chat_room.save()
                messages.success(request, "Chat closed successfully")
        else:
            messages.error(request, "Permission denied")
        
        return redirect('message_dashboard')
        
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('message_dashboard')


@check_user_session
def clear_chat(request, room_id):
    """Clear all messages in a chat (soft delete)"""
    try:
        chat_room = get_object_or_404(ChatRoom, room_id=room_id)
        
        employer_id = request.session.get('employer_id')
        employee_id = request.session.get('employee_id')
        
        # Check if user has access
        if employer_id:
            employer = get_object_or_404(Employer, employer_id=employer_id)
            if chat_room.employer == employer:
                # Soft delete all messages
                chat_room.messages.update(is_deleted=True)
                messages.success(request, "Chat cleared successfully")
                
        elif employee_id:
            employee = get_object_or_404(Employee, employee_id=employee_id)
            if chat_room.employee == employee:
                # Soft delete all messages
                chat_room.messages.update(is_deleted=True)
                messages.success(request, "Chat cleared successfully")
        else:
            messages.error(request, "Permission denied")
        
        return redirect('chat_room', room_id=room_id)
        
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('chat_room', room_id=room_id)


# AJAX view for sending messages
@check_user_session
def send_message(request):
    """Handle sending messages via AJAX"""
    if request.method == 'POST':
        try:
            # Check session
            employer_id = request.session.get('employer_id')
            employee_id = request.session.get('employee_id')
            
            if not employer_id and not employee_id:
                return JsonResponse({'success': False, 'error': 'Please login'})
            
            data = json.loads(request.body)
            room_id = data.get('room_id')
            content = data.get('content')
            message_type = data.get('message_type', 'text')
            
            if not all([room_id, content]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            chat_room = get_object_or_404(ChatRoom, room_id=room_id)
            
            # Create message
            if employer_id:
                employer = get_object_or_404(Employer, employer_id=employer_id)
                # Check if employer has access to this chat room
                if chat_room.employer != employer:
                    return JsonResponse({'success': False, 'error': 'Access denied'})
                
                message = Message.objects.create(
                    room=chat_room,
                    sender_type='employer',
                    sender_employer=employer,
                    content=content,
                    message_type=message_type,
                    status='sent'
                )
                # Update unread count for employee
                chat_room.unread_employee += 1
                
            elif employee_id:
                employee = get_object_or_404(Employee, employee_id=employee_id)
                # Check if employee has access to this chat room
                if chat_room.employee != employee:
                    return JsonResponse({'success': False, 'error': 'Access denied'})
                
                message = Message.objects.create(
                    room=chat_room,
                    sender_type='employee',
                    sender_employee=employee,
                    content=content,
                    message_type=message_type,
                    status='sent'
                )
                # Update unread count for employer
                chat_room.unread_employer += 1
            else:
                return JsonResponse({'success': False, 'error': 'Invalid user type'})
            
            # Update chat room stats
            chat_room.message_count += 1
            chat_room.last_message_time = timezone.now()
            chat_room.save()
            
            return JsonResponse({
                'success': True,
                'message_id': message.message_id,
                'sender_type': message.sender_type,
                'sender_id': employer_id if employer_id else employee_id,
                'content': message.content,
                'timestamp': message.created_at.isoformat(),
                'formatted_time': message.formatted_time
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


# AJAX view for fetching new messages
@check_user_session
def get_new_messages(request, room_id):
    """Get new messages for a chat room"""
    try:
        # Check session
        employer_id = request.session.get('employer_id')
        employee_id = request.session.get('employee_id')
        
        if not employer_id and not employee_id:
            return JsonResponse({'success': False, 'error': 'Please login'})
        
        last_message_id = request.GET.get('last_message_id', 0)
        
        chat_room = get_object_or_404(ChatRoom, room_id=room_id)
        
        # Check access
        if employer_id:
            employer = get_object_or_404(Employer, employer_id=employer_id)
            if chat_room.employer != employer:
                return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
                
        elif employee_id:
            employee = get_object_or_404(Employee, employee_id=employee_id)
            if chat_room.employee != employee:
                return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
        
        # Get new messages
        new_messages = chat_room.messages.filter(
            message_id__gt=last_message_id,
            is_deleted=False
        ).order_by('created_at')
        
        messages_data = []
        for msg in new_messages:
            # Get sender name
            sender_name = ""
            if msg.sender_type == 'employer' and msg.sender_employer:
                sender_name = f"{msg.sender_employer.first_name} {msg.sender_employer.last_name}"
            elif msg.sender_type == 'employee' and msg.sender_employee:
                sender_name = f"{msg.sender_employee.first_name} {msg.sender_employee.last_name}"
            
            messages_data.append({
                'id': msg.message_id,
                'content': msg.content,
                'sender_type': msg.sender_type,
                'sender_id': msg.sender_employer.employer_id if msg.sender_type == 'employer' else msg.sender_employee.employee_id,
                'sender_name': sender_name,
                'timestamp': msg.created_at.isoformat(),
                'formatted_time': msg.formatted_time,
                'is_edited': msg.is_edited
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'has_new': len(messages_data) > 0
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)