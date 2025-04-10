import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, ConversationParticipant, Message, TypingIndicator
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        # Anonymous users can't connect
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get the conversation_id from the URL route
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        
        # Check if user is a participant in this conversation
        is_participant = await self.is_conversation_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join the conversation group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Notify other users that this user is online
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_online',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        if hasattr(self, 'conversation_group_name'):
            # Notify other users that this user is offline
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'user_offline',
                    'user_id': self.user.id,
                    'username': self.user.username
                }
            )
            
            # Leave the conversation group
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        """
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            # Handle a new chat message
            content = data.get('content')
            
            # Save message to database
            message = await self.save_message(content)
            
            # Send message to the conversation group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'content': content,
                    'timestamp': message.timestamp.isoformat()
                }
            )
        
        elif message_type == 'typing':
            # User is typing
            is_typing = data.get('is_typing', False)
            
            if is_typing:
                # Update typing indicator
                await self.update_typing_indicator()
            
            # Send typing status to the group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'username': self.user.get_full_name() or self.user.username,
                    'is_typing': is_typing
                }
            )
    
    async def chat_message(self, event):
        """
        Receive message from room group and send to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'content': event['content'],
            'timestamp': event['timestamp']
        }))
    
    async def user_typing(self, event):
        """
        Send typing indicator to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    async def user_online(self, event):
        """
        Send user online status to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': 'online'
        }))
    
    async def user_offline(self, event):
        """
        Send user offline status to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': 'offline'
        }))
    
    @database_sync_to_async
    def is_conversation_participant(self):
        """
        Check if the user is a participant in this conversation.
        """
        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user
        ).exists()
    
    @database_sync_to_async
    def save_message(self, content):
        """
        Save a message to the database.
        """
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        return message
    
    @database_sync_to_async
    def update_typing_indicator(self):
        """
        Update the typing indicator for this user.
        """
        conversation = Conversation.objects.get(id=self.conversation_id)
        TypingIndicator.objects.update_or_create(
            conversation=conversation,
            user=self.user,
            defaults={'timestamp': timezone.now()}
        )