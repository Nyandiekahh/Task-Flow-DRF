# reports/serializers.py
from rest_framework import serializers
from .models import ReportConfiguration
from django.utils import timezone

class ReportConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for report configurations"""
    
    class Meta:
        model = ReportConfiguration
        fields = [
            'id', 'name', 'report_type', 'organization', 'created_by',
            'configuration', 'is_favorite', 'last_generated',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Set created_by automatically to the current user"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

# Project Status Report
class ProjectStatusReportSerializer(serializers.Serializer):
    """Serializer for project status report parameters"""
    
    project_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validate date range if provided"""
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data

# Team Productivity Report
class TeamProductivityReportSerializer(serializers.Serializer):
    """Serializer for team productivity report parameters"""
    
    team_member_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    group_by = serializers.ChoiceField(
        choices=['day', 'week', 'month', 'project'],
        default='week',
        required=False
    )
    
    def validate(self, data):
        """Validate date range if provided"""
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data

# Task Completion Report
class TaskCompletionReportSerializer(serializers.Serializer):
    """Serializer for task completion report parameters"""
    
    project_id = serializers.IntegerField(required=False)
    team_member_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    group_by = serializers.ChoiceField(
        choices=['day', 'week', 'month', 'project', 'category', 'priority'],
        default='week',
        required=False
    )
    
    def validate(self, data):
        """Validate date range if provided"""
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data

# Time Tracking Report
class TimeTrackingReportSerializer(serializers.Serializer):
    """Serializer for time tracking report parameters"""
    
    project_id = serializers.IntegerField(required=False)
    team_member_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    billable_only = serializers.BooleanField(default=False, required=False)
    group_by = serializers.ChoiceField(
        choices=['day', 'week', 'month', 'project', 'team_member'],
        default='project',
        required=False
    )
    
    def validate(self, data):
        """Validate date range if provided"""
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data

# Overdue Tasks Report
class OverdueTasksReportSerializer(serializers.Serializer):
    """Serializer for overdue tasks report parameters"""
    
    project_id = serializers.IntegerField(required=False)
    team_member_id = serializers.IntegerField(required=False)
    days_overdue = serializers.IntegerField(required=False)
    group_by = serializers.ChoiceField(
        choices=['project', 'team_member', 'priority', 'category'],
        default='project',
        required=False
    )