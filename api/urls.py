# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import views
from organizations.views import OrganizationViewSet, TeamMemberViewSet
from roles.views import RoleViewSet, PermissionViewSet
from onboarding.views import OnboardingDataView, CompleteOnboardingView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from organizations.views import TitleViewSet

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
]