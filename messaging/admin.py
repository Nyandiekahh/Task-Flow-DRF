from django.contrib import admin
from .models import (
    Conversation, ConversationParticipant, Message, 
    MessageRead, MessageReaction, MessageAttachment,
    MessageThread, PinnedMessage, SavedMessage, TypingIndicator
)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'organization', 'is_group_chat', 'created_at', 'updated_at')
    list_filter = ('is_group_chat', 'organization')
    search_fields = ('name',)

@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'user', 'joined_at', 'is_admin')
    list_filter = ('is_admin',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'content', 'timestamp', 'edited_at')
    list_filter = ('conversation', 'sender')
    search_fields = ('content',)
    date_hierarchy = 'timestamp'

@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'read_at')
    list_filter = ('user',)
    date_hierarchy = 'read_at'

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'reaction', 'created_at')
    list_filter = ('reaction', 'user')
    search_fields = ('reaction',)

@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'file_name', 'file_type', 'file_size', 'uploaded_at')
    list_filter = ('file_type',)
    search_fields = ('file_name',)

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent_message', 'reply_message')

@admin.register(PinnedMessage)
class PinnedMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'conversation', 'pinned_by', 'pinned_at')
    list_filter = ('conversation', 'pinned_by')
    date_hierarchy = 'pinned_at'

@admin.register(SavedMessage)
class SavedMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'saved_at')
    list_filter = ('user',)
    date_hierarchy = 'saved_at'
    
@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'user', 'timestamp')
    list_filter = ('conversation', 'user')
    date_hierarchy = 'timestamp'