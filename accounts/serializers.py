# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import Invitation

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'title', 'organization', 'organization_name', 'onboarding_completed')
        read_only_fields = ('id',)


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for creating a user account"""
    
    # Add password confirmation field
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    # Add email validator to ensure uniqueness
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password', 'name', 'organization_name')
        extra_kwargs = {
            'name': {'required': True},
            'organization_name': {'required': False}
        }

    def validate(self, attrs):
        """Check that passwords match"""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        """Create and return a new user"""
        # Remove confirm_password from the data as it's not needed for creation
        validated_data.pop('confirm_password')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            organization_name=validated_data.get('organization_name', '')
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset"""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset"""
    token = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        """Check that passwords match"""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})
        return attrs


# Using a string for the queryset to avoid immediate evaluation
class InvitationCreateSerializer(serializers.Serializer):
    """Serializer for creating team member invitations"""
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    # Set read_only=True by default to avoid the queryset assertion error
    role = serializers.PrimaryKeyRelatedField(
        read_only=True,
        required=False,
        allow_null=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import Role model here to avoid circular imports
        try:
            from roles.models import Role
            
            # Replace the read-only field with a writable one if we have context
            if 'context' in kwargs and 'organization' in kwargs['context']:
                organization = kwargs['context']['organization']
                self.fields['role'] = serializers.PrimaryKeyRelatedField(
                    queryset=Role.objects.filter(organization=organization),
                    required=False,
                    allow_null=True
                )
        except ImportError:
            # Keep the field as read-only if the Role model can't be imported
            pass
    
    def validate_email(self, value):
        """Validate email isn't already in use by an existing user in the same organization"""
        organization = self.context.get('organization')
        if not organization:
            return value
            
        # Check if user with this email already exists in the organization
        if User.objects.filter(email=value, organization=organization).exists():
            raise serializers.ValidationError(
                "A user with this email already exists in your organization."
            )
        
        # Check if there's an existing invitation for this email
        existing_invite = Invitation.objects.filter(
            email=value, 
            organization=organization,
            accepted=False
        ).first()
        
        if existing_invite:
            # Update the existing invitation instead of creating a new one
            self.context['existing_invitation'] = existing_invite
            
        return value


class InvitationListSerializer(serializers.ModelSerializer):
    """Serializer for listing invitations"""
    invited_by_name = serializers.CharField(source='invited_by.name', read_only=True)
    invited_by_email = serializers.CharField(source='invited_by.email', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Invitation
        fields = ('id', 'token', 'email', 'name', 'invited_by_name', 'invited_by_email',
                  'organization_name', 'role_name', 'accepted', 'date_sent', 
                  'date_accepted', 'email_sent')
        read_only_fields = fields


class BulkInvitationSerializer(serializers.Serializer):
    """Serializer for handling bulk invitations"""
    invitations = InvitationCreateSerializer(many=True)