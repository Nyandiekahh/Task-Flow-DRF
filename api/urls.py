from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import views
from organizations.views import OrganizationViewSet, TeamMemberViewSet, TitleViewSet
from roles.views import RoleViewSet, PermissionViewSet
from onboarding.views import OnboardingDataView, CompleteOnboardingView
from tasks.views import TaskViewSet, CommentViewSet, TaskAttachmentViewSet, TaskHistoryViewSet
from projects.views import ProjectViewSet
from reports.views import ReportConfigurationViewSet  # Add this import

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint to verify API is working"""
    return Response({
        'message': 'Welcome to the TaskFlow API',
        'version': '1.0.0',
        'status': 'API is operational'
    })

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'team-members', TeamMemberViewSet, basename='team-member')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'titles', TitleViewSet, basename='titles')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'attachments', TaskAttachmentViewSet, basename='attachment')
router.register(r'history', TaskHistoryViewSet, basename='history')
router.register(r'report-configurations', ReportConfigurationViewSet, basename='report-config')  # Add this line

urlpatterns = [
    # API root
    path('', api_root, name='api-root'),
    
    # Include router URLs
    path('', include(router.urls)),
    
    # Authentication URLs
    path('auth/', include('accounts.urls')),
    
    # Onboarding URLs
    path('onboarding/data/', OnboardingDataView.as_view(), name='onboarding-data'),
    path('onboarding/complete/', CompleteOnboardingView.as_view(), name='complete-onboarding'),
    
    # Reports URLs
    path('reports/', include('reports.urls')),  # Add this line
]