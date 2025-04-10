# views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Prefetch, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

from .models import (
    Conversation, ConversationParticipant, Message, 
    MessageRead, MessageReaction, MessageAttachment,
    MessageThread, PinnedMessage, SavedMessage, TypingIndicator
    # TaskReference removed
)
from .serializers import (
    ConversationSerializer, MessageSerializer, 
    MessageReactionSerializer, PinnedMessageSerializer,
    SavedMessageSerializer, ThreadMessageSerializer,
    UserMinimalSerializer, OrganizationUserSerializer
)
from .permissions import SameOrganizationPermission, ConversationPermission
from organizations.models import Organization, TeamMember
from django.contrib.auth import get_user_model
from tasks.models import Task

User = get_user_model()

class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, SameOrganizationPermission, ConversationPermission]

    
    def get_queryset(self):
        user = self.request.user
        # Get conversations where user is a participant
        queryset = Conversation.objects.filter(
            participants__user=user
        ).distinct().prefetch_related(
            'participants', 
            'participants__user'
        )
    
        # Instead of using a slice in prefetch_related, handle last message separately
        return queryset
    
    def perform_create(self, serializer):
        """Create a new conversation and add the current user as participant"""
        conversation = serializer.save()
        
        # Add current user as participant and admin (for group chats)
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.request.user,
            is_admin=True
        )
        
        # Add other participants from the request
        participant_ids = self.request.data.get('participant_ids', [])
        organization_id = self.request.data.get('organization')
        
        # Get organization
        organization = get_object_or_404(Organization, id=organization_id)
        
        # Verify all participants belong to the organization
        team_members = TeamMember.objects.filter(
            organization=organization,
            user__id__in=participant_ids
        )
        
        valid_user_ids = [tm.user.id for tm in team_members]
        
        # Create conversation participants
        for user_id in valid_user_ids:
            if user_id != self.request.user.id:  # Skip creator, already added
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user_id=user_id
                )
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        # Get organization
        organization = conversation.organization
        
        # Check if user is in the organization
        try:
            team_member = TeamMember.objects.get(
                organization=organization,
                user_id=user_id
            )
            
            # Check if user is already a participant
            if ConversationParticipant.objects.filter(
                conversation=conversation,
                user_id=user_id
            ).exists():
                return Response(
                    {"error": "User is already a participant"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add user as participant
            ConversationParticipant.objects.create(
                conversation=conversation,
                user_id=user_id
            )
            
            return Response(
                {"success": "User added to conversation"},
                status=status.HTTP_201_CREATED
            )
            
        except TeamMember.DoesNotExist:
            return Response(
                {"error": "User is not a member of this organization"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        # Check if requesting user is an admin
        is_admin = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user,
            is_admin=True
        ).exists()
        
        if not is_admin and user_id != request.user.id:
            # Users can remove themselves, but only admins can remove others
            return Response(
                {"error": "You don't have permission to remove this user"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove the participant
        participant = get_object_or_404(
            ConversationParticipant,
            conversation=conversation,
            user_id=user_id
        )
        participant.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def organization_users(self, request):
        """Get all users in the organization for starting new conversations"""
        organization_id = request.query_params.get('organization_id')
    
        if not organization_id:
            return Response(
                {"error": "Organization ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # Get all users except the current user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.exclude(id=request.user.id)
    
        serializer = UserMinimalSerializer(users, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessagePagination
    
    def get_queryset(self):
        user = self.request.user
        conversation_id = self.request.query_params.get('conversation_id')
        
        # Base queryset - messages in conversations where user is a participant
        queryset = Message.objects.filter(
            conversation__participants__user=user
        ).select_related('sender').prefetch_related(
            'attachments',
            'reactions',
            'reactions__user',
            'read_receipts',
            'read_receipts__user'
            # task_references and task_references__task removed
        )
        
        # Filter by conversation if provided
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
            
            # Mark messages as read when fetching them
            self.mark_as_read(user, conversation_id)
        
        return queryset.order_by('timestamp')
    
    def mark_as_read(self, user, conversation_id):
        """Mark all messages in the conversation as read by the user"""
        # Get messages that haven't been read by this user
        messages = Message.objects.filter(
            conversation_id=conversation_id
        ).exclude(
            sender=user  # Skip messages sent by current user
        ).exclude(
            read_receipts__user=user  # Skip already read messages
        )
        
        # Create read receipts
        for message in messages:
            MessageRead.objects.get_or_create(
                message=message,
                user=user
            )
    
    def perform_create(self, serializer):
        """Create a message with optional file attachments"""
        conversation_id = self.request.data.get('conversation')
        
        # Check if user is a participant
        participant = get_object_or_404(
            ConversationParticipant,
            conversation_id=conversation_id,
            user=self.request.user
        )
        
        # Create message
        message = serializer.save(sender=self.request.user)
        
        # Handle file attachments
        files = self.request.FILES.getlist('files')
        for file in files:
            MessageAttachment.objects.create(
                message=message,
                file=file,
                file_name=file.name,
                file_type=file.content_type,
                file_size=file.size
            )
        
        # Update conversation's updated_at field
        conversation = message.conversation
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # Handle thread reply
        parent_message_id = self.request.data.get('parent_message_id')
        if parent_message_id:
            # Create thread relation
            parent_message = get_object_or_404(Message, id=parent_message_id)
            MessageThread.objects.create(
                parent_message=parent_message,
                reply_message=message
            )
        
        # Process task references - removed
        # import re
        # task_ids = re.findall(r'#task-(\d+)', message.content)
        # for task_id in task_ids:
        #     try:
        #         task = Task.objects.get(id=task_id)
        #         TaskReference.objects.create(
        #             message=message,
        #             task=task
        #         )
        #     except Task.DoesNotExist:
        #         pass
                
        return message
    
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark a specific message as read"""
        message = self.get_object()
        
        # Skip if message is from current user
        if message.sender == request.user:
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        # Create read receipt
        read_receipt, created = MessageRead.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add a reaction to a message"""
        message = self.get_object()
        reaction = request.data.get('reaction')
        
        if not reaction:
            return Response(
                {"error": "Reaction is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Toggle reaction
        existing_reaction = MessageReaction.objects.filter(
            message=message,
            user=request.user,
            reaction=reaction
        )
        
        if existing_reaction.exists():
            # Remove reaction if it exists
            existing_reaction.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # Add new reaction
            new_reaction = MessageReaction.objects.create(
                message=message,
                user=request.user,
                reaction=reaction
            )
            serializer = MessageReactionSerializer(new_reaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def typing(self, request, pk=None):
        """Indicate user is typing in a conversation"""
        message = self.get_object()
        conversation = message.conversation
        
        # Update or create typing indicator
        TypingIndicator.objects.update_or_create(
            conversation=conversation,
            user=request.user,
            defaults={'timestamp': timezone.now()}
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin a message in a conversation"""
        message = self.get_object()
        conversation = message.conversation
        
        # Check if message is already pinned
        existing_pin = PinnedMessage.objects.filter(
            message=message,
            conversation=conversation
        )
        
        if existing_pin.exists():
            return Response(
                {"error": "Message is already pinned"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create pin
        pinned_message = PinnedMessage.objects.create(
            message=message,
            conversation=conversation,
            pinned_by=request.user
        )
        
        serializer = PinnedMessageSerializer(pinned_message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None):
        """Unpin a message"""
        message = self.get_object()
        
        # Find and delete pin
        pin = get_object_or_404(
            PinnedMessage,
            message=message
        )
        pin.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """Save a message for the user"""
        message = self.get_object()
        
        # Check if already saved
        existing_save = SavedMessage.objects.filter(
            message=message,
            user=request.user
        )
        
        if existing_save.exists():
            return Response(
                {"error": "Message is already saved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save the message
        saved_message = SavedMessage.objects.create(
            message=message,
            user=request.user
        )
        
        serializer = SavedMessageSerializer(saved_message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def unsave(self, request, pk=None):
        """Unsave a message"""
        message = self.get_object()
        
        # Find and delete saved message
        saved = get_object_or_404(
            SavedMessage,
            message=message,
            user=request.user
        )
        saved.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def thread(self, request):
        """Get a message thread"""
        parent_message_id = request.query_params.get('parent_message_id')
        
        if not parent_message_id:
            return Response(
                {"error": "Parent message ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get parent message with permission check
        parent_message = get_object_or_404(
            Message.objects.filter(
                conversation__participants__user=request.user
            ),
            id=parent_message_id
        )
        
        # Get thread replies
        thread_replies = MessageThread.objects.filter(
            parent_message=parent_message
        ).select_related('reply_message')
        
        # Serialize parent with replies
        serializer = ThreadMessageSerializer(parent_message)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def saved(self, request):
        """Get all messages saved by the user"""
        saved_messages = SavedMessage.objects.filter(
            user=request.user
        ).select_related('message', 'message__sender').order_by('-saved_at')
        
        serializer = SavedMessageSerializer(saved_messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get']) 
    def pinned(self, request):
        """Get all pinned messages in a conversation"""
        conversation_id = request.query_params.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {"error": "Conversation ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is a participant
        get_object_or_404(
            ConversationParticipant,
            conversation_id=conversation_id,
            user=request.user
        )
        
        # Get pinned messages
        pinned_messages = PinnedMessage.objects.filter(
            conversation_id=conversation_id
        ).select_related('message', 'message__sender', 'pinned_by').order_by('-pinned_at')
        
        serializer = PinnedMessageSerializer(pinned_messages, many=True)
        return Response(serializer.data)
        
    # reference_task action removed