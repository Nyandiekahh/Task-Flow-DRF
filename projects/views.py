# projects/views.py
from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import Project
from .serializers import ProjectSerializer, ProjectListSerializer, ProjectDetailSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action in ['retrieve', 'update', 'partial_update', 'create']:
            return ProjectDetailSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        """
        Return projects for the user's organization.
        For regular team members, only return projects where they are:
        1. Team member of the project
        2. Creator of tasks in the project
        3. Assignee of tasks in the project
        4. Watcher of tasks in the project
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
                    return Project.objects.none()
            except Exception as e:
                print(f"Error getting team membership: {e}")
                # If there's an error, return empty queryset
                return Project.objects.none()
        
        # Base queryset - all projects for this organization
        base_queryset = Project.objects.filter(organization=organization)
        
        # For organization owners, get all projects in the organization
        if is_org_owner:
            return base_queryset
        else:
            # For regular team members, only show projects they're involved with
            team_member = user.team_memberships.first()
            
            # 1. Projects where they are a team member
            projects_as_member = base_queryset.filter(team_members=team_member)
            
            # 2. Projects that have tasks assigned to them
            projects_with_assigned_tasks = base_queryset.filter(
                tasks__assigned_to=team_member
            )
            
            # 3. Projects that have tasks where they are an additional assignee
            projects_with_additional_assignee = base_queryset.filter(
                tasks__assignees_through__team_member=team_member
            )
            
            # 4. Projects that have tasks where they are a watcher
            projects_with_watcher = base_queryset.filter(
                tasks__watchers_through__team_member=team_member
            )
            
            # 5. Projects that have tasks they created
            projects_with_created_tasks = base_queryset.filter(
                tasks__created_by=user
            )
            
            # Combine all querysets and remove duplicates
            return (projects_as_member | 
                    projects_with_assigned_tasks | 
                    projects_with_additional_assignee | 
                    projects_with_watcher | 
                    projects_with_created_tasks).distinct()
    
    def perform_create(self, serializer):
        # Set the organization to the user's organization
        user = self.request.user
        organization = None
        
        if hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        elif hasattr(user, 'team_memberships') and user.team_memberships.exists():
            organization = user.team_memberships.first().organization
        
        if organization:
            serializer.save(organization=organization)
        else:
            raise serializers.ValidationError("User is not associated with any organization")