from django.contrib import admin
from .models import Role, Permission

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'description']
    search_fields = ['name', 'code', 'description']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['organization']
    filter_horizontal = ['permissions']  # This creates a nice widget for managing many-to-many relationships