# projects/serializers.py
from rest_framework import serializers
from .models import Project
from django.db.models import Count, Q

class ProjectSerializer(serializers.ModelSerializer):
    """Base Project serializer"""
    class Meta:
        model = Project
        fields = '__all__'

class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for project list view with additional calculated fields"""
    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    organization_name = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'start_date', 'end_date', 'status',
            'organization', 'organization_name', 'created_at', 'updated_at',
            'tasks_count', 'completed_tasks_count', 'progress'
        ]
    
    def get_organization_name(self, obj):
        return obj.organization.name if obj.organization else None
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()
    
    def get_completed_tasks_count(self, obj):
        return obj.tasks.filter(
            Q(status='completed') | Q(status='approved')
        ).count()
    
    def get_progress(self, obj):
        total = obj.tasks.count()
        if total == 0:
            return 0
        
        completed = obj.tasks.filter(
            Q(status='completed') | Q(status='approved')
        ).count()
        
        return round((completed / total) * 100)

class ProjectDetailSerializer(ProjectListSerializer):
    """Serializer for project detail view with additional fields"""
    team_members_info = serializers.SerializerMethodField()
    
    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + ['team_members', 'team_members_info']
    
    def get_team_members_info(self, obj):
        team_members = obj.team_members.all()
        return [
            {
                'id': member.id,
                'name': member.name,
                'email': member.user.email if member.user else None,
                'title': member.title
            }
            for member in team_members
        ]