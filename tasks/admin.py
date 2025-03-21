from django.contrib import admin
from .models import Task, Comment, TaskAttachment, TaskHistory


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'organization', 'created_by', 'assigned_to', 'created_at', 'due_date')
    list_filter = ('status', 'priority', 'organization')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    list_filter = ('task__status', 'author')
    search_fields = ('text',)
    date_hierarchy = 'created_at'


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'task', 'uploaded_by', 'uploaded_at')
    list_filter = ('task__status', 'uploaded_by')
    search_fields = ('filename',)
    date_hierarchy = 'uploaded_at'


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('task', 'action', 'actor', 'timestamp')
    list_filter = ('action', 'actor')
    search_fields = ('description',)
    date_hierarchy = 'timestamp'