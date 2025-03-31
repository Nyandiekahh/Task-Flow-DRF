# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import random
import string
import uuid


class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom User model that uses email instead of username."""

    # Remove username field (we'll use email instead)
    username = None
    
    # Add required fields
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(_('full name'), max_length=150, blank=True)
    
    # Organization relationship
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )
    
    # Keep organization_name for backward compatibility
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Add fields to track onboarding progress
    onboarding_completed = models.BooleanField(default=False)
    
    # Fields for title
    title = models.CharField(max_length=100, blank=True, null=True)
    
    # Use email as the unique identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Specify the manager for this model
    objects = CustomUserManager()

    def __str__(self):
        return self.email


class PasswordResetOTP(models.Model):
    """Model to store OTPs for password reset"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_otp_for_user(cls, user):
        """Create a new OTP for the user"""
        # Invalidate any existing OTPs
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Create new OTP
        otp = cls.generate_otp()
        otp_obj = cls.objects.create(user=user, otp=otp)
        return otp_obj
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        # OTP expires after 15 minutes
        expiry_time = timezone.timedelta(minutes=15)
        return (not self.is_used and 
                timezone.now() < self.created_at + expiry_time)


class Invitation(models.Model):
    """Model to store team member invitations"""
    # Unique token for the invitation
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Who is being invited
    email = models.EmailField()
    name = models.CharField(max_length=150, blank=True)
    
    # Who sent the invitation
    invited_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    
    # Organization and role for the invited user
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    role = models.ForeignKey(
        'roles.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitations'
    )
    
    # Status tracking
    accepted = models.BooleanField(default=False)
    date_sent = models.DateTimeField(auto_now_add=True)
    date_accepted = models.DateTimeField(null=True, blank=True)
    
    # Email sending status
    email_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.organization.name}"
    
    def accept(self, user=None):
        """Mark invitation as accepted and associate with user if provided"""
        self.accepted = True
        self.date_accepted = timezone.now()
        
        if user:
            user.organization = self.organization
            if self.role:
                # Assuming the role name is stored in user.title
                user.title = self.role.name
            user.save()
            
        self.save()
    
    class Meta:
        unique_together = ('email', 'organization')
        ordering = ['-date_sent']