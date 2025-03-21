# Create a new app for organizations
# python manage.py startapp organizations

# organizations/models.py
from django.db import models
from django.conf import settings


class Organization(models.Model):
    """Model for storing organization information"""
    
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100)
    size = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='organization_logos/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Owner of the organization (admin user)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='owned_organizations'
    )
    
    def __str__(self):
        return self.name


class TeamMember(models.Model):
    """Model for storing team member information"""
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='team_members'
    )
    
    name = models.CharField(max_length=255)
    email = models.EmailField()
    title = models.CharField(max_length=100)
    
    # Associated user account (if they've signed up)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_memberships'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    class Meta:
        unique_together = ('organization', 'email')

# organizations/models.py
class Title(models.Model):
    """Model for storing team titles/positions"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='titles'
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('organization', 'name')