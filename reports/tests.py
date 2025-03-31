import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

# Import additional required models if needed
# from accounts.models import CustomUser

from organizations.models import Organization, TeamMember
from projects.models import Project
from tasks.models import Task, TaskHistory
from .models import ReportConfiguration

User = get_user_model()

class ReportConfigurationTests(APITestCase):
    """Tests for the report configuration endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        
        # Create an organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            owner=self.user
        )
        
        # Associate user with organization
        self.user.organization = self.organization
        self.user.save()
        
        # Create a test report configuration
        self.report_config = ReportConfiguration.objects.create(
            name='Test Report',
            report_type='project_status',
            organization=self.organization,
            created_by=self.user,
            configuration={
                'project_id': None,
                'start_date': '2023-01-01',
                'end_date': '2023-12-31'
            }
        )
        
        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Define endpoints
        self.list_url = reverse('report-config-list')
        self.detail_url = reverse('report-config-detail', args=[self.report_config.id])
        self.generate_url = reverse('report-config-generate', args=[self.report_config.id])
    
    def test_list_report_configurations(self):
        """Test retrieving list of report configurations"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Report')
    
    def test_create_report_configuration(self):
        """Test creating a new report configuration"""
        data = {
            'name': 'New Report',
            'report_type': 'team_productivity',
            'organization': self.organization.id,
            'configuration': {
                'team_member_id': None,
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'group_by': 'week'
            },
            'is_favorite': True
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Report')
        self.assertEqual(response.data['report_type'], 'team_productivity')
        self.assertEqual(response.data['created_by'], self.user.id)
    
    def test_update_report_configuration(self):
        """Test updating an existing report configuration"""
        data = {
            'name': 'Updated Report',
            'report_type': 'project_status',
            'organization': self.organization.id,
            'configuration': {
                'project_id': None,
                'start_date': '2023-02-01',
                'end_date': '2023-11-30'
            },
            'is_favorite': True
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Report')
        self.assertEqual(response.data['is_favorite'], True)
    
    def test_delete_report_configuration(self):
        """Test deleting a report configuration"""
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ReportConfiguration.objects.count(), 0)
    
    def test_generate_report(self):
        """Test generating a report from a configuration"""
        # Create test data needed for report generation
        project = Project.objects.create(
            name='Test Project',
            organization=self.organization,
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date() + timedelta(days=30),
            status='in_progress'
        )
        
        # Create a task for the project
        Task.objects.create(
            title='Test Task',
            status='in_progress',
            organization=self.organization,
            project=project,
            created_by=self.user,
            due_date=timezone.now() + timedelta(days=7)
        )
        
        response = self.client.post(self.generate_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['report_type'], 'project_status')
        self.assertIn('projects', response.data)
        
        # Verify the report configuration was updated with last_generated timestamp
        updated_config = ReportConfiguration.objects.get(id=self.report_config.id)
        self.assertIsNotNone(updated_config.last_generated)


class ProjectStatusReportTests(APITestCase):
    """Tests for the project status report endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        
        # Create an organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            owner=self.user
        )
        
        # Associate user with organization
        self.user.organization = self.organization
        self.user.save()
        
        # Create test projects
        self.project1 = Project.objects.create(
            name='Project 1',
            organization=self.organization,
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date() + timedelta(days=30),
            status='in_progress'
        )
        
        self.project2 = Project.objects.create(
            name='Project 2',
            organization=self.organization,
            start_date=timezone.now().date() - timedelta(days=15),
            end_date=timezone.now().date() + timedelta(days=45),
            status='planning'
        )
        
        # Create tasks for the projects
        # Project 1 tasks
        Task.objects.create(
            title='Task 1',
            status='completed',
            organization=self.organization,
            project=self.project1,
            created_by=self.user,
            completed_at=timezone.now() - timedelta(days=5)
        )
        
        Task.objects.create(
            title='Task 2',
            status='in_progress',
            organization=self.organization,
            project=self.project1,
            created_by=self.user
        )
        
        Task.objects.create(
            title='Task 3',
            status='pending',
            organization=self.organization,
            project=self.project1,
            created_by=self.user
        )
        
        # Project 2 tasks
        Task.objects.create(
            title='Task 4',
            status='in_progress',
            organization=self.organization,
            project=self.project2,
            created_by=self.user
        )
        
        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Define endpoint
        self.url = reverse('project-status-report')
    
    def test_project_status_report_all_projects(self):
        """Test generating a project status report for all projects"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=60)).isoformat(),
            'end_date': (timezone.now().date() + timedelta(days=60)).isoformat()
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['report_type'], 'project_status')
        self.assertEqual(len(response.data['projects']), 2)
        
        # Verify project 1 data
        project1_data = next(p for p in response.data['projects'] if p['id'] == self.project1.id)
        self.assertEqual(project1_data['name'], 'Project 1')
        self.assertEqual(project1_data['total_tasks'], 3)
        self.assertEqual(project1_data['completed_tasks'], 1)
        self.assertEqual(project1_data['in_progress_tasks'], 1)
        self.assertEqual(project1_data['pending_tasks'], 1)
    
    def test_project_status_report_specific_project(self):
        """Test generating a project status report for a specific project"""
        data = {
            'project_id': self.project1.id,
            'start_date': (timezone.now().date() - timedelta(days=60)).isoformat(),
            'end_date': (timezone.now().date() + timedelta(days=60)).isoformat()
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['projects']), 1)
        
        # Verify project data
        project_data = response.data['projects'][0]
        self.assertEqual(project_data['id'], self.project1.id)
        self.assertEqual(project_data['total_tasks'], 3)
    
    def test_project_status_report_date_validation(self):
        """Test date validation in project status report"""
        data = {
            'start_date': (timezone.now().date() + timedelta(days=10)).isoformat(),
            'end_date': (timezone.now().date()).isoformat()
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TeamProductivityReportTests(APITestCase):
    """Tests for the team productivity report endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        
        # Create an organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            owner=self.user
        )
        
        # Associate user with organization
        self.user.organization = self.organization
        self.user.save()
        
        # Create team members
        self.team_member1 = TeamMember.objects.create(
            name='Team Member 1',
            email='member1@example.com',
            organization=self.organization,
            user=self.user,
            title='Developer'  # Adding title field which might be required
        )
        
        self.team_member2 = TeamMember.objects.create(
            name='Team Member 2',
            email='member2@example.com',
            organization=self.organization,
            title='Designer'  # Adding title field which might be required
        )
        
        # Create a project
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.organization,
            status='in_progress'
        )
        
        # Add team members to project
        self.project.team_members.add(self.team_member1, self.team_member2)
        
        # Create tasks assigned to team members
        # Team member 1 tasks
        task1 = Task.objects.create(
            title='Task 1',
            status='completed',
            organization=self.organization,
            project=self.project,
            created_by=self.user,
            assigned_to=self.team_member1,
            due_date=timezone.now() - timedelta(days=5),
            completed_at=timezone.now() - timedelta(days=7)  # Completed early
        )
        
        task2 = Task.objects.create(
            title='Task 2',
            status='in_progress',
            organization=self.organization,
            project=self.project,
            created_by=self.user,
            assigned_to=self.team_member1
        )
        
        # Team member 2 tasks
        task3 = Task.objects.create(
            title='Task 3',
            status='completed',
            organization=self.organization,
            project=self.project,
            created_by=self.user,
            assigned_to=self.team_member2,
            due_date=timezone.now() - timedelta(days=10),
            completed_at=timezone.now() - timedelta(days=5)  # Completed late
        )
        
        # Create task history records for completed tasks
        TaskHistory.objects.create(
            task=task1,
            action='completed',
            actor=self.user,
            description='Task completed'
        )
        
        TaskHistory.objects.create(
            task=task3,
            action='completed',
            actor=self.user,
            description='Task completed'
        )
        
        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Define endpoint
        self.url = reverse('team-productivity-report')
    
    def test_team_productivity_report_all_members(self):
        """Test generating a team productivity report for all team members"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'week'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['report_type'], 'team_productivity')
        self.assertEqual(len(response.data['team_productivity']), 2)
        
        # Verify team member 1 data
        member1_data = next(m for m in response.data['team_productivity'] 
                           if m['team_member']['id'] == self.team_member1.id)
        self.assertEqual(member1_data['metrics']['total_tasks'], 2)
        self.assertEqual(member1_data['metrics']['completed_tasks'], 1)
        self.assertEqual(member1_data['metrics']['on_time_completion_rate'], 100.0)
        
        # Verify team member 2 data
        member2_data = next(m for m in response.data['team_productivity']
                           if m['team_member']['id'] == self.team_member2.id)
        self.assertEqual(member2_data['metrics']['total_tasks'], 1)
        self.assertEqual(member2_data['metrics']['completed_tasks'], 1)
        self.assertEqual(member2_data['metrics']['on_time_completion_rate'], 0.0)  # Completed late
    
    def test_team_productivity_report_specific_member(self):
        """Test generating a team productivity report for a specific team member"""
        data = {
            'team_member_id': self.team_member1.id,
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'week'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['team_productivity']), 1)
        
        # Verify team member data
        member_data = response.data['team_productivity'][0]
        self.assertEqual(member_data['team_member']['id'], self.team_member1.id)
        self.assertEqual(member_data['metrics']['total_tasks'], 2)
    
    def test_team_productivity_report_group_by_project(self):
        """Test generating a team productivity report grouped by project"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'project'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify grouping by project in trend data
        for member_data in response.data['team_productivity']:
            # Each member should have trend data for the test project
            trend_data = member_data['trend_data']
            self.assertTrue(len(trend_data) > 0)
            
            # Check for project-specific data
            project_entry = next((item for item in trend_data 
                               if 'project_id' in item and item['project_id'] == self.project.id), None)
            self.assertIsNotNone(project_entry)
            self.assertEqual(project_entry['project_name'], 'Test Project')


class TaskCompletionReportTests(APITestCase):
    """Tests for the task completion report endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        
        # Create an organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            owner=self.user
        )
        
        # Associate user with organization
        self.user.organization = self.organization
        self.user.save()
        
        # Create a team member
        self.team_member = TeamMember.objects.create(
            name='Team Member',
            email='member@example.com',
            organization=self.organization,
            user=self.user,
            title='Project Manager'  # Adding title field which might be required
        )
        
        # Create a project
        self.project = Project.objects.create(
            name='Test Project',
            organization=self.organization,
            status='in_progress'
        )
        
        # Create tasks with different statuses and priorities
        # Completed tasks
        for i in range(3):
            Task.objects.create(
                title=f'Completed Task {i+1}',
                status='completed',
                organization=self.organization,
                project=self.project,
                created_by=self.user,
                assigned_to=self.team_member,
                priority='high',
                category='general',
                completed_at=timezone.now() - timedelta(days=i)
            )
        
        # In progress tasks
        for i in range(2):
            Task.objects.create(
                title=f'In Progress Task {i+1}',
                status='in_progress',
                organization=self.organization,
                project=self.project,
                created_by=self.user,
                assigned_to=self.team_member,
                priority='medium',
                category='planning'
            )
        
        # Pending tasks
        Task.objects.create(
            title='Pending Task',
            status='pending',
            organization=self.organization,
            project=self.project,
            created_by=self.user,
            assigned_to=self.team_member,
            priority='low',
            category='admin'
        )
        
        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Define endpoint
        self.url = reverse('task-completion-report')
    
    def test_task_completion_report_default(self):
        """Test generating a default task completion report"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'week'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['report_type'], 'task_completion')
        
        # Verify summary data
        summary = response.data['summary']
        self.assertEqual(summary['total_tasks'], 6)
        self.assertEqual(summary['status_counts']['completed'], 3)
        self.assertEqual(summary['status_counts']['in_progress'], 2)
        self.assertEqual(summary['status_counts']['pending'], 1)
        self.assertEqual(summary['completion_rate'], 50.0)  # 3 out of 6 tasks completed
    
    def test_task_completion_report_group_by_priority(self):
        """Test generating a task completion report grouped by priority"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'priority'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify grouped data
        grouped_data = response.data['grouped_data']
        self.assertEqual(len(grouped_data), 3)  # Three priority levels used
        
        # Verify high priority data
        high_priority = next(item for item in grouped_data if item['priority'] == 'high')
        self.assertEqual(high_priority['total_tasks'], 3)
        self.assertEqual(high_priority['completed_tasks'], 3)
        self.assertEqual(high_priority['completion_rate'], 100.0)
        
        # Verify medium priority data
        medium_priority = next(item for item in grouped_data if item['priority'] == 'medium')
        self.assertEqual(medium_priority['total_tasks'], 2)
        self.assertEqual(medium_priority['completed_tasks'], 0)
        self.assertEqual(medium_priority['completion_rate'], 0.0)
    
    def test_task_completion_report_group_by_category(self):
        """Test generating a task completion report grouped by category"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'category'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify grouped data
        grouped_data = response.data['grouped_data']
        self.assertEqual(len(grouped_data), 3)  # Three categories used
        
        # Verify general category data
        general_category = next(item for item in grouped_data if item['category'] == 'general')
        self.assertEqual(general_category['total_tasks'], 3)
        self.assertEqual(general_category['completed_tasks'], 3)
        
        # Verify planning category data
        planning_category = next(item for item in grouped_data if item['category'] == 'planning')
        self.assertEqual(planning_category['total_tasks'], 2)
        self.assertEqual(planning_category['completed_tasks'], 0)
    
    def test_task_completion_report_filters(self):
        """Test generating a task completion report with filters"""
        data = {
            'project_id': self.project.id,
            'team_member_id': self.team_member.id,
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'day'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # All tasks should be included since they match the filters
        self.assertEqual(response.data['summary']['total_tasks'], 6)


class TimeTrackingReportTests(APITestCase):
    """Tests for the time tracking report endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword'
        )
        
        # Create an organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            owner=self.user
        )
        
        # Associate user with organization
        self.user.organization = self.organization
        self.user.save()
        
        # Create team members
        self.team_member1 = TeamMember.objects.create(
            name='Team Member 1',
            email='member1@example.com',
            organization=self.organization,
            user=self.user
        )
        
        self.team_member2 = TeamMember.objects.create(
            name='Team Member 2',
            email='member2@example.com',
            organization=self.organization
        )
        
        # Create projects
        self.project1 = Project.objects.create(
            name='Project 1',
            organization=self.organization,
            status='in_progress'
        )
        
        self.project2 = Project.objects.create(
            name='Project 2',
            organization=self.organization,
            status='in_progress'
        )
        
        # Create tasks with time tracking enabled
        # Project 1, Team Member 1
        Task.objects.create(
            title='Task 1',
            status='completed',
            organization=self.organization,
            project=self.project1,
            created_by=self.user,
            assigned_to=self.team_member1,
            time_tracking_enabled=True,
            budget_hours=10,
            estimated_hours=8,
            is_billable=True,
            completed_at=timezone.now() - timedelta(days=5)
        )
        
        Task.objects.create(
            title='Task 2',
            status='in_progress',
            organization=self.organization,
            project=self.project1,
            created_by=self.user,
            assigned_to=self.team_member1,
            time_tracking_enabled=True,
            budget_hours=20,
            estimated_hours=5,
            is_billable=True
        )
        
        # Project 2, Team Member 2
        Task.objects.create(
            title='Task 3',
            status='completed',
            organization=self.organization,
            project=self.project2,
            created_by=self.user,
            assigned_to=self.team_member2,
            time_tracking_enabled=True,
            budget_hours=15,
            estimated_hours=18,
            is_billable=False,
            completed_at=timezone.now() - timedelta(days=3)
        )
        
        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Define endpoint
        self.url = reverse('time-tracking-report')
    
    def test_time_tracking_report_by_project(self):
        """Test generating a time tracking report grouped by project"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'project'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['report_type'], 'time_tracking')
        
        # Verify summary data
        summary = response.data['summary']
        self.assertEqual(summary['total_budget_hours'], 45)  # 10 + 20 + 15
        self.assertEqual(summary['total_time_spent'], 26)  # 8 + 18 (completed tasks only)
        self.assertEqual(summary['billable_tasks'], 2)
        self.assertEqual(summary['total_tasks'], 3)
        
        # Verify grouped data
        grouped_data = response.data['grouped_data']
        self.assertEqual(len(grouped_data), 2)  # Two projects
        
        # Verify Project 1 data
        project1_data = next(item for item in grouped_data if item['project_id'] == self.project1.id)
        self.assertEqual(project1_data['budget_hours'], 30)  # 10 + 20
        self.assertEqual(project1_data['time_spent'], 8)  # Only completed task
        self.assertEqual(project1_data['billable_tasks'], 2)
        self.assertEqual(project1_data['total_tasks'], 2)
        
        # Verify Project 2 data
        project2_data = next(item for item in grouped_data if item['project_id'] == self.project2.id)
        self.assertEqual(project2_data['budget_hours'], 15)
        self.assertEqual(project2_data['time_spent'], 18)
        self.assertEqual(project2_data['billable_tasks'], 0)
        self.assertEqual(project2_data['total_tasks'], 1)
    
    def test_time_tracking_report_by_team_member(self):
        """Test generating a time tracking report grouped by team member"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'team_member'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify grouped data
        grouped_data = response.data['grouped_data']
        self.assertEqual(len(grouped_data), 2)  # Two team members
        
        # Verify Team Member 1 data
        member1_data = next(item for item in grouped_data if item['team_member_id'] == self.team_member1.id)
        self.assertEqual(member1_data['budget_hours'], 30)  # 10 + 20
        self.assertEqual(member1_data['time_spent'], 8)  # Only completed task
        self.assertEqual(member1_data['billable_tasks'], 2)
        
        # Verify Team Member 2 data
        member2_data = next(item for item in grouped_data if item['team_member_id'] == self.team_member2.id)
        self.assertEqual(member2_data['budget_hours'], 15)
        self.assertEqual(member2_data['time_spent'], 18)
        self.assertEqual(member2_data['billable_tasks'], 0)
        self.assertEqual(member2_data['total_tasks'], 1)
    
    def test_time_tracking_report_billable_only(self):
        """Test generating a time tracking report with billable tasks only"""
        data = {
            'start_date': (timezone.now().date() - timedelta(days=30)).isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'group_by': 'project',
            'billable_only': True
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only billable tasks are included
        summary = response.data['summary']
        self.assertEqual(summary['total_tasks'], 2)
        self.assertEqual(summary['billable_tasks'], 2)
        
        # Only Project 1 should be included (since only it has billable tasks)
        grouped_data = response.data['grouped_data']
        self.assertEqual(len(grouped_data), 1)
        self.assertEqual(grouped_data[0]['project_id'], self.project1.id)


class OverdueTasksReportTests(APITestCase):
    """Tests for the overdue tasks report endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create an organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            owner=self.user
        )
        
        # Associate user with organization
        self.user.organization = self.organization
        self.user.save()
        
        # Create team members
        self.team_member1 = TeamMember.objects.create(
            name='Team Member 1',
            email='member1@example.com',
            organization=self.organization,
            user=self.user
        )
        
        self.team_member2 = TeamMember.objects.create(
            name='Team Member 2',
            email='member2@example.com',
            organization=self.organization
        )
        
        # Create projects
        self.project1 = Project.objects.create(
            name='Project 1',
            organization=self.organization,
            status='in_progress'
        )
        
        self.project2 = Project.objects.create(
            name='Project 2',
            organization=self.organization,
            status='in_progress'
        )
        
        # Create current date for reference
        self.today = timezone.now().date()
        
        # Create overdue tasks with different severities
        # Mild (1-3 days overdue)
        Task.objects.create(
            title='Mild Overdue Task 1',
            status='in_progress',
            organization=self.organization,
            project=self.project1,
            created_by=self.user,
            assigned_to=self.team_member1,
            due_date=self.today - timedelta(days=2),
            priority='medium',
            category='general'
        )
        
        Task.objects.create(
            title='Mild Overdue Task 2',
            status='pending',
            organization=self.organization,
            project=self.project1,
            created_by=self.user,
            assigned_to=self.team_member1,
            due_date=self.today - timedelta(days=3),
            priority='low',
            category='admin'
        )
        
        # Moderate (4-7 days overdue)
        Task.objects.create(
            title='Moderate Overdue Task',
            status='in_progress',
            organization=self.organization,
            project=self.project1,
            created_by=self.user,
            assigned_to=self.team_member2,
            due_date=self.today - timedelta(days=5),
            priority='high',
            category='planning'
        )
        
        # Severe (8-14 days overdue)
        Task.objects.create(
            title='Severe Overdue Task',
            status='in_progress',
            organization=self.organization,
            project=self.project2,
            created_by=self.user,
            assigned_to=self.team_member2,
            due_date=self.today - timedelta(days=10),
            priority='urgent',
            category='operations'
        )
        
        # Critical (15+ days overdue)
        Task.objects.create(
            title='Critical Overdue Task',
            status='pending',
            organization=self.organization,
            project=self.project2,
            created_by=self.user,
            assigned_to=self.team_member1,
            due_date=self.today - timedelta(days=20),
            priority='urgent',
            category='research'
        )
        
        # Create non-overdue tasks (should not appear in report)
        Task.objects.create(
            title='Future Task',
            status='pending',
            organization=self.organization,
            project=self.project1,
            created_by=self.user,
            assigned_to=self.team_member1,
            due_date=self.today + timedelta(days=5)
        )
        
        Task.objects.create(
            title='Completed Task',
            status='completed',
            organization=self.organization,
            project=self.project1,
            created_by=self.user,
            assigned_to=self.team_member1,
            due_date=self.today - timedelta(days=5),
            completed_at=self.today - timedelta(days=7)
        )
        
        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Define endpoint
        self.url = reverse('overdue-tasks-report')
    
    def test_overdue_tasks_report_by_project(self):
        """Test generating an overdue tasks report grouped by project"""
        data = {
            'group_by': 'project'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['report_type'], 'overdue_tasks')
        
        # Verify summary data
        summary = response.data['summary']
        self.assertEqual(summary['total_overdue'], 5)
        self.assertEqual(summary['critical_count'], 1)
        self.assertEqual(summary['severe_count'], 1)
        self.assertEqual(summary['moderate_count'], 1)
        self.assertEqual(summary['mild_count'], 2)
        
        # Verify grouped data
        grouped_data = response.data['grouped_data']
        self.assertEqual(len(grouped_data), 2)  # Two projects
        
        # Verify Project 1 data (3 overdue tasks)
        project1_data = next(item for item in grouped_data if item['project_id'] == self.project1.id)
        self.assertEqual(project1_data['overdue_tasks'], 3)
        self.assertEqual(project1_data['critical_count'], 0)
        self.assertEqual(project1_data['severe_count'], 0)
        self.assertEqual(project1_data['moderate_count'], 1)
        self.assertEqual(project1_data['mild_count'], 2)
        
        # Verify Project 2 data (2 overdue tasks)
        project2_data = next(item for item in grouped_data if item['project_id'] == self.project2.id)
        self.assertEqual(project2_data['overdue_tasks'], 2)
        self.assertEqual(project2_data['critical_count'], 1)
        self.assertEqual(project2_data['severe_count'], 1)
    
    def test_overdue_tasks_report_by_team_member(self):
        """Test generating an overdue tasks report grouped by team member"""
        data = {
            'group_by': 'team_member'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify grouped data
        grouped_data = response.data['grouped_data']
        self.assertEqual(len(grouped_data), 2)  # Two team members
        
        # Verify Team Member 1 data (3 overdue tasks)
        member1_data = next(item for item in grouped_data if item['team_member_id'] == self.team_member1.id)
        self.assertEqual(member1_data['overdue_tasks'], 3)
        self.assertEqual(member1_data['critical_count'], 1)
        self.assertEqual(member1_data['mild_count'], 2)
        
        # Verify Team Member 2 data (2 overdue tasks)
        member2_data = next(item for item in grouped_data if item['team_member_id'] == self.team_member2.id)
        self.assertEqual(member2_data['overdue_tasks'], 2)
        self.assertEqual(member2_data['severe_count'], 1)
        self.assertEqual(member2_data['moderate_count'], 1)
    
    def test_overdue_tasks_report_days_overdue_filter(self):
        """Test generating an overdue tasks report with days_overdue filter"""
        data = {
            'days_overdue': 5,  # Tasks at least 5 days overdue
            'group_by': 'project'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only tasks at least 5 days overdue are included
        summary = response.data['summary']
        self.assertEqual(summary['total_overdue'], 3)  # Moderate, Severe, Critical
        self.assertEqual(summary['critical_count'], 1)
        self.assertEqual(summary['severe_count'], 1)
        self.assertEqual(summary['moderate_count'], 1)
        self.assertEqual(summary['mild_count'], 0)  # No mild tasks should be included
    
    def test_overdue_tasks_report_most_overdue(self):
        """Test the most_overdue section of the overdue tasks report"""
        data = {
            'group_by': 'project'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify most_overdue list is included
        most_overdue = response.data['most_overdue']
        self.assertTrue(len(most_overdue) > 0)
        
        # Verify the first task is the most overdue one (20 days)
        self.assertEqual(most_overdue[0]['days_overdue'], 20)
        
        # Verify tasks are ordered by days_overdue (descending)
        for i in range(1, len(most_overdue)):
            self.assertTrue(most_overdue[i-1]['days_overdue'] >= most_overdue[i]['days_overdue'])