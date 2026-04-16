import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'chat_{self.session_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = await self.save_message(data)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'data': message,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def save_message(self, data):
        from .models import Message
        from .serializers import MessageSerializer
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=self.scope['user'].pk)
        msg = Message.objects.create(
            session_id=self.session_id,
            sender=user,
            content=data.get('content', ''),
        )
        return {
            'id': msg.id,
            'sender': msg.sender.id,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'sender_role': msg.sender.role,
            'content': msg.content,
            'image_url': None,
            'created_at': str(msg.created_at),
        }
