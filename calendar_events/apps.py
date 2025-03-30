from django.apps import AppConfig


class CalendarEventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calendar_events'
    verbose_name = 'Calendar Events'
    
    def ready(self):
        try:
            # Import signals
            import calendar_events.signals
        except ImportError:
            pass  # Handle the case when signals module doesn't exist yet