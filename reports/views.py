# reports/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Count, Sum, Avg, F, Q, Case, When, Value, IntegerField, DurationField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Coalesce
from django.utils.dateparse import parse_date

from .models import ReportConfiguration
from .serializers import (
    ReportConfigurationSerializer,
    ProjectStatusReportSerializer,
    TeamProductivityReportSerializer,
    TaskCompletionReportSerializer,
    TimeTrackingReportSerializer,
    OverdueTasksReportSerializer
)

from projects.models import Project
from tasks.models import Task, TaskHistory
from organizations.models import TeamMember

class ReportConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing report configurations"""
    
    serializer_class = ReportConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return configurations for the user's organization"""
        user = self.request.user
        
        # Find user's organization
        if hasattr(user, 'organization') and user.organization:
            organization = user.organization
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        else:
            return ReportConfiguration.objects.none()
            
        return ReportConfiguration.objects.filter(organization=organization)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate a report using a saved configuration"""
        config = self.get_object()
        
        # Update the last_generated timestamp
        config.last_generated = timezone.now()
        config.save()
        
        # Generate the report based on the configuration
        if config.report_type == 'project_status':
            return self._generate_project_status_report(config.configuration)
        elif config.report_type == 'team_productivity':
            return self._generate_team_productivity_report(config.configuration)
        elif config.report_type == 'task_completion':
            return self._generate_task_completion_report(config.configuration)
        elif config.report_type == 'time_tracking':
            return self._generate_time_tracking_report(config.configuration)
        elif config.report_type == 'overdue_tasks':
            return self._generate_overdue_tasks_report(config.configuration)
        
        return Response({"error": "Invalid report type"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Helper methods to call the appropriate report generator
    def _generate_project_status_report(self, config):
        report_view = ProjectStatusReportView()
        return report_view.post(self.request, config=config)
    
    def _generate_team_productivity_report(self, config):
        report_view = TeamProductivityReportView()
        return report_view.post(self.request, config=config)
    
    def _generate_task_completion_report(self, config):
        report_view = TaskCompletionReportView()
        return report_view.post(self.request, config=config)
    
    def _generate_time_tracking_report(self, config):
        report_view = TimeTrackingReportView()
        return report_view.post(self.request, config=config)
    
    def _generate_overdue_tasks_report(self, config):
        report_view = OverdueTasksReportView()
        return report_view.post(self.request, config=config)


class ProjectStatusReportView(APIView):
    """API View for generating project status reports"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, config=None):
        """Generate a project status report"""
        # Use passed configuration or request data
        data = config if config else request.data
        
        # Validate parameters
        serializer = ProjectStatusReportSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's organization
        user = request.user
        if hasattr(user, 'organization') and user.organization:
            organization = user.organization
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        else:
            return Response({"error": "No organization found for user"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter projects by organization
        projects_queryset = Project.objects.filter(organization=organization)
        
        # Apply filters from parameters
        if 'project_id' in serializer.validated_data:
            projects_queryset = projects_queryset.filter(id=serializer.validated_data['project_id'])
        
        # Get project statistics
        project_stats = []
        for project in projects_queryset:
            # Get tasks for this project
            tasks = Task.objects.filter(project=project)
            
            # Apply date filters if provided
            if 'start_date' in serializer.validated_data:
                start_date = serializer.validated_data['start_date']
                tasks = tasks.filter(Q(due_date__gte=start_date) | Q(created_at__gte=start_date))
            
            if 'end_date' in serializer.validated_data:
                end_date = serializer.validated_data['end_date']
                tasks = tasks.filter(Q(due_date__lte=end_date) | Q(created_at__lte=end_date))
            
            # Count tasks by status
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status__in=['completed', 'approved']).count()
            in_progress_tasks = tasks.filter(status='in_progress').count()
            pending_tasks = tasks.filter(status='pending').count()
            overdue_tasks = tasks.filter(due_date__lt=timezone.now().date(), status__in=['pending', 'in_progress']).count()
            
            # Calculate completion percentage
            completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Calculate timeline metrics
            days_remaining = None
            days_total = None
            timeline_percentage = None
            
            if project.start_date and project.end_date:
                today = timezone.now().date()
                days_total = (project.end_date - project.start_date).days
                
                if today < project.start_date:
                    # Project hasn't started yet
                    days_remaining = days_total
                    timeline_percentage = 0
                elif today > project.end_date:
                    # Project is past end date
                    days_remaining = 0
                    timeline_percentage = 100
                else:
                    # Project is in progress
                    days_elapsed = (today - project.start_date).days
                    days_remaining = (project.end_date - today).days
                    timeline_percentage = (days_elapsed / days_total * 100) if days_total > 0 else 0
            
            # Add to project stats
            project_stats.append({
                'id': project.id,
                'name': project.name,
                'status': project.status,
                'start_date': project.start_date,
                'end_date': project.end_date,
                'days_remaining': days_remaining,
                'days_total': days_total,
                'timeline_percentage': timeline_percentage,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'pending_tasks': pending_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_percentage': completion_percentage,
                'team_members_count': project.team_members.count(),
            })
        
        # Return the report data
        return Response({
            'report_type': 'project_status',
            'generated_at': timezone.now(),
            'parameters': serializer.validated_data,
            'projects': project_stats
        })


class TeamProductivityReportView(APIView):
    """API View for generating team productivity reports"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, config=None):
        """Generate a team productivity report"""
        # Use passed configuration or request data
        data = config if config else request.data
        
        # Validate parameters
        serializer = TeamProductivityReportSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's organization
        user = request.user
        if hasattr(user, 'organization') and user.organization:
            organization = user.organization
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        else:
            return Response({"error": "No organization found for user"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get team members
        team_members_queryset = TeamMember.objects.filter(organization=organization)
        
        # Apply filters
        if 'team_member_id' in serializer.validated_data:
            team_members_queryset = team_members_queryset.filter(
                id=serializer.validated_data['team_member_id']
            )
        
        # Define date range
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        
        # Use default date range if not provided
        if not start_date:
            # Default to last 30 days
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        
        if not end_date:
            end_date = timezone.now().date()
        
        # Get group_by parameter
        group_by = serializer.validated_data.get('group_by', 'week')
        
        # Collect productivity stats for each team member
        team_productivity = []
        
        for member in team_members_queryset:
            # Get tasks assigned to this team member
            member_tasks = Task.objects.filter(
                assigned_to=member,
                organization=organization
            )
            
            # Apply date filters
            if start_date:
                member_tasks = member_tasks.filter(
                    Q(created_at__date__gte=start_date) | 
                    Q(completed_at__date__gte=start_date)
                )
            
            if end_date:
                member_tasks = member_tasks.filter(
                    Q(created_at__date__lte=end_date) | 
                    Q(completed_at__date__lte=end_date)
                )
            
            # Calculate metrics
            total_tasks = member_tasks.count()
            completed_tasks = member_tasks.filter(status__in=['completed', 'approved']).count()
            
            # Calculate on-time completion rate
            on_time_tasks = member_tasks.filter(
                status__in=['completed', 'approved'],
                due_date__gte=F('completed_at')
            ).count()
            
            on_time_rate = (on_time_tasks / completed_tasks * 100) if completed_tasks > 0 else 0
            
            # Get task history to calculate average task duration
            task_history = TaskHistory.objects.filter(
                task__in=member_tasks.filter(status__in=['completed', 'approved']),
                action='completed'
            )
            
            # Group data based on group_by parameter
            grouped_data = []
            
            if group_by == 'day':
                # Group by day
                for day in range((end_date - start_date).days + 1):
                    current_date = start_date + timezone.timedelta(days=day)
                    day_tasks = member_tasks.filter(
                        Q(created_at__date=current_date) | 
                        Q(completed_at__date=current_date)
                    )
                    day_completed = day_tasks.filter(
                        status__in=['completed', 'approved'],
                        completed_at__date=current_date
                    ).count()
                    
                    grouped_data.append({
                        'date': current_date,
                        'total_tasks': day_tasks.count(),
                        'completed_tasks': day_completed
                    })
            
            elif group_by == 'week':
                # Group by week (each item is a week)
                # Use django's TruncWeek to group by week
                weekly_completed = member_tasks.filter(
                    status__in=['completed', 'approved'],
                    completed_at__isnull=False
                ).annotate(
                    week=TruncWeek('completed_at')
                ).values('week').annotate(
                    count=Count('id')
                ).order_by('week')
                
                for week_data in weekly_completed:
                    week_start = week_data['week']
                    if week_start and start_date <= week_start.date() <= end_date:
                        week_end = week_start + timezone.timedelta(days=6)
                        grouped_data.append({
                            'week_start': week_start.date(),
                            'week_end': week_end.date(),
                            'completed_tasks': week_data['count']
                        })
            
            elif group_by == 'month':
                # Group by month
                monthly_completed = member_tasks.filter(
                    status__in=['completed', 'approved'],
                    completed_at__isnull=False
                ).annotate(
                    month=TruncMonth('completed_at')
                ).values('month').annotate(
                    count=Count('id')
                ).order_by('month')
                
                for month_data in monthly_completed:
                    month_date = month_data['month']
                    if month_date and start_date <= month_date.date() <= end_date:
                        grouped_data.append({
                            'month': month_date.date(),
                            'completed_tasks': month_data['count']
                        })
            
            elif group_by == 'project':
                # Group by project
                for task in member_tasks:
                    if task.project:
                        # Find or create project entry
                        project_entry = next(
                            (item for item in grouped_data if item['project_id'] == task.project.id),
                            None
                        )
                        
                        if not project_entry:
                            project_entry = {
                                'project_id': task.project.id,
                                'project_name': task.project.name,
                                'total_tasks': 0,
                                'completed_tasks': 0
                            }
                            grouped_data.append(project_entry)
                        
                        # Update counts
                        project_entry['total_tasks'] += 1
                        if task.status in ['completed', 'approved']:
                            project_entry['completed_tasks'] += 1
            
            # Add team member productivity data
            team_productivity.append({
                'team_member': {
                    'id': member.id,
                    'name': member.name,
                    'email': member.email,
                    'title': member.title
                },
                'metrics': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                    'on_time_completion_rate': on_time_rate,
                },
                'trend_data': grouped_data
            })
        
        # Return the report data
        return Response({
            'report_type': 'team_productivity',
            'generated_at': timezone.now(),
            'parameters': serializer.validated_data,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'team_productivity': team_productivity
        })


class TaskCompletionReportView(APIView):
    """API View for generating task completion reports"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, config=None):
        """Generate a task completion report"""
        # Use passed configuration or request data
        data = config if config else request.data
        
        # Validate parameters
        serializer = TaskCompletionReportSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's organization
        user = request.user
        if hasattr(user, 'organization') and user.organization:
            organization = user.organization
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        else:
            return Response({"error": "No organization found for user"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Base query for tasks
        tasks = Task.objects.filter(organization=organization)
        
        # Apply filters
        if 'project_id' in serializer.validated_data:
            tasks = tasks.filter(project_id=serializer.validated_data['project_id'])
        
        if 'team_member_id' in serializer.validated_data:
            tasks = tasks.filter(assigned_to_id=serializer.validated_data['team_member_id'])
        
        # Define date range
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        
        # Apply date filters
        if start_date:
            tasks = tasks.filter(created_at__date__gte=start_date)
        
        if end_date:
            tasks = tasks.filter(created_at__date__lte=end_date)
        
        # Get total tasks count
        total_tasks = tasks.count()
        
        # Get counts by status
        task_status_counts = {
            'completed': tasks.filter(status='completed').count(),
            'approved': tasks.filter(status='approved').count(),
            'rejected': tasks.filter(status='rejected').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'pending': tasks.filter(status='pending').count()
        }
        
        # Calculate completion metrics
        completion_rate = ((task_status_counts['completed'] + task_status_counts['approved']) / total_tasks * 100) if total_tasks > 0 else 0
        
        # Group data based on group_by parameter
        group_by = serializer.validated_data.get('group_by', 'week')
        grouped_data = []
        
        if group_by == 'day':
            # Group completed tasks by day
            if start_date and end_date:
                daily_completions = tasks.filter(
                    status__in=['completed', 'approved'],
                    completed_at__isnull=False
                ).annotate(
                    day=TruncDay('completed_at')
                ).values('day').annotate(
                    count=Count('id')
                ).order_by('day')
                
                # Create a dictionary to look up completions by day
                completion_by_day = {item['day'].date(): item['count'] for item in daily_completions}
                
                # Generate entries for each day in the range
                for day in range((end_date - start_date).days + 1):
                    current_date = start_date + timezone.timedelta(days=day)
                    grouped_data.append({
                        'date': current_date,
                        'completed_tasks': completion_by_day.get(current_date, 0)
                    })
        
        elif group_by == 'week':
            # Group completed tasks by week
            weekly_completions = tasks.filter(
                status__in=['completed', 'approved'],
                completed_at__isnull=False
            ).annotate(
                week=TruncWeek('completed_at')
            ).values('week').annotate(
                count=Count('id')
            ).order_by('week')
            
            for week_data in weekly_completions:
                week_start = week_data['week']
                if week_start:
                    week_end = week_start + timezone.timedelta(days=6)
                    grouped_data.append({
                        'week_start': week_start.date(),
                        'week_end': week_end.date(),
                        'completed_tasks': week_data['count']
                    })
        
        elif group_by == 'month':
            # Group completed tasks by month
            monthly_completions = tasks.filter(
                status__in=['completed', 'approved'],
                completed_at__isnull=False
            ).annotate(
                month=TruncMonth('completed_at')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
            
            for month_data in monthly_completions:
                month_date = month_data['month']
                if month_date:
                    grouped_data.append({
                        'month': month_date.date(),
                        'month_name': month_date.strftime('%B %Y'),
                        'completed_tasks': month_data['count']
                    })
        
        elif group_by == 'project':
            # Group by project
            project_completions = tasks.values(
                'project__id', 'project__name'
            ).annotate(
                total=Count('id'),
                completed=Count(Case(
                    When(status__in=['completed', 'approved'], then=1),
                    output_field=IntegerField()
                ))
            ).order_by('project__name')
            
            for project_data in project_completions:
                if project_data['project__id'] is not None:
                    completion_rate = (project_data['completed'] / project_data['total'] * 100) if project_data['total'] > 0 else 0
                    grouped_data.append({
                        'project_id': project_data['project__id'],
                        'project_name': project_data['project__name'],
                        'total_tasks': project_data['total'],
                        'completed_tasks': project_data['completed'],
                        'completion_rate': completion_rate
                    })
        
        elif group_by == 'category':
            # Group by task category
            category_completions = tasks.values('category').annotate(
                total=Count('id'),
                completed=Count(Case(
                    When(status__in=['completed', 'approved'], then=1),
                    output_field=IntegerField()
                ))
            ).order_by('category')
            
            for category_data in category_completions:
                completion_rate = (category_data['completed'] / category_data['total'] * 100) if category_data['total'] > 0 else 0
                grouped_data.append({
                    'category': category_data['category'],
                    'total_tasks': category_data['total'],
                    'completed_tasks': category_data['completed'],
                    'completion_rate': completion_rate
                })
        
        elif group_by == 'priority':
            # Group by task priority
            priority_completions = tasks.values('priority').annotate(
                total=Count('id'),
                completed=Count(Case(
                    When(status__in=['completed', 'approved'], then=1),
                    output_field=IntegerField()
                ))
            ).order_by('priority')
            
            for priority_data in priority_completions:
                completion_rate = (priority_data['completed'] / priority_data['total'] * 100) if priority_data['total'] > 0 else 0
                grouped_data.append({
                    'priority': priority_data['priority'],
                    'total_tasks': priority_data['total'],
                    'completed_tasks': priority_data['completed'],
                    'completion_rate': completion_rate
                })
        
        # Return the report data
        return Response({
            'report_type': 'task_completion',
            'generated_at': timezone.now(),
            'parameters': serializer.validated_data,
            'summary': {
                'total_tasks': total_tasks,
                'status_counts': task_status_counts,
                'completion_rate': completion_rate
            },
            'grouped_data': grouped_data
        })


class TimeTrackingReportView(APIView):
    """API View for generating time tracking reports"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, config=None):
        """Generate a time tracking report"""
        # Use passed configuration or request data
        data = config if config else request.data
        
        # Validate parameters
        serializer = TimeTrackingReportSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's organization
        user = request.user
        if hasattr(user, 'organization') and user.organization:
            organization = user.organization
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        else:
            return Response({"error": "No organization found for user"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Base query for tasks with time tracking enabled
        tasks = Task.objects.filter(
            organization=organization,
            time_tracking_enabled=True
        )
        
        # Apply filters
        if 'project_id' in serializer.validated_data:
            tasks = tasks.filter(project_id=serializer.validated_data['project_id'])
        
        if 'team_member_id' in serializer.validated_data:
            tasks = tasks.filter(assigned_to_id=serializer.validated_data['team_member_id'])
        
        if serializer.validated_data.get('billable_only', False):
            tasks = tasks.filter(is_billable=True)
        
        # Define date range
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        
        # Apply date filters
        if start_date:
            tasks = tasks.filter(created_at__date__gte=start_date)
        
        if end_date:
            tasks = tasks.filter(created_at__date__lte=end_date)
        
        # Get total time statistics
        total_budget_hours = tasks.aggregate(total=Coalesce(Sum('budget_hours'), 0))['total']
        
        # For actual time spent, we need to implement a TaskTimeEntry model
        # Since this model doesn't exist yet in your system, I'll add a placeholder
        # calculation based on the estimated_hours and completion status
        
        # Placeholder for actual time spent
        # In a real implementation, you would sum time entries from a TaskTimeEntry model
        estimated_time_spent = tasks.filter(status__in=['completed', 'approved']).aggregate(
            total=Coalesce(Sum('estimated_hours'), 0)
        )['total']
        
        # Calculate over/under budget status
        budget_variance = total_budget_hours - estimated_time_spent
        budget_variance_percentage = (budget_variance / total_budget_hours * 100) if total_budget_hours > 0 else 0
        
        # Group data based on group_by parameter
        group_by = serializer.validated_data.get('group_by', 'project')
        grouped_data = []
        
        if group_by == 'project':
            # Group by project
            project_time = tasks.values(
                'project__id', 'project__name'
            ).annotate(
                budget_hours=Coalesce(Sum('budget_hours'), 0),
                estimated_hours=Coalesce(Sum('estimated_hours'), 0),
                billable_count=Count(Case(When(is_billable=True, then=1), output_field=IntegerField())),
                task_count=Count('id')
            ).order_by('project__name')
            
            for project_data in project_time:
                if project_data['project__id'] is not None:
                    # Calculate budget variance
                    variance = project_data['budget_hours'] - project_data['estimated_hours']
                    variance_percentage = (variance / project_data['budget_hours'] * 100) if project_data['budget_hours'] > 0 else 0
                    
                    grouped_data.append({
                        'project_id': project_data['project__id'],
                        'project_name': project_data['project__name'],
                        'budget_hours': project_data['budget_hours'],
                        'time_spent': project_data['estimated_hours'],  # Placeholder
                        'variance': variance,
                        'variance_percentage': variance_percentage,
                        'billable_tasks': project_data['billable_count'],
                        'total_tasks': project_data['task_count']
                    })
        
        elif group_by == 'team_member':
            # Group by team member
            member_time = tasks.values(
                'assigned_to__id', 'assigned_to__name', 'assigned_to__email'
            ).annotate(
                budget_hours=Coalesce(Sum('budget_hours'), 0),
                estimated_hours=Coalesce(Sum('estimated_hours'), 0),
                billable_count=Count(Case(When(is_billable=True, then=1), output_field=IntegerField())),
                task_count=Count('id')
            ).order_by('assigned_to__name')
            
            for member_data in member_time:
                if member_data['assigned_to__id'] is not None:
                    # Calculate budget variance
                    variance = member_data['budget_hours'] - member_data['estimated_hours']
                    variance_percentage = (variance / member_data['budget_hours'] * 100) if member_data['budget_hours'] > 0 else 0
                    
                    grouped_data.append({
                        'team_member_id': member_data['assigned_to__id'],
                        'name': member_data['assigned_to__name'],
                        'email': member_data['assigned_to__email'],
                        'budget_hours': member_data['budget_hours'],
                        'time_spent': member_data['estimated_hours'],  # Placeholder
                        'variance': variance,
                        'variance_percentage': variance_percentage,
                        'billable_tasks': member_data['billable_count'],
                        'total_tasks': member_data['task_count']
                    })
        
        elif group_by in ['day', 'week', 'month']:
            # Note: For accurate time tracking by date, you would need a TaskTimeEntry model
            # This is just a placeholder implementation
            if group_by == 'day':
                # Group by day
                if start_date and end_date:
                    for day in range((end_date - start_date).days + 1):
                        current_date = start_date + timezone.timedelta(days=day)
                        day_tasks = tasks.filter(created_at__date=current_date)
                        
                        grouped_data.append({
                            'date': current_date,
                            'budget_hours': day_tasks.aggregate(total=Coalesce(Sum('budget_hours'), 0))['total'],
                            'time_spent': day_tasks.aggregate(total=Coalesce(Sum('estimated_hours'), 0))['total'],
                            'task_count': day_tasks.count()
                        })
            
            elif group_by == 'week':
                # Group by week
                weekly_time = tasks.annotate(
                    week=TruncWeek('created_at')
                ).values('week').annotate(
                    budget_hours=Coalesce(Sum('budget_hours'), 0),
                    time_spent=Coalesce(Sum('estimated_hours'), 0),
                    task_count=Count('id')
                ).order_by('week')
                
                for week_data in weekly_time:
                    if week_data['week']:
                        week_start = week_data['week'].date()
                        week_end = week_start + timezone.timedelta(days=6)
                        
                        grouped_data.append({
                            'week_start': week_start,
                            'week_end': week_end,
                            'budget_hours': week_data['budget_hours'],
                            'time_spent': week_data['time_spent'],
                            'task_count': week_data['task_count']
                        })
            
            elif group_by == 'month':
                # Group by month
                monthly_time = tasks.annotate(
                    month=TruncMonth('created_at')
                ).values('month').annotate(
                    budget_hours=Coalesce(Sum('budget_hours'), 0),
                    time_spent=Coalesce(Sum('estimated_hours'), 0),
                    task_count=Count('id')
                ).order_by('month')
                
                for month_data in monthly_time:
                    if month_data['month']:
                        grouped_data.append({
                            'month': month_data['month'].date(),
                            'month_name': month_data['month'].strftime('%B %Y'),
                            'budget_hours': month_data['budget_hours'],
                            'time_spent': month_data['time_spent'],
                            'task_count': month_data['task_count']
                        })
        
        # Return the report data
        return Response({
            'report_type': 'time_tracking',
            'generated_at': timezone.now(),
            'parameters': serializer.validated_data,
            'summary': {
                'total_budget_hours': total_budget_hours,
                'total_time_spent': estimated_time_spent,  # Placeholder
                'budget_variance': budget_variance,
                'budget_variance_percentage': budget_variance_percentage,
                'billable_tasks': tasks.filter(is_billable=True).count(),
                'total_tasks': tasks.count()
            },
            'grouped_data': grouped_data
        })


class OverdueTasksReportView(APIView):
    """API View for generating overdue tasks reports"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, config=None):
        """Generate an overdue tasks report"""
        # Use passed configuration or request data
        data = config if config else request.data
        
        # Validate parameters
        serializer = OverdueTasksReportSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's organization
        user = request.user
        if hasattr(user, 'organization') and user.organization:
            organization = user.organization
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        else:
            return Response({"error": "No organization found for user"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Current date
        today = timezone.now().date()
        
        # Base query for overdue tasks
        overdue_tasks = Task.objects.filter(
            organization=organization,
            due_date__lt=today,
            status__in=['pending', 'in_progress']  # Tasks not completed/approved
        )
        
        # Apply filters
        if 'project_id' in serializer.validated_data:
            overdue_tasks = overdue_tasks.filter(project_id=serializer.validated_data['project_id'])
        
        if 'team_member_id' in serializer.validated_data:
            overdue_tasks = overdue_tasks.filter(assigned_to_id=serializer.validated_data['team_member_id'])
        
        if 'days_overdue' in serializer.validated_data:
            days_overdue = serializer.validated_data['days_overdue']
            cutoff_date = today - timezone.timedelta(days=days_overdue)
            overdue_tasks = overdue_tasks.filter(due_date__lte=cutoff_date)
        
        # Add days overdue calculation
        overdue_tasks = overdue_tasks.annotate(
            days_overdue=Cast(today - F('due_date'), output_field=IntegerField())
        )
        
        # Calculate severity based on days overdue
        # Severity: 1=Mild (1-3 days), 2=Moderate (4-7 days), 3=Severe (8-14 days), 4=Critical (15+ days)
        overdue_tasks = overdue_tasks.annotate(
            severity=Case(
                When(days_overdue__lte=3, then=Value(1)),
                When(days_overdue__lte=7, then=Value(2)),
                When(days_overdue__lte=14, then=Value(3)),
                default=Value(4),
                output_field=IntegerField()
            )
        )
        
        # Total overdue tasks
        total_overdue = overdue_tasks.count()
        
        # Group data based on group_by parameter
        group_by = serializer.validated_data.get('group_by', 'project')
        grouped_data = []
        
        if group_by == 'project':
            # Group by project
            project_overdue = overdue_tasks.values(
                'project__id', 'project__name'
            ).annotate(
                task_count=Count('id'),
                avg_days_overdue=Avg('days_overdue'),
                critical_count=Count(Case(When(severity=4, then=1), output_field=IntegerField())),
                severe_count=Count(Case(When(severity=3, then=1), output_field=IntegerField())),
                moderate_count=Count(Case(When(severity=2, then=1), output_field=IntegerField())),
                mild_count=Count(Case(When(severity=1, then=1), output_field=IntegerField()))
            ).order_by('-task_count')
            
            for project_data in project_overdue:
                if project_data['project__id'] is not None:
                    grouped_data.append({
                        'project_id': project_data['project__id'],
                        'project_name': project_data['project__name'],
                        'overdue_tasks': project_data['task_count'],
                        'avg_days_overdue': project_data['avg_days_overdue'],
                        'critical_count': project_data['critical_count'],
                        'severe_count': project_data['severe_count'],
                        'moderate_count': project_data['moderate_count'],
                        'mild_count': project_data['mild_count']
                    })
        
        elif group_by == 'team_member':
            # Group by team member
            member_overdue = overdue_tasks.values(
                'assigned_to__id', 'assigned_to__name', 'assigned_to__email'
            ).annotate(
                task_count=Count('id'),
                avg_days_overdue=Avg('days_overdue'),
                critical_count=Count(Case(When(severity=4, then=1), output_field=IntegerField())),
                severe_count=Count(Case(When(severity=3, then=1), output_field=IntegerField())),
                moderate_count=Count(Case(When(severity=2, then=1), output_field=IntegerField())),
                mild_count=Count(Case(When(severity=1, then=1), output_field=IntegerField()))
            ).order_by('-task_count')
            
            for member_data in member_overdue:
                if member_data['assigned_to__id'] is not None:
                    grouped_data.append({
                        'team_member_id': member_data['assigned_to__id'],
                        'name': member_data['assigned_to__name'],
                        'email': member_data['assigned_to__email'],
                        'overdue_tasks': member_data['task_count'],
                        'avg_days_overdue': member_data['avg_days_overdue'],
                        'critical_count': member_data['critical_count'],
                        'severe_count': member_data['severe_count'],
                        'moderate_count': member_data['moderate_count'],
                        'mild_count': member_data['mild_count']
                    })
        
        elif group_by == 'priority':
            # Group by priority
            priority_overdue = overdue_tasks.values(
                'priority'
            ).annotate(
                task_count=Count('id'),
                avg_days_overdue=Avg('days_overdue'),
                critical_count=Count(Case(When(severity=4, then=1), output_field=IntegerField())),
                severe_count=Count(Case(When(severity=3, then=1), output_field=IntegerField())),
                moderate_count=Count(Case(When(severity=2, then=1), output_field=IntegerField())),
                mild_count=Count(Case(When(severity=1, then=1), output_field=IntegerField()))
            ).order_by('-task_count')
            
            for priority_data in priority_overdue:
                grouped_data.append({
                    'priority': priority_data['priority'],
                    'overdue_tasks': priority_data['task_count'],
                    'avg_days_overdue': priority_data['avg_days_overdue'],
                    'critical_count': priority_data['critical_count'],
                    'severe_count': priority_data['severe_count'],
                    'moderate_count': priority_data['moderate_count'],
                    'mild_count': priority_data['mild_count']
                })
        
        elif group_by == 'category':
            # Group by category
            category_overdue = overdue_tasks.values(
                'category'
            ).annotate(
                task_count=Count('id'),
                avg_days_overdue=Avg('days_overdue'),
                critical_count=Count(Case(When(severity=4, then=1), output_field=IntegerField())),
                severe_count=Count(Case(When(severity=3, then=1), output_field=IntegerField())),
                moderate_count=Count(Case(When(severity=2, then=1), output_field=IntegerField())),
                mild_count=Count(Case(When(severity=1, then=1), output_field=IntegerField()))
            ).order_by('-task_count')
            
            for category_data in category_overdue:
                grouped_data.append({
                    'category': category_data['category'],
                    'overdue_tasks': category_data['task_count'],
                    'avg_days_overdue': category_data['avg_days_overdue'],
                    'critical_count': category_data['critical_count'],
                    'severe_count': category_data['severe_count'],
                    'moderate_count': category_data['moderate_count'],
                    'mild_count': category_data['mild_count']
                })
        
        # Get most overdue tasks
        most_overdue = overdue_tasks.order_by('-days_overdue')[:10].values(
            'id', 'title', 'due_date', 'days_overdue', 'priority', 
            'assigned_to__name', 'project__name'
        )
        
        # Return the report data
        return Response({
            'report_type': 'overdue_tasks',
            'generated_at': timezone.now(),
            'parameters': serializer.validated_data,
            'summary': {
                'total_overdue': total_overdue,
                'critical_count': overdue_tasks.filter(severity=4).count(),
                'severe_count': overdue_tasks.filter(severity=3).count(),
                'moderate_count': overdue_tasks.filter(severity=2).count(),
                'mild_count': overdue_tasks.filter(severity=1).count(),
                'avg_days_overdue': overdue_tasks.aggregate(avg=Avg('days_overdue'))['avg']
            },
            'grouped_data': grouped_data,
            'most_overdue': list(most_overdue)
        })