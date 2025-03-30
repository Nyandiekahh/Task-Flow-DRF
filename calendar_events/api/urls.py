from django.urls import path, include
from rest_framework.routers import DefaultRouter
from calendar_events.api.views import CalendarEventViewSet, EventAttendeeViewSet

router = DefaultRouter()
router.register(r'events', CalendarEventViewSet, basename='calendar-events')
router.register(r'attendees', EventAttendeeViewSet, basename='event-attendees')

urlpatterns = [
    path('', include(router.urls)),
    # Add custom actions for date range filtering
    path('events/by_date_range/', CalendarEventViewSet.as_view({'get': 'by_date_range'})),
]