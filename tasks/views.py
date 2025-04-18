from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import Task, Comment, TaskAttachment, TaskHistory, TaskWatcher, TaskAssignee
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskApproveSerializer,
    TaskRejectSerializer,
    TaskDelegateSerializer,
    CommentSerializer,
    TaskAttachmentSerializer,
    TaskHistorySerializer
)
from .permissions import (
    HasTaskPermission,
    CanCreateTasks,
    CanViewTasks,
    CanUpdateTasks,
    CanDeleteTasks,
    CanAssignTasks,
    CanApproveTasks,
    CanRejectTasks,
    CanComment
)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for handling task operations"""
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return tasks for the user's organization.
        For regular team members, only return tasks where they are:
        1. Assigned to the task (primary assignee)
        2. Additional assignee (through TaskAssignee)
        3. Watcher (through TaskWatcher)
        4. Task creator
        
        Filter based on query parameters if provided.
        """
        user = self.request.user
        
        # Check if user is an organization owner
        organization = user.owned_organizations.first()
        is_org_owner = organization is not None
        
        # If not an owner, get organization from team membership
        if not organization:
            try:
                team_membership = user.team_memberships.first()
                if team_membership:
                    organization = team_membership.organization
                    # Get the team member object for this user
                    team_member = team_membership
                else:
                    # If user is not associated with any organization, return empty queryset
                    return Task.objects.none()
            except Exception as e:
                print(f"Error getting team membership: {e}")
                # If there's an error, return empty queryset
                return Task.objects.none()
        
        # Base queryset - all tasks for this organization
        base_queryset = Task.objects.filter(organization=organization)
        
        # For organization owners, get all tasks in the organization
        if is_org_owner:
            queryset = base_queryset
        else:
            # For regular team members, only show tasks they're involved with
            # 1. Tasks where they are the primary assignee
            # 2. Tasks where they are additional assignees (through TaskAssignee)
            # 3. Tasks where they are watchers (through TaskWatcher)
            # 4. Tasks they created
            team_member = user.team_memberships.first()
            queryset = base_queryset.filter(
                Q(assigned_to=team_member) |
                Q(assignees_through__team_member=team_member) |
                Q(watchers_through__team_member=team_member) |
                Q(created_by=user)
            ).distinct()
        
        # Filter by status if specified
        status_param = self.request.query_params.get('status')
        if status_param:
            statuses = status_param.split(',')
            queryset = queryset.filter(status__in=statuses)
        
        # Filter by priority if specified
        priority_param = self.request.query_params.get('priority')
        if priority_param:
            priorities = priority_param.split(',')
            queryset = queryset.filter(priority__in=priorities)
        
        # Filter by assigned team member if specified
        assigned_to_param = self.request.query_params.get('assigned_to')
        if assigned_to_param:
            queryset = queryset.filter(assigned_to_id=assigned_to_param)
        
        # Filter by created_by if specified
        created_by_param = self.request.query_params.get('created_by')
        if created_by_param:
            queryset = queryset.filter(created_by_id=created_by_param)
        
        # Date range filter for due_date
        due_date_after = self.request.query_params.get('due_date_after')
        due_date_before = self.request.query_params.get('due_date_before')
        
        if due_date_after:
            queryset = queryset.filter(due_date__gte=due_date_after)
        if due_date_before:
            queryset = queryset.filter(due_date__lte=due_date_before)
        
        # Search term
        search_term = self.request.query_params.get('search')
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action"""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return TaskUpdateSerializer
        elif self.action == 'approve':
            return TaskApproveSerializer
        elif self.action == 'reject':
            return TaskRejectSerializer
        elif self.action == 'delegate':
            return TaskDelegateSerializer
        return TaskDetailSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action"""
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, CanCreateTasks]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated, CanViewTasks]
        elif self.action in ['update', 'partial_update']:
            self.permission_classes = [permissions.IsAuthenticated, CanUpdateTasks]
        elif self.action == 'destroy':
            self.permission_classes = [permissions.IsAuthenticated, CanDeleteTasks]
        elif self.action == 'assign':
            self.permission_classes = [permissions.IsAuthenticated, CanAssignTasks]
        elif self.action == 'delegate':
            # For delegation, we'll check inside the serializer if the task is assigned to the user
            # or if they have the assign permission
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'approve':
            self.permission_classes = [permissions.IsAuthenticated, CanApproveTasks]
        elif self.action == 'reject':
            self.permission_classes = [permissions.IsAuthenticated, CanRejectTasks]
        elif self.action in ['add_comment', 'add_time']:
            self.permission_classes = [permissions.IsAuthenticated, CanComment]
        else:
            self.permission_classes = [permissions.IsAuthenticated, HasTaskPermission]
        
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign a task to a team member"""
        task = self.get_object()
        team_member_id = request.data.get('team_member_id')
        
        if not team_member_id:
            return Response({'error': 'team_member_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get team member and verify organization
            from organizations.models import TeamMember
            team_member = TeamMember.objects.get(id=team_member_id)
            
            if team_member.organization != task.organization:
                return Response(
                    {'error': 'Team member must belong to the same organization as the task'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update task
            task.assigned_to = team_member
            task.save()
            
            # Create history entry
            TaskHistory.objects.create(
                task=task,
                action='assigned',
                actor=request.user,
                description=f"Task assigned to {team_member.name}"
            )
            
            serializer = TaskDetailSerializer(task)
            return Response(serializer.data)
            
        except TeamMember.DoesNotExist:
            return Response({'error': 'Team member not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a completed task"""
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a completed task with a reason"""
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to a task"""
        task = self.get_object()
        text = request.data.get('text')
        
        if not text:
            return Response({'error': 'Comment text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create comment
        comment = Comment.objects.create(
            task=task,
            text=text,
            author=request.user
        )
        
        # Create history entry
        TaskHistory.objects.create(
            task=task,
            action='commented',
            actor=request.user,
            description=f"Comment added: {text[:50]}{'...' if len(text) > 50 else ''}"
        )
        
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        """Add an attachment to a task"""
        task = self.get_object()
        
        if 'file' not in request.FILES:
            return Response({'error': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Create attachment
        attachment = TaskAttachment.objects.create(
            task=task,
            file=file,
            filename=file.name,
            uploaded_by=request.user
        )
        
        # Create history entry
        TaskHistory.objects.create(
            task=task,
            action='updated',
            actor=request.user,
            description=f"File attachment added: {file.name}"
        )
        
        return Response(TaskAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)
        
    @action(detail=True, methods=['post'])
    def add_time(self, request, pk=None):
        """Add time spent to a task"""
        task = self.get_object()
        hours = request.data.get('hours')
        description = request.data.get('description', '')
        
        if not hours:
            return Response({'error': 'Hours is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            hours = float(hours)
        except ValueError:
            return Response({'error': 'Hours must be a number'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create comment with time info
        comment_text = f"Time logged: {hours} hours. {description}"
        
        # Create comment
        comment = Comment.objects.create(
            task=task,
            text=comment_text,
            author=request.user
        )
        
        # Create history entry
        TaskHistory.objects.create(
            task=task,
            action='time_logged',  # Using a dedicated action type for time logging
            actor=request.user,
            description=f"Time entry added: {hours} hours"
        )
        
        return Response({
            'success': True, 
            'hours': hours,
            'comment': CommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def delegate(self, request, pk=None):
        """Delegate a task to another team member"""
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(TaskDetailSerializer(task).data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for handling comments"""
    
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CanComment]
    
    def get_queryset(self):
        """Return comments for the user's organization"""
        user = self.request.user
        organization = user.owned_organizations.first()
        
        if not organization:
            try:
                team_member = user.team_memberships.first()
                if team_member:
                    organization = team_member.organization
                else:
                    return Comment.objects.none()
            except:
                return Comment.objects.none()
        
        # Filter by task if specified
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return Comment.objects.filter(task__organization=organization, task_id=task_id)
        
        return Comment.objects.filter(task__organization=organization)
    
    def perform_create(self, serializer):
        """Set author automatically on create"""
        serializer.save(author=self.request.user)


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet for handling task attachments"""
    
    serializer_class = TaskAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, HasTaskPermission]
    
    def get_queryset(self):
        """Return attachments for the user's organization"""
        user = self.request.user
        organization = user.owned_organizations.first()
        
        if not organization:
            try:
                team_member = user.team_memberships.first()
                if team_member:
                    organization = team_member.organization
                else:
                    return TaskAttachment.objects.none()
            except:
                return TaskAttachment.objects.none()
        
        # Filter by task if specified
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return TaskAttachment.objects.filter(task__organization=organization, task_id=task_id)
        
        return TaskAttachment.objects.filter(task__organization=organization)
    
    def perform_create(self, serializer):
        """Set uploaded_by automatically on create"""
        serializer.save(uploaded_by=self.request.user)


class TaskHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for handling task history (read-only)"""
    
    serializer_class = TaskHistorySerializer
    permission_classes = [permissions.IsAuthenticated, CanViewTasks]
    
    def get_queryset(self):
        """Return history for the user's organization"""
        user = self.request.user
        organization = user.owned_organizations.first()
        
        if not organization:
            try:
                team_member = user.team_memberships.first()
                if team_member:
                    organization = team_member.organization
                else:
                    return TaskHistory.objects.none()
            except:
                return TaskHistory.objects.none()
        
        # Filter by task if specified
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return TaskHistory.objects.filter(task__organization=organization, task_id=task_id)
        
        return TaskHistory.objects.filter(task__organization=organization)