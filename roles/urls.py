# roles/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoleViewSet, PermissionViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]