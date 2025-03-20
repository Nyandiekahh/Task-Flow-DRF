# api/urls.py

from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint to verify API is working"""
    return Response({
        'message': 'Welcome to the TaskFlow API',
        'version': '1.0.0',
        'status': 'API is operational'
    })


urlpatterns = [
    # API root for testing
    path('', api_root, name='api-root'),
    
    # Include the accounts URLs for authentication
    path('auth/', include('accounts.urls')),
    
    # Add other API endpoints here as we build them
]