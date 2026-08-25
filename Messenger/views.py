import json
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import BlockedUser, Conversation, Message
from .services import broadcast_message_notification
from Home.jalali import jalali_date, jalali_date_long, jalali_parts, jalali_time

logger = logging.getLogger(__name__)
User = get_user_model()

ONLINE_THRESHOLD_SECONDS = 5 * 60


def _is_user_online(user_id: int) -> bool:
    last_seen = cache.get(f"user_last_seen_{user_id}")
    if not last_seen:
        return False
    return (timezone.now() - last_seen).total_seconds() < ONLINE_THRESHOLD_SECONDS


def _invite_url(request, conv: Conversation) -> str:
    if not (conv.is_group and conv.invite_token):
        return ''
    return request.build_absolute_uri(f'/messenger/join/{conv.invite_token}/')


def _system_message(conv, sender, text: str):
    msg = Message(conversation=conv, sender=sender)
    msg.set_content(f'ℹ️ {text}')
    msg.save()
    conv.save(update_fields=['updated_at'])
    return msg


def _format_conversation(request, conv: Conversation, current_user) -> dict:
    last_msg = conv.messages.order_by('-created_at').first()
    unread_count = conv.messages.filter(is_read=False).exclude(sender=current_user).count()

    last_message_text, last_message_time = '', ''
    if last_msg:
        last_message_text = last_msg.get_content()
        if len(last_message_text) > 60:
            last_message_text = last_message_text[:57] + '...'
        day_parts = jalali_parts(last_msg.created_at)
        today_parts = jalali_parts(timezone.localtime(timezone.now()))
        if day_parts and day_parts == today_parts:
            last_message_time = jalali_time(last_msg.created_at, fa=False)
        else:
            last_message_time = jalali_date(last_msg.created_at)

    base = {
        'id': conv.pk,
        'last_message': last_message_text,
        'last_message_time': last_message_time,
        'unread_count': unread_count,
        'avatar': None,
    }

    if conv.is_group:
        base.update({
            'user_id': conv.created_by_id or current_user.pk,
            'username': conv.name or 'گروه بدون‌نام',
            'is_group': True,
            'online': False,
            'members_count': conv.participants.count(),
            'owner_id': conv.created_by_id,
            'is_owner': conv.is_owner(current_user),
            'invite_url': _invite_url(request, conv),
        })
    else:
        other = conv.participants.exclude(pk=current_user.pk).first() or current_user
        base.update({
            'user_id': other.pk,
            'username': other.username,
            'is_group': False,
            'online': _is_user_online(other.pk),
            'members_count': 2,
            'owner_id': None,
            'is_owner': False,
            'invite_url': '',
            'blocked_by_me': other.pk != current_user.pk and BlockedUser.objects.filter(
                blocker=current_user, blocked=other).exists(),
            'blocked_between': BlockedUser.is_blocked_between(current_user, other)
            if other.pk != current_user.pk else False,
        })
    return base


def _format_message(msg: Message, current_user) -> dict:
    content = msg.get_content()
    return {
        'id': msg.pk,
        'sender_id': msg.sender_id,
        'sender_username': msg.sender.username,
        'content': content,
        'is_system': content.startswith('ℹ️'),
        'created_at': jalali_time(msg.created_at, fa=False),
        'created_at_full': msg.created_at.isoformat(),
        'created_at_day': jalali_date_long(msg.created_at),
        'is_mine': msg.sender_id == current_user.pk,
        'is_read': msg.is_read,
    }


@login_required
def messenger_page(request):
    return render(request, 'messenger/app.html')


@login_required
@require_http_methods(["GET", "POST"])
def join_group(request, token: str):
    conv = get_object_or_404(Conversation, invite_token=token, is_group=True)
    is_member = conv.participants.filter(pk=request.user.pk).exists()

    if request.method == 'POST':
        # Lock the group while checking capacity so simultaneous invite joins
        # cannot make a 200-member group overflow its stated limit.
        with transaction.atomic():
            conv = Conversation.objects.select_for_update().get(pk=conv.pk)
            is_member = conv.participants.filter(pk=request.user.pk).exists()
            if not is_member:
                if conv.participants.count() >= 200:
                    messages.error(request, 'ظرفیت گروه تکمیل است!')
                    return redirect('messenger:join_group', token=token)
                conv.participants.add(request.user)
                _system_message(conv, request.user, f'{request.user.username} با لینک دعوت به گروه پیوست 🎉')
        return redirect(f'/messenger/?c={conv.pk}')

    return render(request, 'messenger/join.html', {
        'conv': conv,
        'members_count': conv.participants.count(),
        'is_member': is_member,
        'preview_members': conv.participants.all()[:6],
    })


@login_required
@require_http_methods(["GET"])
def get_conversations(request) -> JsonResponse:
    try:
        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants').order_by('-updated_at')
        data = [_format_conversation(request, conv, request.user) for conv in conversations]
        return JsonResponse({'success': True, 'conversations': data, 'me_id': request.user.pk})
    except Exception as e:
        logger.error(f"خطا در دریافت مکالمات: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'خطا در دریافت مکالمات'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_or_create_conversation(request, user_id: int) -> JsonResponse:
    if user_id == request.user.pk:
        return JsonResponse({'success': False, 'error': 'نمی‌توانید با خودتان مکالمه داشته باشید'}, status=400)
    try:
        other_user = get_object_or_404(User, pk=user_id)

        if BlockedUser.is_blocked_between(request.user, other_user):
            return JsonResponse({'success': False,
                                 'error': 'امکان گفت‌وگو با این کاربر وجود ندارد'}, status=403)

        conv = Conversation.get_or_create_dm(request.user, other_user)
        return JsonResponse({'success': True,
                             'conversation': _format_conversation(request, conv, request.user)})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'کاربر یافت نشد'}, status=404)
    except Exception as e:
        logger.error(f"خطا در دریافت/ایجاد مکالمه: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'خطای داخلی سرور'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_messages(request, conversation_id: int) -> JsonResponse:
    try:
        conv = get_object_or_404(Conversation, pk=conversation_id)
        if not conv.participants.filter(pk=request.user.pk).exists():
            return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)

        Message.objects.filter(conversation=conv, is_read=False) \
            .exclude(sender=request.user).update(is_read=True)

        messages_qs = conv.messages.select_related('sender').order_by('created_at')
        data = [_format_message(m, request.user) for m in messages_qs]

        payload = {
            'success': True,
            'messages': data,
            'conversation_id': conversation_id,
            'conversation': _format_conversation(request, conv, request.user),
        }
        if conv.is_group:
            payload['participants'] = [
                {'id': u.pk, 'username': u.username, 'is_owner': conv.created_by_id == u.pk,
                 'online': _is_user_online(u.pk)}
                for u in conv.participants.all().order_by('username')
            ]
        return JsonResponse(payload)
    except Exception as e:
        logger.error(f"خطا در دریافت پیام‌ها: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'خطا در دریافت پیام‌ها'}, status=500)


@login_required
@require_http_methods(["POST"])
def send_message(request) -> JsonResponse:
    try:
        body = json.loads(request.body)
        conversation_id = body.get('conversation_id')
        raw_content = (body.get('content') or '').strip()

        if not conversation_id:
            return JsonResponse({'success': False, 'error': 'شناسه مکالمه الزامی است'}, status=400)
        if not raw_content:
            return JsonResponse({'success': False, 'error': 'متن پیام نمی‌تواند خالی باشد'}, status=400)
        if len(raw_content) > 5000:
            return JsonResponse({'success': False, 'error': 'پیام بیش از حد مجاز طولانی است'}, status=400)

        conv = get_object_or_404(Conversation, pk=conversation_id)
        if not conv.participants.filter(pk=request.user.pk).exists():
            return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)


        if not conv.is_group:
            other = conv.participants.exclude(pk=request.user.pk).first()
            if other and BlockedUser.is_blocked_between(request.user, other):
                return JsonResponse({'success': False, 'blocked': True,
                                     'error': 'امکان ارسال پیام در این گفت‌وگو وجود ندارد'}, status=403)

        msg = Message(conversation=conv, sender=request.user)
        msg.set_content(raw_content)
        msg.save()
        conv.save(update_fields=['updated_at'])
        try:
            broadcast_message_notification(conv, msg, request.user)
        except Exception:
            logger.error('خطا در پخش اعلان پیام', exc_info=True)
        return JsonResponse({'success': True, 'message': _format_message(msg, request.user)}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'فرمت JSON نامعتبر'}, status=400)
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'خطا در ارسال پیام'}, status=500)


@login_required
@require_http_methods(["GET"])
def search_users(request) -> JsonResponse:
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'success': True, 'users': []})
    try:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(pk=request.user.pk)[:20]
        my_blocks = set(BlockedUser.objects.filter(blocker=request.user).values_list('blocked_id', flat=True))
        blocked_me = set(BlockedUser.objects.filter(blocked=request.user).values_list('blocker_id', flat=True))
        data = [{
            'id': u.pk,
            'username': u.username,
            'avatar': None,
            'online': _is_user_online(u.pk),
            'blocked_by_me': u.pk in my_blocks,
            'blocked_me': u.pk in blocked_me,
        } for u in users]
        return JsonResponse({'success': True, 'users': data})
    except Exception as e:
        logger.error(f"خطا در جستجوی کاربران: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'خطا در جستجو'}, status=500)


@login_required
@require_http_methods(["GET"])
def online_status(request, user_id: int) -> JsonResponse:
    try:
        get_object_or_404(User, pk=user_id)
        last_seen = cache.get(f"user_last_seen_{user_id}")
        return JsonResponse({
            'success': True, 'user_id': user_id,
            'online': _is_user_online(user_id),
            'last_seen': last_seen.isoformat() if last_seen else None,
        })
    except Exception as e:
        logger.error(f"خطا در دریافت وضعیت آنلاین: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'خطای داخلی'}, status=500)


@login_required
@require_http_methods(["POST"])
def create_group(request) -> JsonResponse:
    try:
        body = json.loads(request.body)
        name = (body.get('name') or '').strip()
        participant_ids = body.get('participant_ids') or []

        if not name:
            return JsonResponse({'success': False, 'error': 'نام گروه الزامی است'}, status=400)
        if len(name) > 255:
            return JsonResponse({'success': False, 'error': 'نام گروه بیش از حد مجاز طولانی است'}, status=400)
        if not participant_ids:
            return JsonResponse({'success': False, 'error': 'حداقل یک عضو باید انتخاب شود'}, status=400)
        if len(participant_ids) > 50:
            return JsonResponse({'success': False, 'error': 'تعداد اعضای گروه نمی‌تواند بیشتر از ۵۰ نفر باشد'}, status=400)

        participant_ids = list(set(int(i) for i in participant_ids if int(i) != request.user.pk))
        participants = list(User.objects.filter(pk__in=participant_ids))
        if len(participants) != len(participant_ids):
            return JsonResponse({'success': False, 'error': 'برخی از کاربران یافت نشدند'}, status=400)

        # Keep creation and its initial system event all-or-nothing.
        with transaction.atomic():
            conv = Conversation.objects.create(
                name=name, is_group=True, created_by=request.user,
            )
            conv.participants.add(request.user, *participants)
            _system_message(conv, request.user, f'گروه «{name}» ساخته شد 🎉')

        return JsonResponse({'success': True,
                             'conversation': _format_conversation(request, conv, request.user)}, status=201)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'شناسهٔ اعضا یا فرمت درخواست نامعتبر است'}, status=400)
    except Exception:
        logger.error('خطا در ایجاد گروه', exc_info=True)
        return JsonResponse({'success': False, 'error': 'خطا در ایجاد گروه'}, status=500)


@login_required
@require_http_methods(["POST"])
def leave_group(request, conversation_id: int) -> JsonResponse:
    conv = get_object_or_404(Conversation, pk=conversation_id, is_group=True)
    if not conv.participants.filter(pk=request.user.pk).exists():
        return JsonResponse({'success': False, 'error': 'عضوی این گروه نیستید'}, status=403)

    _system_message(conv, request.user, f'{request.user.username} گروه را ترک کرد 👋')
    conv.participants.remove(request.user)

    remaining = conv.participants.count()
    if remaining == 0:
        conv.delete()
        return JsonResponse({'success': True, 'deleted': True})
    if conv.created_by_id == request.user.pk:
        conv.created_by = conv.participants.order_by('id').first()
        conv.save(update_fields=['created_by'])
    return JsonResponse({'success': True, 'deleted': False, 'members_count': remaining})


@login_required
@require_http_methods(["POST"])
def regenerate_invite(request, conversation_id: int) -> JsonResponse:
    conv = get_object_or_404(Conversation, pk=conversation_id, is_group=True)
    if not conv.is_owner(request.user):
        return JsonResponse({'success': False, 'error': 'فقط مدیر گروه می‌تواند لینک را عوض کند'}, status=403)
    conv.invite_token = None
    conv.save()
    return JsonResponse({'success': True, 'invite_url': _invite_url(request, conv)})


@login_required
@require_http_methods(["POST"])
def group_add_members(request, conversation_id: int) -> JsonResponse:
    conv = get_object_or_404(Conversation, pk=conversation_id, is_group=True)
    if not conv.is_owner(request.user):
        return JsonResponse({'success': False, 'error': 'فقط مدیر گروه می‌تواند عضو اضافه کند'}, status=403)
    try:
        body = json.loads(request.body)
        ids = list(set(int(i) for i in (body.get('participant_ids') or [])))
        if not ids:
            return JsonResponse({'success': False, 'error': 'عضوی انتخاب نشده'}, status=400)
        users = list(User.objects.filter(pk__in=ids))
        if len(users) != len(ids):
            return JsonResponse({'success': False, 'error': 'برخی کاربران یافت نشدند'}, status=400)
        with transaction.atomic():
            conv = Conversation.objects.select_for_update().get(pk=conv.pk)
            if not conv.is_owner(request.user):
                return JsonResponse({'success': False, 'error': 'فقط مدیر گروه می‌تواند عضو اضافه کند'}, status=403)
            existing_ids = set(conv.participants.values_list('pk', flat=True))
            new_users = [u for u in users if u.pk not in existing_ids]
            if conv.participants.count() + len(new_users) > 200:
                return JsonResponse({'success': False, 'error': 'افزودن این تعداد عضو از ظرفیت ۲۰۰ نفر گروه بیشتر است'}, status=400)
            added = []
            for u in new_users:
                conv.participants.add(u)
                _system_message(conv, request.user, f'{u.username} به گروه اضافه شد ➕')
                added.append(u.username)
            members_count = conv.participants.count()
        return JsonResponse({'success': True, 'added': added,
                             'members_count': members_count})
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'فرمت JSON نامعتبر'}, status=400)


@login_required
@require_http_methods(["POST"])
def group_remove_member(request, conversation_id: int, user_id: int) -> JsonResponse:
    conv = get_object_or_404(Conversation, pk=conversation_id, is_group=True)
    if not conv.is_owner(request.user):
        return JsonResponse({'success': False, 'error': 'فقط مدیر گروه می‌تواند عضو حذف کند'}, status=403)
    if user_id == request.user.pk:
        return JsonResponse({'success': False, 'error': 'برای خروج خودتان از «ترک گروه» استفاده کنید'}, status=400)
    target = get_object_or_404(User, pk=user_id)
    if not conv.participants.filter(pk=target.pk).exists():
        return JsonResponse({'success': False, 'error': 'این کاربر عضو گروه نیست'}, status=404)
    conv.participants.remove(target)
    _system_message(conv, request.user, f'{target.username} از گروه حذف شد ✂️')
    return JsonResponse({'success': True, 'members_count': conv.participants.count()})


@login_required
@require_http_methods(["POST"])
def block_user(request, user_id: int) -> JsonResponse:
    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk:
        return JsonResponse({'success': False, 'error': 'نمی‌توانید خودتان را بلاک کنید'}, status=400)
    _, created = BlockedUser.objects.get_or_create(blocker=request.user, blocked=target)
    return JsonResponse({'success': True, 'blocked': True, 'created': created,
                         'username': target.username})


@login_required
@require_http_methods(["POST"])
def unblock_user(request, user_id: int) -> JsonResponse:
    deleted, _ = BlockedUser.objects.filter(blocker=request.user, blocked_id=user_id).delete()
    return JsonResponse({'success': True, 'blocked': False, 'was_blocked': bool(deleted)})


@login_required
@require_http_methods(["GET"])
def blocked_list(request) -> JsonResponse:
    rows = BlockedUser.objects.filter(blocker=request.user).select_related('blocked').order_by('-created_at')
    data = [{'id': r.blocked_id, 'username': r.blocked.username,
             'since': jalali_date(r.created_at)} for r in rows]
    return JsonResponse({'success': True, 'blocked_users': data})
