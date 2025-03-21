# organizations/serializers.py

from rest_framework import serializers
from .models import Organization, TeamMember, Title


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for the Organization model"""
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'industry', 'size', 'logo', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create and return a new organization"""
        # Set the owner to the current user
        user = self.context['request'].user
        organization = Organization.objects.create(owner=user, **validated_data)
        
        # Set the user's organization
        user.organization = organization
        user.organization_name = organization.name  # Set the name as well for compatibility
        user.save()
        
        return organization


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for the TeamMember model"""
    
    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'email', 'title', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create and return a new team member"""
        # Set the organization to the current user's organization
        user = self.context['request'].user
        
        if not hasattr(user, 'organization') or not user.organization:
            raise serializers.ValidationError("You must create an organization before adding team members")
        
        team_member = TeamMember.objects.create(
            organization=user.organization,
            **validated_data
        )
        
        return team_member
    
# organizations/serializers.py
class TitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']