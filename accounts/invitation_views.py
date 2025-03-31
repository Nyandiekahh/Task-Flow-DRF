# accounts/invitation_views.py

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Invitation
from .serializers import (
    UserSerializer,
    InvitationCreateSerializer,
    InvitationListSerializer,
    BulkInvitationSerializer
)

User = get_user_model()


class InvitationListView(APIView):
    """View for listing pending invitations for an organization"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request):
        """Get all pending invitations for the user's organization"""
        if not request.user.organization:
            return Response({
                'error': 'You must be part of an organization to view invitations'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        invitations = Invitation.objects.filter(
            organization=request.user.organization,
            accepted=False
        )
        
        serializer = InvitationListSerializer(invitations, many=True)
        return Response(serializer.data)


class InvitationCreateView(APIView):
    """View for creating a new invitation"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        """Create a new invitation"""
        # Check if user is part of an organization
        if not request.user.organization:
            return Response({
                'error': 'You must be part of an organization to send invitations'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process bulk invitations
        serializer = BulkInvitationSerializer(data=request.data)
        if serializer.is_valid():
            invitations_data = serializer.validated_data['invitations']
            created_invitations = []
            
            # Process each invitation
            for invitation_data in invitations_data:
                # Set the serializer context with the organization
                invitation_serializer = InvitationCreateSerializer(
                    data=invitation_data,
                    context={
                        'organization': request.user.organization
                    }
                )
                
                if invitation_serializer.is_valid():
                    # Check if we're updating an existing invitation
                    existing_invitation = invitation_serializer.context.get('existing_invitation')
                    
                    if existing_invitation:
                        # Update the existing invitation
                        if invitation_data.get('name'):
                            existing_invitation.name = invitation_data['name']
                        if 'role' in invitation_data and invitation_serializer.fields['role'] != invitation_serializer.fields['role'].__class__(read_only=True):
                            existing_invitation.role = invitation_data.get('role')
                        existing_invitation.invited_by = request.user
                        existing_invitation.email_sent = False  # Reset so we'll send a new email
                        existing_invitation.save()
                        
                        invitation = existing_invitation
                    else:
                        # Create new invitation
                        invitation_kwargs = {
                            'email': invitation_data['email'],
                            'name': invitation_data.get('name', ''),
                            'invited_by': request.user,
                            'organization': request.user.organization,
                        }
                        
                        # Only add role if it's not a read-only field (which means we have a valid queryset)
                        if 'role' in invitation_data and invitation_serializer.fields['role'] != invitation_serializer.fields['role'].__class__(read_only=True):
                            invitation_kwargs['role'] = invitation_data.get('role')
                            
                        invitation = Invitation.objects.create(**invitation_kwargs)
                    
                    created_invitations.append(invitation)
                    
                    # Send invitation email
                    self.send_invitation_email(invitation)
                else:
                    # Return validation errors
                    return Response(
                        invitation_serializer.errors, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Return success response
            return Response({
                'message': f'Successfully sent {len(created_invitations)} invitations',
                'invitations': InvitationListSerializer(created_invitations, many=True).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_invitation_email(self, invitation):
        """Send invitation email to the invitee"""
        
        # Create frontend URL for accepting invitation
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        invitation_link = f"{frontend_url}/accept-invitation/{invitation.token}"
        
        subject = f"You've been invited to join {invitation.organization.name} on TaskFlow"
        
        # Email body
        message = f"""
        Hello {invitation.name or invitation.email},
        
        You've been invited by {invitation.invited_by.name or invitation.invited_by.email} to join {invitation.organization.name} on TaskFlow.
        
        {f"You've been invited to join as {invitation.role.name}." if invitation.role else ""}
        
        Click the following link to accept the invitation:
        {invitation_link}
        
        This invitation link will expire in 7 days.
        
        If you have any questions, please contact {invitation.invited_by.email}.
        
        Best regards,
        The TaskFlow Team
        """
        
        # Send the email
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [invitation.email],
                fail_silently=False,
            )
            
            # Mark email as sent
            invitation.email_sent = True
            invitation.save()
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error sending invitation email: {str(e)}")


class InvitationAcceptView(APIView):
    """View for accepting an invitation"""
    permission_classes = (permissions.AllowAny,)
    
    def get(self, request, token):
        """Check if invitation is valid"""
        try:
            invitation = Invitation.objects.get(token=token, accepted=False)
            
            # Check if invitation is for an existing user
            user_exists = User.objects.filter(email=invitation.email).exists()
            
            return Response({
                'valid': True,
                'invitation': InvitationListSerializer(invitation).data,
                'user_exists': user_exists
            })
        except Invitation.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid or expired invitation'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, token):
        """Accept an invitation"""
        try:
            invitation = Invitation.objects.get(token=token, accepted=False)
            
            # Get or create user
            try:
                # If user exists, they just need to sign in
                user = User.objects.get(email=invitation.email)
                
                # Update user's organization and role
                user.organization = invitation.organization
                if invitation.role:
                    user.title = invitation.role.name
                user.save()
                
            except User.DoesNotExist:
                # Create new user with provided data
                password = request.data.get('password')
                
                if not password:
                    return Response({
                        'error': 'Password is required for new users'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create the user
                user = User.objects.create_user(
                    email=invitation.email,
                    password=password,
                    name=invitation.name or '',
                    organization=invitation.organization
                )
                
                # Set user title from role if available
                if invitation.role:
                    user.title = invitation.role.name
                    user.save()
            
            # Mark invitation as accepted
            invitation.accept(user)
            
            # Return authentication tokens for the user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Invitation accepted successfully',
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
            
        except Invitation.DoesNotExist:
            return Response({
                'error': 'Invalid or expired invitation'
            }, status=status.HTTP_404_NOT_FOUND)


class InvitationResendView(APIView):
    """View for resending an invitation"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request, invitation_id):
        """Resend an invitation email"""
        # Check if user is part of an organization
        if not request.user.organization:
            return Response({
                'error': 'You must be part of an organization to resend invitations'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            invitation = Invitation.objects.get(
                id=invitation_id,
                organization=request.user.organization,
                accepted=False
            )
            
            # Create frontend URL for accepting invitation
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            invitation_link = f"{frontend_url}/accept-invitation/{invitation.token}"
            
            subject = f"You've been invited to join {invitation.organization.name} on TaskFlow"
            
            # Email body
            message = f"""
            Hello {invitation.name or invitation.email},
            
            You've been invited by {invitation.invited_by.name or invitation.invited_by.email} to join {invitation.organization.name} on TaskFlow.
            
            {f"You've been invited to join as {invitation.role.name}." if invitation.role else ""}
            
            Click the following link to accept the invitation:
            {invitation_link}
            
            This invitation link will expire in 7 days.
            
            If you have any questions, please contact {invitation.invited_by.email}.
            
            Best regards,
            The TaskFlow Team
            """
            
            # Send the email
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [invitation.email],
                fail_silently=False,
            )
            
            # Update invitation sent status
            invitation.email_sent = True
            invitation.date_sent = timezone.now()  # Update the sent date
            invitation.save()
            
            return Response({
                'message': 'Invitation resent successfully'
            }, status=status.HTTP_200_OK)
            
        except Invitation.DoesNotExist:
            return Response({
                'error': 'Invitation not found'
            }, status=status.HTTP_404_NOT_FOUND)


class InvitationDeleteView(APIView):
    """View for deleting an invitation"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def delete(self, request, invitation_id):
        """Delete an invitation"""
        # Check if user is part of an organization
        if not request.user.organization:
            return Response({
                'error': 'You must be part of an organization to delete invitations'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            invitation = Invitation.objects.get(
                id=invitation_id,
                organization=request.user.organization,
                accepted=False
            )
            
            # Delete the invitation
            invitation.delete()
            
            return Response({
                'message': 'Invitation deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Invitation.DoesNotExist:
            return Response({
                'error': 'Invitation not found'
            }, status=status.HTTP_404_NOT_FOUND)