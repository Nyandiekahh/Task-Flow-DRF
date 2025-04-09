from rest_framework import serializers
from .models import (
    Task, TaskAttachment, Comment, TaskHistory,
    TaskAssignee, TaskApprover, TaskWatcher,
    TaskPrerequisite, TaskLink
)
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
        if hasattr(obj.author, 'get_full_name'):
            name = obj.author.get_full_name()
            if name and name.strip():
                return name
            
        if hasattr(obj.author, 'username') and obj.author.username:
            return obj.author.username
        
        if hasattr(obj.author, 'email') and obj.author.email:
            return obj.author.email.split('@')[0]
        
        return "Unknown User"


class TaskHistorySerializer(serializers.ModelSerializer):
    """Serializer for task history"""
    
    actor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskHistory
        fields = ['id', 'action', 'actor', 'actor_name', 'description', 'timestamp']
        read_only_fields = ['action', 'actor', 'description', 'timestamp']
    
    def get_actor_name(self, obj):
        if hasattr(obj.actor, 'get_full_name'):
            name = obj.actor.get_full_name()
            if name and name.strip():
                return name
            
        if hasattr(obj.actor, 'username') and obj.actor.username:
            return obj.actor.username
        
        if hasattr(obj.actor, 'email') and obj.actor.email:
            return obj.actor.email.split('@')[0]
        
        return "Unknown User"


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for team members"""
    
    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'email']


class TaskListSerializer(serializers.ModelSerializer):
    """Simplified serializer for task listings"""
    
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'category', 'due_date',
            'assigned_to', 'assigned_to_name', 'created_by',
            'created_by_name', 'created_at', 'updated_at', 'tags_list'
        ]
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.name
        return None
    
    def get_created_by_name(self, obj):
        if hasattr(obj.created_by, 'get_full_name'):
            name = obj.created_by.get_full_name()
            if name and name.strip():
                return name
            
        if hasattr(obj.created_by, 'username') and obj.created_by.username:
            return obj.created_by.username
        
        if hasattr(obj.created_by, 'email') and obj.created_by.email:
            return obj.created_by.email.split('@')[0]
        
        return "Unknown User"
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for task details with all enhanced fields"""
    
    comments = CommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    history = TaskHistorySerializer(many=True, read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    rejected_by_name = serializers.SerializerMethodField()
    delegated_by_name = serializers.SerializerMethodField()
    
    # Add project name if available
    project_name = serializers.SerializerMethodField()
    
    # Tags as list
    tags_list = serializers.SerializerMethodField()
    
    # Additional fields for many-to-many relationships
    assignees = serializers.SerializerMethodField()
    approvers = serializers.SerializerMethodField()
    watchers = serializers.SerializerMethodField()
    prerequisites = serializers.SerializerMethodField()
    linked_tasks = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'category',
            'start_date', 'due_date', 'estimated_hours',
            'is_recurring', 'recurring_frequency', 'recurring_ends_on',
            'organization', 'project', 'project_name', 'visibility',
            'tags', 'tags_list', 'acceptance_criteria', 'notes',
            'time_tracking_enabled', 'budget_hours', 'is_billable', 'client_reference',
            'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_name',
            'assignees', 'approvers', 'watchers',
            'prerequisites', 'linked_tasks',
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
        if hasattr(obj.created_by, 'get_full_name'):
            name = obj.created_by.get_full_name()
            if name and name.strip():
                return name
            
        if hasattr(obj.created_by, 'username') and obj.created_by.username:
            return obj.created_by.username
        
        if hasattr(obj.created_by, 'email') and obj.created_by.email:
            return obj.created_by.email.split('@')[0]
        
        return "Unknown User"
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            if hasattr(obj.approved_by, 'get_full_name'):
                name = obj.approved_by.get_full_name()
                if name and name.strip():
                    return name
                
            if hasattr(obj.approved_by, 'username') and obj.approved_by.username:
                return obj.approved_by.username
            
            if hasattr(obj.approved_by, 'email') and obj.approved_by.email:
                return obj.approved_by.email.split('@')[0]
            
            return "Unknown User"
        return None
    
    def get_rejected_by_name(self, obj):
        if obj.rejected_by:
            if hasattr(obj.rejected_by, 'get_full_name'):
                name = obj.rejected_by.get_full_name()
                if name and name.strip():
                    return name
                
            if hasattr(obj.rejected_by, 'username') and obj.rejected_by.username:
                return obj.rejected_by.username
            
            if hasattr(obj.rejected_by, 'email') and obj.rejected_by.email:
                return obj.rejected_by.email.split('@')[0]
            
            return "Unknown User"
        return None
        
    def get_delegated_by_name(self, obj):
        if obj.delegated_by:
            if hasattr(obj.delegated_by, 'get_full_name'):
                name = obj.delegated_by.get_full_name()
                if name and name.strip():
                    return name
                
            if hasattr(obj.delegated_by, 'username') and obj.delegated_by.username:
                return obj.delegated_by.username
            
            if hasattr(obj.delegated_by, 'email') and obj.delegated_by.email:
                return obj.delegated_by.email.split('@')[0]
            
            return "Unknown User"
        return None
    
    def get_project_name(self, obj):
        if obj.project:
            return obj.project.name
        return None
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()
    
    def get_assignees(self, obj):
        assignees = []
        for assignment in TaskAssignee.objects.filter(task=obj):
            assignees.append({
                'id': assignment.team_member.id,
                'name': assignment.team_member.name,
                'email': assignment.team_member.email
            })
        return assignees
    
    def get_approvers(self, obj):
        approvers = []
        for approval in TaskApprover.objects.filter(task=obj):
            approvers.append({
                'id': approval.team_member.id,
                'name': approval.team_member.name,
                'email': approval.team_member.email
            })
        return approvers
    
    def get_watchers(self, obj):
        watchers = []
        for watcher in TaskWatcher.objects.filter(task=obj):
            watchers.append({
                'id': watcher.team_member.id,
                'name': watcher.team_member.name,
                'email': watcher.team_member.email
            })
        return watchers
    
    def get_prerequisites(self, obj):
        prerequisites = []
        for prereq in TaskPrerequisite.objects.filter(task=obj):
            prerequisites.append({
                'id': prereq.prerequisite_task.id,
                'title': prereq.prerequisite_task.title,
                'status': prereq.prerequisite_task.status
            })
        return prerequisites
    
    def get_linked_tasks(self, obj):
        linked_tasks = []
        
        # Get tasks linked as task1
        for link in TaskLink.objects.filter(task1=obj):
            linked_tasks.append({
                'id': link.task2.id,
                'title': link.task2.title,
                'status': link.task2.status
            })
        
        # Get tasks linked as task2
        for link in TaskLink.objects.filter(task2=obj):
            linked_tasks.append({
                'id': link.task1.id,
                'title': link.task1.title,
                'status': link.task1.status
            })
        
        return linked_tasks
    
    def validate_assigned_to(self, value):
        """Ensure the assigned team member belongs to the task's organization"""
        if value and value.organization != self.instance.organization:
            raise serializers.ValidationError("Team member must belong to the same organization as the task")
        return value


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks with all enhanced fields"""
    
    tags_list = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority', 'category',
            'start_date', 'due_date', 'estimated_hours',
            'assigned_to', 'project', 'tags', 'tags_list',
            'is_recurring', 'recurring_frequency', 'recurring_ends_on',
            'acceptance_criteria', 'notes', 'visibility',
            'time_tracking_enabled', 'budget_hours', 'is_billable', 'client_reference'
        ]
    
    def create(self, validated_data):
        # Extract tags_list if it exists
        tags_list = validated_data.pop('tags_list', None)
        
        # Get many-to-many fields from initial data
        assignees_data = self.initial_data.get('assignees[]', [])
        approvers_data = self.initial_data.get('approvers[]', [])
        watchers_data = self.initial_data.get('watchers[]', [])
        prerequisites_data = self.initial_data.get('prerequisites[]', [])
        linked_tasks_data = self.initial_data.get('linked_tasks[]', [])
        
        # Handle custom tags from request data (from form field custom_tags)
        if 'custom_tags' in self.initial_data:
            custom_tags = self.initial_data.get('custom_tags', '')
            if custom_tags:
                if tags_list is None:
                    tags_list = []
                tags_list.extend([tag.strip() for tag in custom_tags.split(',') if tag.strip()])
        
        # If tags_list is provided, convert to comma-separated string
        if tags_list:
            validated_data['tags'] = ', '.join(tags_list)
        
        # Set organization and created_by automatically
        user = self.context['request'].user
        validated_data['organization'] = user.owned_organizations.first()  # Assuming user has organization
        validated_data['created_by'] = user
        
        # Create task
        task = Task.objects.create(**validated_data)
        
        # Add assignees
        for assignee_id in assignees_data:
            try:
                team_member = TeamMember.objects.get(id=assignee_id)
                TaskAssignee.objects.create(task=task, team_member=team_member)
            except TeamMember.DoesNotExist:
                pass
        
        # Add approvers
        for approver_id in approvers_data:
            try:
                team_member = TeamMember.objects.get(id=approver_id)
                TaskApprover.objects.create(task=task, team_member=team_member)
            except TeamMember.DoesNotExist:
                pass
        
        # Add watchers
        for watcher_id in watchers_data:
            try:
                team_member = TeamMember.objects.get(id=watcher_id)
                TaskWatcher.objects.create(task=task, team_member=team_member)
            except TeamMember.DoesNotExist:
                pass
        
        # Add prerequisites
        for prerequisite_id in prerequisites_data:
            try:
                prerequisite_task = Task.objects.get(id=prerequisite_id)
                TaskPrerequisite.objects.create(task=task, prerequisite_task=prerequisite_task)
            except Task.DoesNotExist:
                pass
        
        # Add linked tasks
        for linked_task_id in linked_tasks_data:
            try:
                linked_task = Task.objects.get(id=linked_task_id)
                # Create link in one direction only (the get_linked_tasks method will handle bidirectional retrieval)
                TaskLink.objects.create(task1=task, task2=linked_task)
            except Task.DoesNotExist:
                pass
        
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
    
    def validate(self, data):
        """Perform cross-field validation"""
        
        # Validate recurring task fields
        if data.get('is_recurring'):
            if not data.get('recurring_frequency'):
                raise serializers.ValidationError({"recurring_frequency": "Recurring frequency is required for recurring tasks"})
        
        # Validate billable task fields
        if data.get('is_billable') and data.get('time_tracking_enabled') is False:
            raise serializers.ValidationError({"is_billable": "Time tracking must be enabled for billable tasks"})
        
        # Ensure due date is after start date if both are provided
        start_date = data.get('start_date')
        due_date = data.get('due_date')
        if start_date and due_date and start_date > due_date:
            raise serializers.ValidationError({"due_date": "Due date must be after start date"})
        
        return data


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tasks"""
    
    tags_list = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority', 'category',
            'start_date', 'due_date', 'estimated_hours', 'assigned_to',
            'project', 'tags', 'tags_list', 'is_recurring', 'recurring_frequency', 'recurring_ends_on',
            'acceptance_criteria', 'notes', 'visibility',
            'time_tracking_enabled', 'budget_hours', 'is_billable', 'client_reference'
        ]
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        # Extract tags_list if it exists
        tags_list = validated_data.pop('tags_list', None)
        
        # Handle custom tags from request data (from form field custom_tags)
        if 'custom_tags' in self.initial_data:
            custom_tags = self.initial_data.get('custom_tags', '')
            if custom_tags:
                if tags_list is None:
                    tags_list = []
                tags_list.extend([tag.strip() for tag in custom_tags.split(',') if tag.strip()])
        
        # If tags_list is provided, convert to comma-separated string
        if tags_list:
            validated_data['tags'] = ', '.join(tags_list)
        
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
        
        # Get many-to-many data to update
        assignees_data = self.initial_data.get('assignees[]', None)
        approvers_data = self.initial_data.get('approvers[]', None)
        watchers_data = self.initial_data.get('watchers[]', None)
        prerequisites_data = self.initial_data.get('prerequisites[]', None)
        linked_tasks_data = self.initial_data.get('linked_tasks[]', None)
        
        # Update the task
        task = super().update(instance, validated_data)
        
        # Update assignees if provided
        if assignees_data is not None:
            # Clear existing assignees
            TaskAssignee.objects.filter(task=task).delete()
            
            # Add new assignees
            for assignee_id in assignees_data:
                try:
                    team_member = TeamMember.objects.get(id=assignee_id)
                    TaskAssignee.objects.create(task=task, team_member=team_member)
                except TeamMember.DoesNotExist:
                    pass
            
            changes.append("Additional assignees updated")
        
        # Update approvers if provided
        if approvers_data is not None:
            # Clear existing approvers
            TaskApprover.objects.filter(task=task).delete()
            
            # Add new approvers
            for approver_id in approvers_data:
                try:
                    team_member = TeamMember.objects.get(id=approver_id)
                    TaskApprover.objects.create(task=task, team_member=team_member)
                except TeamMember.DoesNotExist:
                    pass
            
            changes.append("Approvers updated")
        
        # Update watchers if provided
        if watchers_data is not None:
            # Clear existing watchers
            TaskWatcher.objects.filter(task=task).delete()
            
            # Add new watchers
            for watcher_id in watchers_data:
                try:
                    team_member = TeamMember.objects.get(id=watcher_id)
                    TaskWatcher.objects.create(task=task, team_member=team_member)
                except TeamMember.DoesNotExist:
                    pass
            
            changes.append("Watchers updated")
        
        # Update prerequisites if provided
        if prerequisites_data is not None:
            # Clear existing prerequisites
            TaskPrerequisite.objects.filter(task=task).delete()
            
            # Add new prerequisites
            for prerequisite_id in prerequisites_data:
                try:
                    prerequisite_task = Task.objects.get(id=prerequisite_id)
                    TaskPrerequisite.objects.create(task=task, prerequisite_task=prerequisite_task)
                except Task.DoesNotExist:
                    pass
            
            changes.append("Prerequisites updated")
        
        # Update linked tasks if provided
        if linked_tasks_data is not None:
            # Clear existing linked tasks
            TaskLink.objects.filter(task1=task).delete()
            TaskLink.objects.filter(task2=task).delete()
            
            # Add new linked tasks
            for linked_task_id in linked_tasks_data:
                try:
                    linked_task = Task.objects.get(id=linked_task_id)
                    TaskLink.objects.create(task1=task, task2=linked_task)
                except Task.DoesNotExist:
                    pass
            
            changes.append("Linked tasks updated")
        
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
    
    def validate_assigned_to(self, value):
        """Ensure the assigned team member belongs to the task's organization"""
        if value and value.organization != self.instance.organization:
            raise serializers.ValidationError("Team member must belong to the same organization as the task")
        return value
    
    def validate(self, data):
        """Perform cross-field validation"""
        
        # Validate recurring task fields
        if data.get('is_recurring', self.instance.is_recurring):
            if not data.get('recurring_frequency', self.instance.recurring_frequency):
                raise serializers.ValidationError({"recurring_frequency": "Recurring frequency is required for recurring tasks"})
        
        # Validate billable task fields
        is_billable = data.get('is_billable', self.instance.is_billable)
        time_tracking_enabled = data.get('time_tracking_enabled', self.instance.time_tracking_enabled)
        if is_billable and not time_tracking_enabled:
            raise serializers.ValidationError({"is_billable": "Time tracking must be enabled for billable tasks"})
        
        # Ensure due date is after start date if both are provided
        start_date = data.get('start_date', self.instance.start_date)
        due_date = data.get('due_date', self.instance.due_date)
        if start_date and due_date and start_date > due_date:
            raise serializers.ValidationError({"due_date": "Due date must be after start date"})
        
        return data


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
        
        # Get user name with the enhanced method
        user_name = user.get_full_name().strip() if hasattr(user, 'get_full_name') and user.get_full_name() else (
            user.username if hasattr(user, 'username') and user.username else (
                user.email.split('@')[0] if hasattr(user, 'email') and user.email else "Unknown User"
            )
        )
        
        # Create history entry
        TaskHistory.objects.create(
            task=instance,
            action='approved',
            actor=user,
            description=f"Task was approved by {user_name}"
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
        
        # Get user name with the enhanced method
        user_name = user.get_full_name().strip() if hasattr(user, 'get_full_name') and user.get_full_name() else (
            user.username if hasattr(user, 'username') and user.username else (
                user.email.split('@')[0] if hasattr(user, 'email') and user.email else "Unknown User"
            )
        )
        
        # Create history entry
        TaskHistory.objects.create(
            task=instance,
            action='rejected',
            actor=user,
            description=f"Task was rejected by {user_name}. Reason: {rejection_reason}"
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
        user_name = user.get_full_name().strip() if hasattr(user, 'get_full_name') and user.get_full_name() else (
            user.username if hasattr(user, 'username') and user.username else (
                user.email.split('@')[0] if hasattr(user, 'email') and user.email else "Unknown User"
            )
        )
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