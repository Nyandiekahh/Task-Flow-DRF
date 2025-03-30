from rest_framework import serializers
from calendar_events.models import CalendarEvent, EventAttendee
from django.contrib.auth import get_user_model

# Create a simple user serializer since we don't have access to the original
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class EventAttendeeSerializer(serializers.ModelSerializer):
    user_details = SimpleUserSerializer(source='user', read_only=True)
    
    class Meta:
        model = EventAttendee
        fields = ['id', 'user', 'user_details', 'response', 'response_date']
        read_only_fields = ['response_date']


class CalendarEventSerializer(serializers.ModelSerializer):
    creator_details = SimpleUserSerializer(source='creator', read_only=True)
    attendees_details = serializers.SerializerMethodField()
    attendee_responses = EventAttendeeSerializer(many=True, read_only=True)
    
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'title', 'description', 'start_time', 'end_time', 
            'all_day', 'location', 'event_type', 'creator', 'creator_details',
            'attendees', 'attendees_details', 'attendee_responses',
            'related_task', 'related_project', 'is_recurring',
            'recurrence_pattern', 'recurrence_end_date',
            'notification_minutes_before', 'created_at', 'updated_at'
        ]
        read_only_fields = ['creator', 'created_at', 'updated_at']
    
    def get_attendees_details(self, obj):
        """Get detailed info about attendees"""
        return SimpleUserSerializer(obj.attendees.all(), many=True).data
    
    def create(self, validated_data):
        # Extract attendees from validated data
        attendees = validated_data.pop('attendees', [])
        
        # Set creator to current user
        validated_data['creator'] = self.context['request'].user
        
        # Create the event
        event = CalendarEvent.objects.create(**validated_data)
        
        # Add attendees to the event
        if attendees:
            event.attendees.set(attendees)
            
            # Create pending EventAttendee objects for each attendee
            for attendee in attendees:
                EventAttendee.objects.create(event=event, user=attendee)
        
        return event


class CalendarEventDetailSerializer(CalendarEventSerializer):
    """Detailed calendar event serializer with additional information"""
    
    class Meta(CalendarEventSerializer.Meta):
        fields = CalendarEventSerializer.Meta.fields + ['duration_minutes']


class EventAttendeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating attendee response"""
    
    class Meta:
        model = EventAttendee
        fields = ['response']
        read_only_fields = ['event', 'user', 'response_date']