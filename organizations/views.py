# organizations/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Organization, TeamMember, Title
from .serializers import OrganizationSerializer, TeamMemberSerializer, TitleSerializer

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
        if self.request.user.organization:
            return TeamMember.objects.filter(organization=self.request.user.organization)
        return TeamMember.objects.none()
    
# organizations/views.py
class TitleViewSet(viewsets.ModelViewSet):
    """Viewset for the Title model"""
    serializer_class = TitleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return titles for the authenticated user's organization"""
        if self.request.user.organization:
            return Title.objects.filter(organization=self.request.user.organization)
        return Title.objects.none()
    
    def perform_create(self, serializer):
        """Create a new title for the user's organization"""
        serializer.save(organization=self.request.user.organization)