from django.db import models
from django.conf import settings
from django.utils import timezone

class CalendarEvent(models.Model):
    """Model for calendar events"""
    EVENT_TYPE_CHOICES = (
        ('task', 'Task'),
        ('meeting', 'Meeting'),
        ('deadline', 'Deadline'),
        ('reminder', 'Reminder'),
        ('other', 'Other'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Type of event
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='other')
    
    # Relationships
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_events'
    )
    attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='calendar_events',
        blank=True
    )
    
    # Optional connections to other entities
    related_task = models.ForeignKey(
        'tasks.Task', 
        on_delete=models.SET_NULL, 
        related_name='calendar_events',
        blank=True, 
        null=True
    )
    related_project = models.ForeignKey(
        'projects.Project', 
        on_delete=models.SET_NULL, 
        related_name='calendar_events',
        blank=True, 
        null=True
    )
    
    # Recurrence fields
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=100, blank=True, null=True)
    recurrence_end_date = models.DateField(blank=True, null=True)
    
    # Notification
    notification_minutes_before = models.IntegerField(default=15)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
        
    def __str__(self):
        return self.title
    
    @property
    def duration_minutes(self):
        """Calculate duration in minutes"""
        if self.all_day:
            return 24 * 60
        
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60


class EventAttendee(models.Model):
    """Model to track attendee responses to events"""
    RESPONSE_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('tentative', 'Tentative'),
    )
    
    event = models.ForeignKey(
        CalendarEvent, 
        on_delete=models.CASCADE, 
        related_name='attendee_responses'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='event_responses'
    )
    response = models.CharField(
        max_length=10, 
        choices=RESPONSE_CHOICES, 
        default='pending'
    )
    response_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['event', 'user']
        
    def __str__(self):
        return f"{self.user.username} - {self.event.title}: {self.response}"