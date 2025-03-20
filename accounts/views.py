# accounts/views.py

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

User = get_user_model()


class RegisterView(APIView):
    """View for registering a new user"""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens for the new user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'User registered successfully',
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    """View for retrieving and updating user profile"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """Get the logged in user's profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """Request a password reset email"""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # We don't want to reveal that the user doesn't exist
                return Response({
                    'message': 'Password reset link has been sent if the email exists.'
                }, status=status.HTTP_200_OK)
            
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Generate reset link (this would be a frontend URL)
            reset_url = f"http://localhost:3000/reset-password-confirm/{uid}/{token}/"
            
            # Send email with reset link
            subject = "Password Reset for TaskFlow"
            message = f"""
            Hello {user.name},
            
            You've requested a password reset for your TaskFlow account.
            Please click the following link to reset your password:
            
            {reset_url}
            
            If you didn't request this, you can safely ignore this email.
            
            Best regards,
            The TaskFlow Team
            """
            
            # In a real application, you would actually send this email
            # For development, we'll just print the reset URL
            print(f"Password reset link for {email}: {reset_url}")
            
            # Uncomment to actually send emails in production
            # send_mail(
            #     subject,
            #     message,
            #     settings.DEFAULT_FROM_EMAIL,
            #     [email],
            #     fail_silently=False,
            # )
            
            return Response({
                'message': 'Password reset link has been sent if the email exists.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Confirm a password reset using a token"""
    permission_classes = (permissions.AllowAny,)

    def post(self, request, uidb64, token):
        try:
            # Decode the user ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            # Verify the token
            if not default_token_generator.check_token(user, token):
                return Response({
                    'message': 'Invalid or expired token'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process password reset
            serializer = PasswordResetConfirmSerializer(data=request.data)
            if serializer.is_valid():
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response({
                    'message': 'Password has been reset successfully'
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'message': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)