from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, ConversationParticipant, MessageRead, Conversation
from django.utils import timezone

@receiver(post_save, sender=Message)
def handle_new_message(sender, instance, created, **kwargs):
    if created:
        # Auto-mark as read for the sender
        MessageRead.objects.create(
            message=instance,
            user=instance.sender
        )
        
        # Update conversation's updated_at timestamp
        conversation = instance.conversation
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        
        # Here you would trigger any necessary notifications
        # For example, sending a WebSocket event or creating a notification
        # This is where you'd integrate with your notification system
        pass