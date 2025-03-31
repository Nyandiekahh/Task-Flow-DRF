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
from .models import PasswordResetOTP

User = get_user_model()


class RegisterView(APIView):
    """View for registering a new user"""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # If user provided an organization_name, set them as an Admin
            if user.organization_name and not user.title:
                user.title = "Admin"
                user.onboarding_completed = False  # Ensure they go through onboarding
                user.save()
            
            # Generate JWT tokens for the new user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'User registered successfully',
                'needs_onboarding': not user.onboarding_completed
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
    """Request a password reset via OTP"""
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
                    'message': 'Password reset OTP has been sent if the email exists.'
                }, status=status.HTTP_200_OK)
            
            # Generate OTP
            otp_obj = PasswordResetOTP.create_otp_for_user(user)
            
            # Send email with OTP
            subject = "Password Reset OTP for TaskFlow"
            message = f"""
            Hello {user.name or user.email},
            
            You've requested a password reset for your TaskFlow account.
            Please use the following OTP to reset your password:
            
            {otp_obj.otp}
            
            This OTP is valid for 15 minutes.
            
            If you didn't request this, you can safely ignore this email.
            
            Best regards,
            The TaskFlow Team
            """
            
            # Send the email
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'Password reset OTP has been sent if the email exists.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerifyView(APIView):
    """Verify OTP and reset password"""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        # Validate input data
        if not all([email, otp, new_password]):
            return Response({
                'error': 'Email, OTP and new password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Find the latest unused OTP for this user
            otp_obj = PasswordResetOTP.objects.filter(
                user=user, 
                otp=otp, 
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp_obj or not otp_obj.is_valid():
                return Response({
                    'error': 'Invalid or expired OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as used
            otp_obj.is_used = True
            otp_obj.save()
            
            # Reset the password
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password has been reset successfully'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid email'
            }, status=status.HTTP_400_BAD_REQUEST)


# Keep this for backward compatibility
class PasswordResetConfirmView(APIView):
    """Legacy confirm password reset using a token - to be deprecated"""
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