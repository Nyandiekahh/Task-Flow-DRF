from rest_framework import serializers
from .models import Organization, TeamMember, Title
from roles.models import Permission

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


class TitleSerializer(serializers.ModelSerializer):
    """Serializer for Title model with permissions"""
    # Add permissions field for creating/updating
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), 
        many=True, 
        required=False
    )
    
    # Add a method to get permission details
    permission_details = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = ['id', 'name', 'description', 'permissions', 'permission_details']
        read_only_fields = ['id']

    def get_permission_details(self, obj):
        """Get full details of permissions"""
        return [
            {
                'id': perm.id,
                'code': perm.code,
                'name': perm.name,
                'description': perm.description
            }
            for perm in obj.permissions.all()
        ]

    def create(self, validated_data):
        # Extract permissions
        permissions = validated_data.pop('permissions', [])
        
        # Create title
        title = Title.objects.create(**validated_data)
        
        # Add permissions if provided
        if permissions:
            title.permissions.set(permissions)
        
        return title

    def update(self, instance, validated_data):
        # Extract permissions
        permissions = validated_data.pop('permissions', None)
        
        # Update title details
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update permissions if provided
        if permissions is not None:
            instance.permissions.set(permissions)
        
        return instance


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for the TeamMember model"""
    title_name = serializers.CharField(source='title.name', read_only=True, allow_null=True)
    title_id = serializers.PrimaryKeyRelatedField(
        source='title', 
        queryset=Title.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    # Add title permissions
    title_permissions = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = [
            'id', 'name', 'email', 
            'title_id', 'title_name', 
            'title_permissions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_title_permissions(self, obj):
        """Get permissions for the team member's title"""
        if obj.title:
            return [
                {
                    'id': perm.id,
                    'code': perm.code,
                    'name': perm.name,
                    'description': perm.description
                }
                for perm in obj.title.permissions.all()
            ]
        return []
    
    def create(self, validated_data):
        """Create and return a new team member"""
        # Set the organization to the current user's organization
        user = self.context['request'].user
        
        if not hasattr(user, 'organization') or not user.organization:
            raise serializers.ValidationError("You must create an organization before adding team members")
        
        # Extract title if provided
        title = validated_data.pop('title', None)
        
        team_member = TeamMember.objects.create(
            organization=user.organization,
            title=title,
            **validated_data
        )
        
        return team_member