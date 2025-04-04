# organizations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, TeamMemberViewSet, TitleViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'', OrganizationViewSet, basename='organization')
router.register(r'team-members', TeamMemberViewSet, basename='team-member')
router.register(r'titles', TitleViewSet, basename='title')

# The API URLs are now determined automatically by the router
urlpatterns = router.urls