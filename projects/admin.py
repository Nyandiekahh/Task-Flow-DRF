from django.contrib import admin
from .models import Project

class ProjectAdmin(admin.ModelAdmin):
    """Admin configuration for Project model"""
    list_display = (
        'name', 
        'organization', 
        'status', 
        'start_date', 
        'end_date', 
        'created_at', 
        'updated_at'
    )
    list_filter = (
        'status', 
        'organization', 
        'created_at', 
        'updated_at'
    )
    search_fields = (
        'name', 
        'description', 
        'organization__name'
    )
    readonly_fields = (
        'created_at', 
        'updated_at'
    )
    
    # Display team members in a horizontal filter for easy selection
    filter_horizontal = ('team_members',)
    
    # Customize the form to show more details
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Project Details', {
            'fields': (
                'status', 
                'start_date', 
                'end_date', 
                'organization'
            )
        }),
        ('Team Members', {
            'fields': ('team_members',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        """
        Optimize the queryset to reduce database queries
        """
        return super().get_queryset(request).select_related('organization')

# Register the model with the admin site
admin.site.register(Project, ProjectAdmin)