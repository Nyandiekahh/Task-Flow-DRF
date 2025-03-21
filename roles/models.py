# Create a new app for roles
# python manage.py startapp roles

# roles/models.py
from django.db import models


class Permission(models.Model):
    """Model for system permissions"""
    
    PERMISSION_CHOICES = [
        ('create_tasks', 'Create Tasks'),
        ('view_tasks', 'View Tasks'),
        ('assign_tasks', 'Assign Tasks'),
        ('update_tasks', 'Update Tasks'),
        ('delete_tasks', 'Delete Tasks'),
        ('approve_tasks', 'Approve Tasks'),
        ('reject_tasks', 'Reject Tasks'),
        ('comment', 'Comment'),
        ('view_reports', 'View Reports'),
        ('manage_users', 'Manage Users'),
        ('manage_roles', 'Manage Roles'),
    ]
    
    code = models.CharField(max_length=100, choices=PERMISSION_CHOICES, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class Role(models.Model):
    """Model for user roles with associated permissions"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Organization the role belongs to
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='roles'
    )
    
    # Permissions associated with this role
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    class Meta:
        unique_together = ('name', 'organization')