from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone

from calendar_events.models import CalendarEvent, EventAttendee
from calendar_events.api.serializers import (
    CalendarEventSerializer,
    CalendarEventDetailSerializer,
    EventAttendeeSerializer,
    EventAttendeeUpdateSerializer
)


class CalendarEventViewSet(viewsets.ModelViewSet):
    """ViewSet for calendar events"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_time', 'end_time', 'created_at', 'title']
    ordering = ['start_time']
    
    def get_queryset(self):
        """
        Filter events to those created by the user or where the user is an attendee
        """
        user = self.request.user
        return CalendarEvent.objects.filter(
            Q(creator=user) | Q(attendees=user)
        ).distinct()
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action
        """
        if self.action == 'retrieve':
            return CalendarEventDetailSerializer
        return CalendarEventSerializer
    
    def perform_create(self, serializer):
        """Set the creator to the current user"""
        serializer.save(creator=self.request.user)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Return upcoming events within the next 7 days"""
        now = timezone.now()
        next_week = now + timedelta(days=7)
        
        events = self.get_queryset().filter(
            start_time__gte=now,
            start_time__lte=next_week
        )
        
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Get events within a specific date range"""
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if not start_date or not end_date:
            return Response(
                {"error": "Both start and end dates are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        events = self.get_queryset().filter(
            # Include events that start or end within the range,
            # or span the entire range
            Q(start_time__gte=start_date, start_time__lte=end_date) |
            Q(end_time__gte=start_date, end_time__lte=end_date) |
            Q(start_time__lte=start_date, end_time__gte=end_date)
        )
        
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to an event invitation"""
        event = self.get_object()
        user = request.user
        
        # Check if user is an attendee
        if user not in event.attendees.all():
            return Response(
                {"error": "You are not an attendee of this event"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create attendee response
        attendee_response, created = EventAttendee.objects.get_or_create(
            event=event,
            user=user
        )
        
        # Update response
        serializer = EventAttendeeUpdateSerializer(
            attendee_response, 
            data=request.data
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventAttendeeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for event attendee responses"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EventAttendeeSerializer
    
    def get_queryset(self):
        """
        Filter attendee responses to those for events created by the user
        or where the user is an attendee
        """
        user = self.request.user
        return EventAttendee.objects.filter(
            Q(event__creator=user) | Q(user=user)
        ).distinct()
    
    @action(detail=True, methods=['patch'])
    def update_response(self, request, pk=None):
        """Update attendee response"""
        attendee_response = self.get_object()
        user = request.user
        
        # Only allow the attendee to update their own response
        if attendee_response.user != user:
            return Response(
                {"error": "You can only update your own response"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EventAttendeeUpdateSerializer(
            attendee_response, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)