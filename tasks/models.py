from django.db import models
from django.conf import settings
from organizations.models import Organization, TeamMember


class Task(models.Model):
    """Model for storing task information"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic task information
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Organizational context
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    
    # Task creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    
    # Task assignment
    assigned_to = models.ForeignKey(
        TeamMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_tasks'
    )
    
    # Rejection
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_tasks'
    )
    rejection_reason = models.TextField(blank=True)
    
    # Delegation
    delegated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_tasks'
    )
    delegation_notes = models.TextField(blank=True)
    delegation_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title


class TaskAttachment(models.Model):
    """Model for storing task attachments"""
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='task_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.filename


class Comment(models.Model):
    """Model for storing task comments"""
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author} on {self.task}"


class TaskHistory(models.Model):
    """Model for tracking task changes/activity"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('assigned', 'Assigned'),
        ('delegated', 'Delegated'),
        ('status_changed', 'Status Changed'),
        ('commented', 'Commented'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action} by {self.actor} on {self.task}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Task Histories"