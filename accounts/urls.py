# accounts/urls.py

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegisterView,
    UserView,
    PasswordResetRequestView,
    PasswordResetConfirmView
)

urlpatterns = [
    # JWT token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User registration and profile
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserView.as_view(), name='user-profile'),
    
    # Password reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', 
         PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]