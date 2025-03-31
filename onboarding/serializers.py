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


class OrganizationSetupSerializer(serializers.Serializer):
    """Serializer for setting up a new organization"""
    name = serializers.CharField(max_length=255, required=True)
    industry = serializers.CharField(max_length=100, required=False, allow_blank=True)
    size = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_name(self, value):
        """Validate that organization name is unique"""
        if Organization.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                "An organization with this name already exists."
            )
        return value
    
    def create(self, validated_data):
        """Create a new organization"""
        user = self.context['request'].user
        
        # Create the organization
        organization = Organization.objects.create(
            name=validated_data.get('name'),
            industry=validated_data.get('industry', ''),
            size=validated_data.get('size', ''),
            owner=user
        )
        
        # Associate user with the organization
        user.organization = organization
        user.save()
        
        return organization