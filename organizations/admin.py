from django.contrib import admin
from .models import Organization, TeamMember, Title

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'size', 'owner', 'created_at']
    search_fields = ['name']
    list_filter = ['industry', 'size']

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'title', 'organization', 'created_at']
    search_fields = ['name', 'email']
    list_filter = ['title', 'organization']

@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'description']
    search_fields = ['name', 'description']
    list_filter = ['organization']