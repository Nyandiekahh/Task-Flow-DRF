from django.contrib import admin
from calendar_events.models import CalendarEvent, EventAttendee

class EventAttendeeInline(admin.TabularInline):
    model = EventAttendee
    extra = 0

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'event_type', 'creator', 'is_recurring')
    list_filter = ('event_type', 'is_recurring', 'all_day')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_time'
    inlines = [EventAttendeeInline]
    filter_horizontal = ('attendees',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'event_type')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'all_day')
        }),
        ('Location', {
            'fields': ('location',)
        }),
        ('People', {
            'fields': ('creator', 'attendees')
        }),
        ('Related Items', {
            'fields': ('related_task', 'related_project')
        }),
        ('Recurrence', {
            'fields': ('is_recurring', 'recurrence_pattern', 'recurrence_end_date')
        }),
        ('Notifications', {
            'fields': ('notification_minutes_before',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.creator = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'response', 'response_date')
    list_filter = ('response',)
    search_fields = ('event__title', 'user__username', 'user__email')