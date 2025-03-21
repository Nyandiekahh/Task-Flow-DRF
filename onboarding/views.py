# onboarding/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OnboardingDataSerializer, CompleteOnboardingSerializer


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