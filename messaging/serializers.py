# serializers.py

from rest_framework import serializers
from .models import (
    Conversation, ConversationParticipant, Message, 
    MessageRead, MessageReaction, MessageAttachment,
    MessageThread, PinnedMessage, SavedMessage
)
from django.contrib.auth import get_user_model
from organizations.models import Organization, TeamMember
from organizations.serializers import TeamMemberSerializer
from tasks.models import Task

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = '__all__'

class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = '__all__'

class MessageReadSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = MessageRead
        fields = ['id', 'user', 'read_at']

class MessageThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageThread
        fields = '__all__'

# class TaskMinimalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Task
#         fields = ['id', 'title', 'status', 'due_date']

# class TaskReferenceSerializer(serializers.ModelSerializer):
#     task = TaskMinimalSerializer()
    
#     class Meta:
#         model = TaskReference
#         fields = ['id', 'task', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserMinimalSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    read_by = serializers.SerializerMethodField()
    is_thread_reply = serializers.SerializerMethodField()
    # task_references = TaskReferenceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'content', 'timestamp', 
            'edited_at', 'attachments', 'reactions', 'read_by',
            'is_thread_reply'
        ]
    
    def get_read_by(self, obj):
        reads = MessageRead.objects.filter(message=obj)
        return MessageReadSerializer(reads, many=True).data
    
    def get_is_thread_reply(self, obj):
        return MessageThread.objects.filter(reply_message=obj).exists()
    
    def get_formatted_content(self, obj):
        """Return content formatted according to format_type"""
        if obj.format_type == 'markdown':
            # You would need to install a markdown library for this
            import markdown
            return markdown.markdown(obj.content)
        elif obj.format_type == 'html':
            # You might want to sanitize HTML here
            return obj.content
        else:  # plain text
            return obj.content

class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = ['id', 'user', 'joined_at', 'is_admin']

class ConversationSerializer(serializers.ModelSerializer):
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'name', 'organization', 'created_at', 'updated_at', 
            'is_group_chat', 'participants', 'last_message', 'unread_count'
        ]
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return 0
        
        # Count messages that don't have a read receipt from this user
        messages = obj.messages.all()
        read_message_ids = MessageRead.objects.filter(
            user=user, 
            message__in=messages
        ).values_list('message_id', flat=True)
        
        return messages.exclude(id__in=read_message_ids).count()

class PinnedMessageSerializer(serializers.ModelSerializer):
    message = MessageSerializer(read_only=True)
    pinned_by = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = PinnedMessage
        fields = ['id', 'message', 'conversation', 'pinned_by', 'pinned_at']

class SavedMessageSerializer(serializers.ModelSerializer):
    message = MessageSerializer(read_only=True)
    
    class Meta:
        model = SavedMessage
        fields = ['id', 'message', 'user', 'saved_at']

class ThreadMessageSerializer(serializers.ModelSerializer):
    """Serializer for threaded replies"""
    replies = serializers.SerializerMethodField()
    sender = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'content', 
            'timestamp', 'edited_at', 'replies'
        ]
    
    def get_replies(self, obj):
        thread_replies = MessageThread.objects.filter(parent_message=obj)
        reply_messages = [thread.reply_message for thread in thread_replies]
        return MessageSerializer(reply_messages, many=True).data

class OrganizationUserSerializer(serializers.ModelSerializer):
    """Serializer to get all users in an organization"""
    class Meta:
        model = TeamMember
        fields = ['id', 'user', 'organization', 'role', 'title', 'created_at']
        depth = 1  # Include user details