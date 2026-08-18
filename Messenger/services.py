import logging

from channels.layers import get_channel_layer

from Home.jalali import jalali_time

logger = logging.getLogger(__name__)


def notify_group_name(user_id: int) -> str:
    return f'notify_user_{user_id}'


def build_message_notification(conv, msg, sender) -> dict:
    try:
        content = msg.get_content()
    except Exception:
        content = ''
    content = (content or '').replace('\n', ' ').strip()
    if len(content) > 90:
        content = content[:87] + '...'

    avatar_url = ''
    try:
        if sender.avatar:
            avatar_url = sender.avatar.url
    except Exception:
        avatar_url = ''

    return {
        'type': 'notify.message',
        'conversation_id': conv.pk,
        'is_group': bool(conv.is_group),
        'group_name': conv.name or '',
        'sender_id': sender.pk,
        'sender_username': sender.username,
        'sender_avatar': avatar_url,
        'excerpt': content,
        'time': jalali_time(msg.created_at),
    }


def broadcast_message_notification(conv, msg, sender) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    payload = build_message_notification(conv, msg, sender)
    event = {
        'type': 'notify_message',
        'payload': payload,
    }
    from asgiref.sync import async_to_sync

    for participant in conv.participants.exclude(pk=sender.pk):
        try:
            async_to_sync(layer.group_send)(notify_group_name(participant.pk), event)
        except Exception:
            logger.exception('خطا در ارسال اعلان پیام برای کاربر %s', participant.pk)
