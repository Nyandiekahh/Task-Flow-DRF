# roles/serializers.py

from rest_framework import serializers
from .models import Role, Permission


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for the Permission model"""
    
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'description']
        read_only_fields = ['id', 'code', 'name', 'description']  # Permissions are pre-defined


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model"""
    
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions'
    )
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permission_ids', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create and return a new role"""
        # Set the organization to the current user's organization
        user = self.context['request'].user
        
        if not user.organization:
            raise serializers.ValidationError("You must create an organization before adding roles")
        
        permissions = validated_data.pop('permissions')
        role = Role.objects.create(
            organization=user.organization,
            **validated_data
        )
        
        # Add permissions to the role
        role.permissions.set(permissions)
        
        return role