# projects/models.py
from django.db import models
from organizations.models import Organization, TeamMember

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('planning', 'Planning'),
            ('in_progress', 'In Progress'),
            ('on_hold', 'On Hold'),
            ('completed', 'Completed')
        ],
        default='planning'
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    team_members = models.ManyToManyField(TeamMember, related_name='projects', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name