from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import Organization, TeamMember, Title
from .serializers import OrganizationSerializer, TeamMemberSerializer, TitleSerializer
from roles.models import Permission
from roles.serializers import PermissionSerializer
from accounts.models import Invitation, CustomUser

class OrganizationViewSet(viewsets.ModelViewSet):
    """Viewset for the Organization model"""
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return organizations for the authenticated user"""
        return Organization.objects.filter(members=self.request.user) | Organization.objects.filter(owner=self.request.user)


class TeamMemberViewSet(viewsets.ModelViewSet):
    """Viewset for the TeamMember model"""
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return team members for the authenticated user's organization"""
        user = self.request.user
        
        # Try to get organization directly
        if hasattr(user, 'organization') and user.organization:
            # Include recently accepted invitations
            recently_accepted_invitations = Invitation.objects.filter(
                organization=user.organization,
                accepted=True,
                date_accepted__gte=timezone.now() - timedelta(days=7)
            )
            
            # Get team members directly
            team_members = TeamMember.objects.filter(organization=user.organization)
            
            # Add any missing members from recently accepted invitations
            for invitation in recently_accepted_invitations:
                TeamMember.objects.get_or_create(
                    organization=invitation.organization,
                    email=invitation.email,
                    defaults={
                        'name': invitation.name,
                        'user': CustomUser.objects.filter(email=invitation.email).first(),
                        'title': invitation.role
                    }
                )
            
            return team_members
        
        # Try to get from owned organizations
        if hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            return TeamMember.objects.filter(organization__in=user.owned_organizations.all())
        
        # Try to get from organizations where user is a member
        user_teams = TeamMember.objects.filter(user=user)
        if user_teams.exists():
            return TeamMember.objects.filter(organization__in=user_teams.values_list('organization', flat=True))
        
        # Try to get organization by name
        if hasattr(user, 'organization_name') and user.organization_name:
            orgs = Organization.objects.filter(name=user.organization_name)
            if orgs.exists():
                return TeamMember.objects.filter(organization__in=orgs)
        
        # If admin user, return all team members
        if user.is_staff:
            return TeamMember.objects.all()
            
        return TeamMember.objects.none()


class TitleViewSet(viewsets.ModelViewSet):
    """Viewset for the Title model"""
    serializer_class = TitleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return titles for the authenticated user's organization"""
        user = self.request.user
        
        # Try to get organization directly
        if hasattr(user, 'organization') and user.organization:
            return Title.objects.filter(organization=user.organization)
        
        # Try to get from owned organizations
        if hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            return Title.objects.filter(organization__in=user.owned_organizations.all())
        
        # Try to get from organizations where user is a member
        user_teams = TeamMember.objects.filter(user=user)
        if user_teams.exists():
            return Title.objects.filter(organization__in=user_teams.values_list('organization', flat=True))
        
        # Try to get organization by name
        if hasattr(user, 'organization_name') and user.organization_name:
            orgs = Organization.objects.filter(name=user.organization_name)
            if orgs.exists():
                return Title.objects.filter(organization__in=orgs)
        
        # If admin user, return all titles
        if user.is_staff:
            return Title.objects.all()
            
        return Title.objects.none()
    
    def perform_create(self, serializer):
        """Create a new title for the user's organization"""
        # Try multiple ways to get the user's organization
        user = self.request.user
        organization = None
        
        if hasattr(user, 'organization') and user.organization:
            organization = user.organization
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        elif hasattr(user, 'organization_name') and user.organization_name:
            orgs = Organization.objects.filter(name=user.organization_name)
            if orgs.exists():
                organization = orgs.first()
        
        if organization:
            serializer.save(organization=organization)
        else:
            raise Exception("Unable to determine user's organization for creating title")
    
    @action(detail=False, methods=['GET'])
    def available_permissions(self, request):
        """Get all available permissions"""
        permissions = Permission.objects.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)