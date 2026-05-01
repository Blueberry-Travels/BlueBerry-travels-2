"""
WebSocket consumer for collab group real-time chat.

Connection URL:
  ws://host/ws/collab/<group_id>/
  Header: Authorization: Bearer <jwt_access_token>

On connect:
  - Validate JWT
  - Verify user is an accepted member of the group
  - Join channel group
  - Send last 50 messages as history

On receive (text):
  - Persist to CollabMessage
  - Broadcast to all group members

On disconnect:
  - Leave channel group
  - Send system message (optional)
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class CollabChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_id   = self.scope['url_route']['kwargs']['group_id']
        self.room_name  = f'collab_{self.group_id.replace("-", "_")}'
        self.user       = None
        self.user_id    = None
        self.user_name  = None

        # Validate JWT from query string or header
        token = self._extract_token()
        if not token:
            await self.close(code=4001)
            return

        user = await self._get_user_from_token(token)
        if not user:
            await self.close(code=4001)
            return

        self.user      = user
        self.user_id   = str(user.id)
        self.user_name = getattr(user, 'name', user.username)

        # Verify membership
        is_member = await self._verify_membership()
        if not is_member:
            await self.close(code=4003)
            return

        # Join channel group
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        # Send message history
        history = await self._get_history()
        await self.send(text_data=json.dumps({
            'type':     'history',
            'messages': history,
        }))

        # Broadcast join event
        await self.channel_layer.group_send(self.room_name, {
            'type':         'chat_system',
            'content':      f'{self.user_name} joined the group.',
            'sender_id':    self.user_id,
            'sender_name':  self.user_name,
        })

    async def disconnect(self, close_code):
        if self.room_name:
            await self.channel_layer.group_discard(
                self.room_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data    = json.loads(text_data)
            content = str(data.get('content', '')).strip()
            msg_type= data.get('message_type', 'text')

            if not content:
                return

            # Persist
            msg = await self._save_message(content, msg_type,
                                           data.get('metadata', {}))

            # Broadcast
            await self.channel_layer.group_send(self.room_name, {
                'type':         'chat_message',
                'message':      msg.to_dict() if hasattr(msg, 'to_dict') else msg,
            })

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON.'}))
        except Exception as e:
            logger.error(f'CollabChat receive error: {e}')

    async def chat_message(self, event):
        """Receive message from channel group and send to WebSocket."""
        await self.send(text_data=json.dumps({
            'type':    'message',
            'message': event['message'],
        }))

    async def chat_system(self, event):
        """Receive system event from channel group."""
        await self.send(text_data=json.dumps({
            'type':        'system',
            'content':     event['content'],
            'sender_name': event['sender_name'],
        }))

    # ── DB helpers ────────────────────────────────────────────────────────

    def _extract_token(self) -> str:
        # Try query string first (ws://host/ws/collab/id/?token=xxx)
        qs = dict(
            item.split('=') for item in
            self.scope.get('query_string', b'').decode().split('&')
            if '=' in item
        )
        if qs.get('token'):
            return qs['token']
        # Try headers
        for name, value in self.scope.get('headers', []):
            if name == b'authorization':
                parts = value.decode().split(' ')
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    return parts[1]
        return ''

    @database_sync_to_async
    def _get_user_from_token(self, token: str):
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from engine_meta.models import User
            decoded = AccessToken(token)
            return User.objects.get(id=decoded['user_id'])
        except Exception as e:
            logger.debug(f'Token validation failed: {e}')
            return None

    @database_sync_to_async
    def _verify_membership(self) -> bool:
        try:
            from engine_b2c.collab_models import CollabMember
            return CollabMember.objects.filter(
                group_id=self.group_id,
                user_id=self.user_id,
                status='accepted',
            ).exists()
        except Exception:
            return False

    @database_sync_to_async
    def _get_history(self) -> list:
        try:
            from engine_b2c.collab_models import CollabMessage
            msgs = CollabMessage.objects.filter(
                group_id=self.group_id
            ).order_by('-created_at')[:50]
            return [m.to_dict() for m in reversed(list(msgs))]
        except Exception:
            return []

    @database_sync_to_async
    def _save_message(self, content: str, msg_type: str, metadata: dict):
        from engine_b2c.collab_models import CollabMessage
        return CollabMessage.objects.create(
            group_id    = self.group_id,
            sender_id   = self.user_id,
            sender_name = self.user_name,
            message_type= msg_type,
            content     = content,
            metadata    = metadata,
        )