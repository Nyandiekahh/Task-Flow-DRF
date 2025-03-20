# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


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


admin.site.register(CustomUser, CustomUserAdmin)