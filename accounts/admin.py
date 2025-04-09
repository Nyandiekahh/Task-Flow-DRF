# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Invitation, InvitationOTP, PasswordResetOTP


class CustomUserAdmin(UserAdmin):
    """Admin configuration for the custom user model"""
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name',)}),
        (_('Organization info'), {'fields': ('organization_name', 'title', 'onboarding_completed')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name'),
        }),
    )
    list_display = ('email', 'name', 'organization_name', 'is_staff')
    search_fields = ('email', 'name', 'organization_name')
    ordering = ('email',)


class InvitationAdmin(admin.ModelAdmin):
    """Admin configuration for Invitation model"""
    list_display = (
        'email', 
        'name', 
        'invited_by', 
        'organization', 
        'role', 
        'accepted', 
        'date_sent', 
        'date_accepted'
    )
    list_filter = ('accepted', 'date_sent')
    search_fields = ('email', 'name', 'invited_by__email', 'invited_by__name')
    readonly_fields = ('token', 'date_sent', 'date_accepted')


class InvitationOTPAdmin(admin.ModelAdmin):
    """Admin configuration for InvitationOTP model"""
    list_display = (
        'invitation', 
        'code', 
        'created_at', 
        'expires_at', 
        'is_verified'
    )
    list_filter = ('is_verified', 'created_at', 'expires_at')
    search_fields = ('invitation__email', 'code')
    readonly_fields = ('created_at', 'expires_at')


class PasswordResetOTPAdmin(admin.ModelAdmin):
    """Admin configuration for PasswordResetOTP model"""
    list_display = (
        'user', 
        'otp', 
        'created_at', 
        'is_used'
    )
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'otp')
    readonly_fields = ('created_at',)


# Register models with the admin site
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(InvitationOTP, InvitationOTPAdmin)
admin.site.register(PasswordResetOTP, PasswordResetOTPAdmin)