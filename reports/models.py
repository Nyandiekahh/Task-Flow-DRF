# reports/models.py
from django.db import models
from django.contrib.auth import get_user_model
from organizations.models import Organization, TeamMember

User = get_user_model()

class ReportConfiguration(models.Model):
    """Model to store saved report configurations"""
    
    REPORT_TYPE_CHOICES = [
        ('project_status', 'Project Status Report'),
        ('team_productivity', 'Team Productivity Report'),
        ('task_completion', 'Task Completion Report'),
        ('time_tracking', 'Time Tracking Report'),
        ('overdue_tasks', 'Overdue Tasks Report'),
    ]
    
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='report_configurations'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_reports'
    )
    # JSON configuration for report parameters (filters, groupings, etc.)
    configuration = models.JSONField(default=dict)
    is_favorite = models.BooleanField(default=False)
    
    # When was this report last generated
    last_generated = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ('name', 'organization')