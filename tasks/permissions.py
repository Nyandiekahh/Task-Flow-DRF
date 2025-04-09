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
            try:
                # Check if user owns this organization
                if request.user.owned_organizations.filter(id=obj.organization.id).exists():
                    return True
                    
                # Check if user is a member of this organization
                return request.user.team_memberships.filter(organization=obj.organization).exists()
            except:
                return False
        elif hasattr(obj, 'task') and hasattr(obj.task, 'organization'):
            # For Comment, TaskAttachment, TaskHistory objects
            try:
                # Check if user owns this organization
                if request.user.owned_organizations.filter(id=obj.task.organization.id).exists():
                    return True
                    
                # Check if user is a member of this organization
                return request.user.team_memberships.filter(organization=obj.task.organization).exists()
            except:
                return False
        
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
        # Check if user is an organization owner first
        user_owned_org = request.user.owned_organizations.first()
        
        # If user is an organization owner, they have all permissions
        if user_owned_org:
            return True
            
        # Otherwise check team memberships for regular users
        try:
            # Get user's team membership
            team_memberships = request.user.team_memberships.all()
            if not team_memberships.exists():
                return False
                
            # Get the organization from the team membership
            organization = team_memberships.first().organization
            
            # Get user's title in the organization
            title = team_memberships.first().title
            
            # Check if title has the required permission
            from roles.models import Role, Permission
            
            # Get roles for this organization
            roles = Role.objects.filter(organization=organization)
            
            # Get permissions for those roles
            permission_codes = []
            for role in roles:
                permissions = role.permissions.all()
                permission_codes.extend([perm.code for perm in permissions])
            
            return self.permission_code in permission_codes
        except Exception as e:
            print(f"Permission check error: {e}")
            return False
    
    def has_object_permission(self, request, view, obj):
        # Inherit from has_permission first
        if not self.has_permission(request, view):
            return False
        
        # Check if user belongs to the object's organization
        if hasattr(obj, 'organization'):
            # For Task objects
            try:
                # Check if user owns this organization
                if request.user.owned_organizations.filter(id=obj.organization.id).exists():
                    return True
                    
                # Check if user is a member of this organization
                return request.user.team_memberships.filter(organization=obj.organization).exists()
            except:
                return False
        elif hasattr(obj, 'task') and hasattr(obj.task, 'organization'):
            # For Comment, TaskAttachment, TaskHistory objects
            try:
                # Check if user owns this organization
                if request.user.owned_organizations.filter(id=obj.task.organization.id).exists():
                    return True
                    
                # Check if user is a member of this organization
                return request.user.team_memberships.filter(organization=obj.task.organization).exists()
            except:
                return False
        
        return False


class CanCreateTasks(HasPermissionCode):
    """Permission class for creating tasks"""
    permission_code = 'create_tasks'


class CanViewTasks(HasPermissionCode):
    """Permission class for viewing tasks"""
    permission_code = 'view_tasks'
    
    def has_permission(self, request, view):
        # For viewing tasks, always allow if authenticated
        # The filter in get_queryset will handle the access control
        return request.user.is_authenticated


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