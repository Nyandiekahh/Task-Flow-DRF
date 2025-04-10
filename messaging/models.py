from django.db import models
from django.contrib.auth import get_user_model
from organizations.models import Organization
from django.utils import timezone
from tasks.models import Task

User = get_user_model()

class Conversation(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)  # Optional for group chats
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_group_chat = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name if self.name else f"Conversation {self.id}"

class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='participants'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='conversations'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)  # For group chat admins
    
    class Meta:
        unique_together = ['conversation', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.conversation}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class MessageRead(models.Model):
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='read_receipts'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='read_messages'
    )
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} read at {self.read_at}"

class MessageReaction(models.Model):
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='reactions'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='message_reactions'
    )
    reaction = models.CharField(max_length=50)  # Emoji or reaction code
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user', 'reaction']
    
    def __str__(self):
        return f"{self.user.username} reacted with {self.reaction}"

class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='attachments'
    )
    file = models.FileField(upload_to='message_attachments/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.IntegerField()  # Size in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment {self.file_name} for message {self.message.id}"

class MessageThread(models.Model):
    """For threaded replies to a specific message"""
    parent_message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='thread_parent'
    )
    reply_message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='thread_reply'
    )
    
    class Meta:
        unique_together = ['parent_message', 'reply_message']
    
    def __str__(self):
        return f"Reply to message {self.parent_message.id}"

class PinnedMessage(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='pins'
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='pinned_messages'
    )
    pinned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pinned_messages'
    )
    pinned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'conversation']
    
    def __str__(self):
        return f"Message {self.message.id} pinned in {self.conversation}"

class SavedMessage(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_messages'
    )
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"Message {self.message.id} saved by {self.user.username}"

class TypingIndicator(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='typing_indicators'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='typing_status'
    )
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['conversation', 'user']
    
    def __str__(self):
        return f"{self.user.username} typing in {self.conversation}"
    
class TaskReference(models.Model):
    """Link between messages and tasks for contextual references"""
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='task_references'
    )
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='message_references'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'task']
    
    def __str__(self):
        return f"Task {self.task.id} referenced in message {self.message.id}"