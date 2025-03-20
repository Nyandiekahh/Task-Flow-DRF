# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'title', 'organization_name', 'onboarding_completed')
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
        fields = ('email', 'password', 'confirm_password', 'name')
        extra_kwargs = {
            'name': {'required': True}
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
            password=validated_data['password']
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