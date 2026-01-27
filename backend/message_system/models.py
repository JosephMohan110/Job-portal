# message_system/models.py

from django.db import models
from django.utils import timezone

class ChatRoom(models.Model):
    """Model for chat rooms between employers and employees"""
    TYPE_CHOICES = [
        ('job', 'Job-Related'),
        ('general', 'General Inquiry'),
        ('support', 'Customer Support'),
        ('followup', 'Follow-up'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    room_id = models.AutoField(primary_key=True)
    employer = models.ForeignKey('employer.Employer', on_delete=models.CASCADE, related_name='chat_rooms')
    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE, related_name='chat_rooms')
    
    # Job reference (optional - for job-related chats)
    job = models.ForeignKey('employee.JobRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    
    # Chat metadata
    room_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='job')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    subject = models.CharField(max_length=200, null=True, blank=True)
    
    # Tracking
    last_message_time = models.DateTimeField(auto_now=True)
    message_count = models.IntegerField(default=0)
    unread_employee = models.IntegerField(default=0)
    unread_employer = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_room_table'
        unique_together = ['employer', 'employee', 'job']
        ordering = ['-last_message_time']
    
    def __str__(self):
        if self.job:
            return f"Chat #{self.room_id}: {self.employer.full_name} ↔ {self.employee.full_name} (Job #{self.job.job_id})"
        return f"Chat #{self.room_id}: {self.employer.full_name} ↔ {self.employee.full_name}"
    
    @property
    def participants(self):
        return {
            'employer': {
                'id': self.employer.employer_id,
                'name': self.employer.full_name,
                'type': 'employer'
            },
            'employee': {
                'id': self.employee.employee_id,
                'name': self.employee.full_name,
                'type': 'employee'
            }
        }
    
    @property
    def last_activity(self):
        """Human-readable last activity time"""
        from django.utils.timesince import timesince
        return f"{timesince(self.last_message_time)} ago"
    
    def mark_as_read(self, user_type):
        """Mark messages as read for a specific user type"""
        if user_type == 'employer':
            self.unread_employer = 0
        elif user_type == 'employee':
            self.unread_employee = 0
        self.save()


class Message(models.Model):
    """Model for individual messages"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('location', 'Location'),
        ('job_update', 'Job Update'),
        ('payment', 'Payment'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    message_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    
    # Sender info
    sender_type = models.CharField(max_length=10, choices=[('employer', 'Employer'), ('employee', 'Employee')])
    sender_employer = models.ForeignKey('employer.Employer', on_delete=models.SET_NULL, null=True, blank=True)
    sender_employee = models.ForeignKey('employee.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='chat_thumbnails/', null=True, blank=True)
    
    # Message status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Read receipts
    read_by_employer = models.BooleanField(default=False)
    read_by_employee = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'message_table'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message #{self.message_id} in Room #{self.room.room_id}"
    
    @property
    def sender_name(self):
        if self.sender_type == 'employer' and self.sender_employer:
            return self.sender_employer.full_name
        elif self.sender_type == 'employee' and self.sender_employee:
            return self.sender_employee.full_name
        return 'Unknown'
    
    @property
    def sender_avatar(self):
        """Get sender's profile image or initials"""
        if self.sender_type == 'employer' and self.sender_employer:
            if self.sender_employer.profile_image:
                return self.sender_employer.profile_image.url
            return None
        elif self.sender_type == 'employee' and self.sender_employee:
            if self.sender_employee.profile_image:
                return self.sender_employee.profile_image.url
            return None
        return None
    
    @property
    def formatted_time(self):
        """Format message time for display"""
        from django.utils.timezone import localtime
        msg_time = localtime(self.created_at)
        
        if msg_time.date() == timezone.now().date():
            return msg_time.strftime("%I:%M %p")
        elif msg_time.date() == timezone.now().date() - timezone.timedelta(days=1):
            return f"Yesterday {msg_time.strftime('%I:%M %p')}"
        else:
            return msg_time.strftime("%b %d, %I:%M %p")
    
    def mark_as_read(self, user_type):
        """Mark message as read by a specific user"""
        if user_type == 'employer':
            self.read_by_employer = True
        elif user_type == 'employee':
            self.read_by_employee = True
        
        if self.read_by_employer and self.read_by_employee:
            self.read_at = timezone.now()
            self.status = 'read'
        
        self.save()


class ChatNotification(models.Model):
    """Model for chat notifications"""
    NOTIFICATION_TYPES = [
        ('new_message', 'New Message'),
        ('job_update', 'Job Update'),
        ('payment', 'Payment'),
        ('system', 'System'),
    ]
    
    id = models.AutoField(primary_key=True)
    user_type = models.CharField(max_length=10, choices=[('employer', 'Employer'), ('employee', 'Employee')])
    user_employer = models.ForeignKey('employer.Employer', on_delete=models.CASCADE, null=True, blank=True)
    user_employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE, null=True, blank=True)
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='new_message')
    title = models.CharField(max_length=200)
    message_preview = models.TextField()
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_notification_table'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user_type}: {self.title}"