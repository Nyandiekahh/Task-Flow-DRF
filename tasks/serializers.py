from rest_framework import serializers
from .models import Task, TaskAttachment, Comment, TaskHistory
from organizations.models import TeamMember


class TaskAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for task attachments"""
    
    class Meta:
        model = TaskAttachment
        fields = ['id', 'file', 'filename', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for task comments"""
    
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'author_name', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username


class TaskHistorySerializer(serializers.ModelSerializer):
    """Serializer for task history"""
    
    actor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskHistory
        fields = ['id', 'action', 'actor', 'actor_name', 'description', 'timestamp']
        read_only_fields = ['action', 'actor', 'description', 'timestamp']
    
    def get_actor_name(self, obj):
        return obj.actor.get_full_name() or obj.actor.username


class TaskListSerializer(serializers.ModelSerializer):
    """Simplified serializer for task listings"""
    
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'due_date',
            'assigned_to', 'assigned_to_name', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.name
        return None
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for task details"""
    
    comments = CommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    history = TaskHistorySerializer(many=True, read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    rejected_by_name = serializers.SerializerMethodField()
    delegated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'due_date',
            'organization', 'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_name',
            'created_at', 'updated_at', 'completed_at',
            'approved_by', 'approved_by_name',
            'rejected_by', 'rejected_by_name', 'rejection_reason',
            'delegated_by', 'delegated_by_name', 'delegation_notes', 'delegation_date',
            'comments', 'attachments', 'history'
        ]
        read_only_fields = [
            'organization', 'created_by', 'created_at', 'updated_at',
            'completed_at', 'approved_by', 'rejected_by', 'delegated_by', 'delegation_date',
            'comments', 'attachments', 'history'
        ]
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.name
        return None
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.username
        return None
    
    def get_rejected_by_name(self, obj):
        if obj.rejected_by:
            return obj.rejected_by.get_full_name() or obj.rejected_by.username
        return None
        
    def get_delegated_by_name(self, obj):
        if obj.delegated_by:
            return obj.delegated_by.get_full_name() or obj.delegated_by.username
        return None
    
    def validate_assigned_to(self, value):
        """Ensure the assigned team member belongs to the task's organization"""
        if value and value.organization != self.instance.organization:
            raise serializers.ValidationError("Team member must belong to the same organization as the task")
        return value


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority', 'due_date',
            'assigned_to'
        ]
    
    def create(self, validated_data):
        # Set organization and created_by automatically
        user = self.context['request'].user
        validated_data['organization'] = user.owned_organizations.first()  # Assuming user has organization
        validated_data['created_by'] = user
        
        task = Task.objects.create(**validated_data)
        
        # Create task history entry
        TaskHistory.objects.create(
            task=task,
            action='created',
            actor=user,
            description=f"Task '{task.title}' was created"
        )
        
        return task
    
    def validate_assigned_to(self, value):
        """Ensure the assigned team member belongs to the user's organization"""
        if value:
            user = self.context['request'].user
            user_org = user.owned_organizations.first()
            if value.organization != user_org:
                raise serializers.ValidationError("Team member must belong to your organization")
        return value


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tasks"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority', 
            'due_date', 'assigned_to'
        ]
    
    def validate_assigned_to(self, value):
        """Ensure the assigned team member belongs to the task's organization"""
        if value and value.organization != self.instance.organization:
            raise serializers.ValidationError("Team member must belong to the same organization as the task")
        return value
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        # Check if status is being changed
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Track changes
        changes = []
        for field, value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != value:
                if field == 'assigned_to':
                    old_name = old_value.name if old_value else "Unassigned"
                    new_name = value.name if value else "Unassigned"
                    changes.append(f"Assigned to changed from {old_name} to {new_name}")
                else:
                    changes.append(f"{field.replace('_', ' ').title()} changed from '{old_value}' to '{value}'")
        
        # Update the task
        task = super().update(instance, validated_data)
        
        # Create history entries for changes
        if changes:
            change_description = "Task updated: " + ", ".join(changes)
            TaskHistory.objects.create(
                task=task,
                action='updated',
                actor=user,
                description=change_description
            )
        
        # Create specific status change history if needed
        if old_status != new_status:
            action = new_status if new_status in ['completed', 'approved', 'rejected'] else 'status_changed'
            
            # Update completion date if task was completed
            if new_status == 'completed' and old_status != 'completed':
                from django.utils import timezone
                task.completed_at = timezone.now()
                task.save(update_fields=['completed_at'])
            
            TaskHistory.objects.create(
                task=task,
                action=action,
                actor=user,
                description=f"Status changed from {old_status} to {new_status}"
            )
        
        return task


class TaskApproveSerializer(serializers.ModelSerializer):
    """Serializer for approving tasks"""
    
    class Meta:
        model = Task
        fields = []
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        # Only completed tasks can be approved
        if instance.status != 'completed':
            raise serializers.ValidationError("Only completed tasks can be approved")
        
        # Update task
        instance.status = 'approved'
        instance.approved_by = user
        instance.save()
        
        # Create history entry
        TaskHistory.objects.create(
            task=instance,
            action='approved',
            actor=user,
            description=f"Task was approved by {user.get_full_name() or user.username}"
        )
        
        return instance


class TaskRejectSerializer(serializers.ModelSerializer):
    """Serializer for rejecting tasks"""
    
    rejection_reason = serializers.CharField(required=True)
    
    class Meta:
        model = Task
        fields = ['rejection_reason']
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        rejection_reason = validated_data.get('rejection_reason')
        
        # Only completed tasks can be rejected
        if instance.status != 'completed':
            raise serializers.ValidationError("Only completed tasks can be rejected")
        
        # Update task
        instance.status = 'rejected'
        instance.rejected_by = user
        instance.rejection_reason = rejection_reason
        instance.save()
        
        # Create history entry
        TaskHistory.objects.create(
            task=instance,
            action='rejected',
            actor=user,
            description=f"Task was rejected by {user.get_full_name() or user.username}. Reason: {rejection_reason}"
        )
        
        return instance


class TaskDelegateSerializer(serializers.ModelSerializer):
    """Serializer for delegating tasks"""
    
    team_member_id = serializers.IntegerField(required=True)
    delegation_notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Task
        fields = ['team_member_id', 'delegation_notes']
    
    def validate(self, data):
        """Validate team member exists and belongs to the same organization"""
        team_member_id = data.get('team_member_id')
        
        # Get team member
        from organizations.models import TeamMember
        try:
            team_member = TeamMember.objects.get(id=team_member_id)
        except TeamMember.DoesNotExist:
            raise serializers.ValidationError({"team_member_id": "Team member not found"})
        
        # Ensure team member belongs to the same organization
        task = self.instance
        if team_member.organization != task.organization:
            raise serializers.ValidationError(
                {"team_member_id": "Team member must belong to the same organization as the task"}
            )
        
        # Store team member for later use
        data['team_member'] = team_member
        return data
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        team_member = validated_data.get('team_member')
        delegation_notes = validated_data.get('delegation_notes', '')
        
        # Check if task is assigned to the current user or user has assign permission
        from django.utils import timezone
        is_assigned_to_user = False
        
        # If task is assigned to a team member, check if that team member belongs to the current user
        if instance.assigned_to:
            # Check if the team member email matches the user's email
            is_assigned_to_user = instance.assigned_to.email == user.email
        
        # If not assigned to the current user, check for assign_tasks permission
        from tasks.permissions import CanAssignTasks
        has_assign_permission = CanAssignTasks().has_permission(self.context['request'], None)
        
        if not is_assigned_to_user and not has_assign_permission:
            raise serializers.ValidationError(
                "You can only delegate tasks assigned to you or if you have the assign_tasks permission"
            )
        
        # Update task
        instance.assigned_to = team_member
        instance.delegated_by = user
        instance.delegation_notes = delegation_notes
        instance.delegation_date = timezone.now()
        instance.save()
        
        # Get names for history
        user_name = user.get_full_name() or user.username
        team_member_name = team_member.name
        
        # Create history entry
        note_text = f" with note: {delegation_notes}" if delegation_notes else ""
        TaskHistory.objects.create(
            task=instance,
            action='assigned',
            actor=user,
            description=f"Task was delegated by {user_name} to {team_member_name}{note_text}"
        )
        
        return instance