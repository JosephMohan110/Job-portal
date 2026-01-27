from .models import Employer, EmployerNotification

def employer_notifications(request):
    """Context processor to make employer notifications available in all templates"""
    if 'employer_id' in request.session:
        try:
            employer = Employer.objects.get(employer_id=request.session['employer_id'])
            # Get unread notifications
            notifications = EmployerNotification.objects.filter(
                employer=employer,
                is_read=False
            ).order_by('-created_at')[:10]  # Limit to 10 most recent unread
            
            unread_count = notifications.count()
            
            return {
                'employer_notifications': notifications,
                'employer_unread_notifications_count': unread_count
            }
        except Employer.DoesNotExist:
            return {}
            
    return {}
