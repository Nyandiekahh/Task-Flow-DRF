# onboarding/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    OnboardingDataSerializer, 
    CompleteOnboardingSerializer,
    OrganizationSetupSerializer
)
from organizations.serializers import OrganizationSerializer


class OnboardingDataView(APIView):
    """View for retrieving and updating onboarding data"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get the onboarding data for the authenticated user"""
        serializer = OnboardingDataSerializer(request.user)
        return Response(serializer.data)


class CompleteOnboardingView(APIView):
    """View for marking onboarding as complete"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Mark the user's onboarding as complete"""
        serializer = CompleteOnboardingSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Onboarding completed successfully'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationSetupView(APIView):
    """View for setting up an organization during admin onboarding"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Setup a new organization for an admin user"""
        user = request.user
        
        # Make sure user is an admin
        if user.title != "Admin":
            return Response({
                'error': 'Only admin users can set up organizations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle case where user already has an organization
        if user.organization:
            return Response({
                'error': 'User already has an organization',
                'organization': OrganizationSerializer(user.organization).data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and process the organization data
        serializer = OrganizationSetupSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            organization = serializer.save()
            
            return Response({
                'message': 'Organization setup completed successfully',
                'organization': OrganizationSerializer(organization).data
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingStatusView(APIView):
    """View to check a user's onboarding status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get the user's onboarding status"""
        user = request.user
        
        # Check if user is an admin and needs organization setup
        needs_organization_setup = (
            user.title == "Admin" and 
            not user.organization and 
            user.organization_name
        )
        
        # Get organization data if exists
        organization_data = None
        if user.organization:
            organization_data = OrganizationSerializer(user.organization).data
        
        return Response({
            'needs_organization_setup': needs_organization_setup,
            'onboarding_complete': user.onboarding_completed,
            'organization': organization_data,
        })