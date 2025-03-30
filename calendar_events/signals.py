from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver
from django.utils import timezone
from calendar_events.models import CalendarEvent, EventAttendee

@receiver(post_save, sender=CalendarEvent)
def create_event_attendees(sender, instance, created, **kwargs):
    """
    When a new event is created:
    1. Add the creator to the attendees list
    2. Create an attendee response for the creator
    """
    if created:
        # Add the creator to the attendees list
        instance.attendees.add(instance.creator)
        
        # Create an attendee response for the creator
        EventAttendee.objects.get_or_create(
            event=instance, 
            user=instance.creator,
            defaults={'response': 'accepted'}
        )


@receiver(m2m_changed, sender=CalendarEvent.attendees.through)
def handle_attendees_change(sender, instance, action, pk_set, **kwargs):
    """
    When attendees are added to an event, create EventAttendee objects
    """
    if action == 'post_add' and pk_set:
        # Create attendee responses for new attendees
        for user_id in pk_set:
            # Set default response to 'accepted' for the creator, 'pending' for others
            default_response = 'accepted' if user_id == instance.creator_id else 'pending'
            
            EventAttendee.objects.get_or_create(
                event=instance,
                user_id=user_id,
                defaults={'response': default_response}
            )
    
    # Remove attendee responses for removed attendees
    elif action == 'post_remove' and pk_set:
        EventAttendee.objects.filter(
            event=instance,
            user_id__in=pk_set
        ).delete()