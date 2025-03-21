from rest_framework import permissions


class HasTaskPermission(permissions.BasePermission):
    """Base permission class for task operations.
    
    Ensures user is authenticated and belongs to the task's organization.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user belongs to the object's organization
        if hasattr(obj, 'organization'):
            # For Task objects
            user_organizations = request.user.owned_organizations.all()
            return obj.organization in user_organizations
        elif hasattr(obj, 'task') and hasattr(obj.task, 'organization'):
            # For Comment, TaskAttachment, TaskHistory objects
            user_organizations = request.user.owned_organizations.all()
            return obj.task.organization in user_organizations
        
        return False


class HasPermissionCode(permissions.BasePermission):
    """
    Generic permission class to check if user has a specific permission code
    in their organization's roles.
    """
    
    permission_code = None
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get user's organization
        organization = request.user.owned_organizations.first()
        if not organization:
            return False
        
        # Organization owner has all permissions
        if organization.owner == request.user:
            return True
            
        # Get user's team membership
        try:
            team_member = request.user.team_memberships.get(organization=organization)
        except:
            return False
        
        # Get permission codes for the user's roles
        from organizations.models import Title
        from roles.models import Role, Permission
        
        try:
            # Get user's title in the organization
            title = Title.objects.get(name=team_member.title, organization=organization)
            
            # Get roles for the title
            roles = Role.objects.filter(organization=organization)
            
            # Get permissions for those roles
            permission_codes = []
            for role in roles:
                permissions = role.permissions.all()
                permission_codes.extend([perm.code for perm in permissions])
            
            return self.permission_code in permission_codes
        except:
            return False
    
    def has_object_permission(self, request, view, obj):
        # Inherit from has_permission first
        if not self.has_permission(request, view):
            return False
        
        # Check if user belongs to the object's organization
        if hasattr(obj, 'organization'):
            # For Task objects
            user_organizations = request.user.owned_organizations.all()
            return obj.organization in user_organizations
        elif hasattr(obj, 'task') and hasattr(obj.task, 'organization'):
            # For Comment, TaskAttachment, TaskHistory objects
            user_organizations = request.user.owned_organizations.all()
            return obj.task.organization in user_organizations
        
        return False


class CanCreateTasks(HasPermissionCode):
    """Permission class for creating tasks"""
    permission_code = 'create_tasks'


class CanViewTasks(HasPermissionCode):
    """Permission class for viewing tasks"""
    permission_code = 'view_tasks'


class CanUpdateTasks(HasPermissionCode):
    """Permission class for updating tasks"""
    permission_code = 'update_tasks'


class CanDeleteTasks(HasPermissionCode):
    """Permission class for deleting tasks"""
    permission_code = 'delete_tasks'


class CanAssignTasks(HasPermissionCode):
    """Permission class for assigning tasks"""
    permission_code = 'assign_tasks'


class CanApproveTasks(HasPermissionCode):
    """Permission class for approving tasks"""
    permission_code = 'approve_tasks'


class CanRejectTasks(HasPermissionCode):
    """Permission class for rejecting tasks"""
    permission_code = 'reject_tasks'


class CanComment(HasPermissionCode):
    """Permission class for commenting on tasks"""
    permission_code = 'comment'