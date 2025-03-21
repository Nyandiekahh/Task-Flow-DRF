# roles/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Role, Permission
from .serializers import RoleSerializer, PermissionSerializer


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for the Permission model (read-only)"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]


class RoleViewSet(viewsets.ModelViewSet):
    """Viewset for the Role model"""
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return roles for the authenticated user's organization"""
        if self.request.user.organization:
            return Role.objects.filter(organization=self.request.user.organization)
        return Role.objects.none()