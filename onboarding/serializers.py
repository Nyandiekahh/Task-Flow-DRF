# Create a new app for onboarding
# python manage.py startapp onboarding

# onboarding/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from organizations.models import Organization, TeamMember
from organizations.serializers import OrganizationSerializer, TeamMemberSerializer
from roles.models import Role
from roles.serializers import RoleSerializer

User = get_user_model()


class OnboardingDataSerializer(serializers.Serializer):
    """Serializer for complete onboarding data"""
    
    organization = OrganizationSerializer()
    team_members = TeamMemberSerializer(many=True)
    roles = RoleSerializer(many=True)
    completed = serializers.BooleanField()
    
    def to_representation(self, instance):
        """Return the onboarding data for a user"""
        user = instance
        
        # Get the organization data
        organization_data = {}
        if user.organization:
            organization_data = OrganizationSerializer(user.organization).data
        
        # Get team members
        team_members = []
        if user.organization:
            team_members = TeamMemberSerializer(
                user.organization.team_members.all(), 
                many=True
            ).data
        
        # Get roles
        roles = []
        if user.organization:
            roles = RoleSerializer(
                user.organization.roles.all(),
                many=True
            ).data
        
        return {
            'organization': organization_data,
            'team_members': team_members,
            'roles': roles,
            'completed': user.onboarding_completed
        }


class CompleteOnboardingSerializer(serializers.Serializer):
    """Serializer for marking onboarding as complete"""
    
    def update(self, instance, validated_data):
        """Mark the user's onboarding as complete"""
        user = instance
        user.onboarding_completed = True
        user.save()
        return user