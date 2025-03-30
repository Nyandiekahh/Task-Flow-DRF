# projects/views.py
from rest_framework import viewsets, permissions
from .models import Project
from .serializers import ProjectSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return projects for the user's organization
        user = self.request.user
        if hasattr(user, 'organization') and user.organization:
            return Project.objects.filter(organization=user.organization)
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            return Project.objects.filter(organization__in=user.owned_organizations.all())
        return Project.objects.none()
    
    def perform_create(self, serializer):
        # Set the organization to the user's organization
        user = self.request.user
        organization = None
        
        if hasattr(user, 'organization') and user.organization:
            organization = user.organization
        elif hasattr(user, 'owned_organizations') and user.owned_organizations.exists():
            organization = user.owned_organizations.first()
        
        if organization:
            serializer.save(organization=organization)
        else:
            raise serializers.ValidationError("User is not associated with any organization")