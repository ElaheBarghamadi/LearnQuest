import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from .models import BlockedUser, Conversation, Message
from .services import broadcast_message_notification, notify_group_name
from Home.jalali import jalali_date_long, jalali_time

logger = logging.getLogger(__name__)
User = get_user_model()


def _chat_group_name(conversation_id: int) -> str:
    return f"chat_{conversation_id}"


class ChatConsumer(AsyncWebsocketConsumer):


    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.group_name = _chat_group_name(self.conversation_id)
        self.user = self.scope.get('user')


        if not self.user or not self.user.is_authenticated:
            logger.warning("WebSocket اتصال رد شد: کاربر احراز هویت نشده")
            await self.close(code=4001)
            return


        is_member = await self._check_membership()
        if not is_member:
            logger.warning(f"WebSocket اتصال رد شد: کاربر {self.user.pk} عضو مکالمه {self.conversation_id} نیست")
            await self.close(code=4003)
            return


        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()


        await self._update_last_seen()


        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user_status',
                'user_id': self.user.pk,
                'online': True,
            }
        )


        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'اتصال برقرار شد',
            'user_id': self.user.pk,
        }))

        logger.info(f"WebSocket متصل شد: کاربر {self.user.pk} در مکالمه {self.conversation_id}")


    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):

            if hasattr(self, 'user') and self.user and self.user.is_authenticated:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'user_status',
                        'user_id': self.user.pk,
                        'online': False,
                    }
                )

            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        logger.info(f"WebSocket قطع شد: کد {close_code}")


    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type', '')


            await self._update_last_seen()

            if msg_type == 'send_message':
                await self._handle_send_message(data)

            elif msg_type == 'typing':
                await self._handle_typing(data)

            elif msg_type == 'mark_read':
                await self._handle_mark_read(data)

            elif msg_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

            else:
                logger.warning(f"نوع پیام ناشناخته: {msg_type}")

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'فرمت JSON نامعتبر است'
            }))
        except Exception as e:
            logger.error(f"خطا در پردازش پیام WebSocket: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'خطای داخلی سرور'
            }))


    async def _handle_send_message(self, data: dict):
        raw_content = data.get('content', '').strip()

        if not raw_content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'متن پیام نمی‌تواند خالی باشد'
            }))
            return

        if len(raw_content) > 5000:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'پیام بیش از حد مجاز طولانی است'
            }))
            return


        if await self._dm_blocked():
            await self.send(text_data=json.dumps({
                'type': 'blocked',
                'message': 'امکان ارسال پیام در این گفت‌وگو وجود ندارد'
            }, ensure_ascii=False))
            return


        msg = await self._save_message(raw_content)
        if not msg:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'خطا در ذخیره پیام'
            }))
            return


        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'new_message',
                'message_id': msg['id'],
                'sender_id': msg['sender_id'],
                'sender_username': msg['sender_username'],
                'content': msg['content'],
                'created_at': msg['created_at'],
                'created_at_day': msg['created_at_day'],
                'conversation_id': int(self.conversation_id),
            }
        )


    async def _handle_typing(self, data: dict):
        is_typing = data.get('is_typing', False)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.pk,
                'username': self.user.username,
                'is_typing': bool(is_typing),
            }
        )


    async def _handle_mark_read(self, data: dict):
        await self._mark_messages_read()

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'messages_read',
                'user_id': self.user.pk,
                'conversation_id': int(self.conversation_id),
            }
        )


    async def new_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'content': event['content'],
            'created_at': event['created_at'],
            'created_at_day': event.get('created_at_day', ''),
            'conversation_id': event['conversation_id'],
            'is_mine': event['sender_id'] == self.user.pk,
        }))

    async def typing_indicator(self, event):
        if event['user_id'] != self.user.pk:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def messages_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'user_id': event['user_id'],
            'conversation_id': event['conversation_id'],
        }))

    async def user_status(self, event):
        if event['user_id'] != self.user.pk:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'online': event['online'],
            }))


    @database_sync_to_async
    def _check_membership(self) -> bool:
        try:
            return Conversation.objects.filter(
                pk=self.conversation_id,
                participants=self.user
            ).exists()
        except Exception:
            return False

    @database_sync_to_async
    def _dm_blocked(self) -> bool:
        try:
            conv = Conversation.objects.get(pk=self.conversation_id)
            if conv.is_group:
                return False
            other = conv.participants.exclude(pk=self.user.pk).first()
            return BlockedUser.is_blocked_between(self.user, other) if other else False
        except Exception:
            return False

    @database_sync_to_async
    def _save_message(self, content: str) -> dict | None:
        try:
            conv = Conversation.objects.get(pk=self.conversation_id)
            msg = Message(conversation=conv, sender=self.user)
            msg.set_content(content)
            msg.save()


            conv.save(update_fields=['updated_at'])

            try:
                broadcast_message_notification(conv, msg, self.user)
            except Exception:
                logger.error('خطا در پخش اعلان پیام', exc_info=True)

            return {
                'id': msg.pk,
                'sender_id': msg.sender_id,
                'sender_username': self.user.username,
                'content': content,
                'created_at': jalali_time(msg.created_at, fa=False),
                'created_at_full': msg.created_at.isoformat(),
                'created_at_day': jalali_date_long(msg.created_at),
            }
        except Exception as e:
            logger.error(f"خطا در ذخیره پیام: {e}", exc_info=True)
            return None

    @database_sync_to_async
    def _mark_messages_read(self):
        Message.objects.filter(
            conversation_id=self.conversation_id,
            is_read=False
        ).exclude(sender=self.user).update(is_read=True)

    @database_sync_to_async
    def _update_last_seen(self):
        cache.set(
            f"user_last_seen_{self.user.pk}",
            timezone.now(),
            timeout=60 * 60 * 24
        )


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        self.group_name = notify_group_name(self.user.pk)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"WS اعلان‌ها متصل شد: کاربر {self.user.pk}")

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data or '{}')
        except json.JSONDecodeError:
            return
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def notify_message(self, event):
        await self.send(text_data=json.dumps(event['payload'], ensure_ascii=False))
