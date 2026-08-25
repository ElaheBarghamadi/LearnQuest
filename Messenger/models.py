import secrets

from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import hashlib


def generate_invite_token() -> str:
    return secrets.token_urlsafe(16)[:22]


class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='نام گروه'
    )
    is_group = models.BooleanField(default=False, verbose_name='گروه است؟')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='created_groups',
        verbose_name='سازنده (مدیر گروه)'
    )
    invite_token = models.CharField(
        max_length=32, unique=True, null=True, blank=True,
        verbose_name='توکن لینک دعوت'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'مکالمه'
        verbose_name_plural = 'مکالمات'

    def __str__(self):
        if self.is_group and self.name:
            return f"گروه: {self.name}"
        participants = self.participants.all()
        names = [str(p) for p in participants[:3]]
        return f"مکالمه بین: {', '.join(names)}"

    def save(self, *args, **kwargs):

        if self.is_group and not self.invite_token:
            token = generate_invite_token()
            while Conversation.objects.filter(invite_token=token).exists():
                token = generate_invite_token()
            self.invite_token = token
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_dm(cls, user, other):
        conv = cls.objects.filter(is_group=False) \
            .filter(participants=user).filter(participants=other).first()
        if not conv:
            conv = cls.objects.create(is_group=False)
            conv.participants.add(user, other)
        return conv

    def get_other_participant(self, user):
        return self.participants.exclude(pk=user.pk).first()

    def get_unread_count(self, user) -> int:
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def members_count(self) -> int:
        return self.participants.count()

    def is_owner(self, user) -> bool:
        if not user or not self.is_group:
            return False
        if self.created_by_id:
            return self.created_by_id == user.pk
        # Groups created before the ownership field existed have no manager.
        # Promote their earliest member virtually so they remain manageable.
        first_member = self.participants.order_by('pk').first()
        return bool(first_member and first_member.pk == user.pk)


class BlockedUser(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='blocks_made', verbose_name='بلاک‌کننده'
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='blocked_by', verbose_name='بلاک‌شده'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
        verbose_name = 'بلاک کاربر'
        verbose_name_plural = 'بلاک‌های کاربران'

    def __str__(self):
        return f"{self.blocker} ⛔ {self.blocked}"

    @classmethod
    def is_blocked_between(cls, user_a, user_b) -> bool:
        if not user_a or not user_b:
            return False
        return cls.objects.filter(
            models.Q(blocker=user_a, blocked=user_b) |
            models.Q(blocker=user_b, blocked=user_a)
        ).exists()


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    encrypted_content = models.TextField(verbose_name='محتوای رمزنگاری‌شده')
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name='replies', verbose_name='پاسخ به')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'پیام'
        verbose_name_plural = 'پیام‌ها'

    def __str__(self):
        return f"پیام از {self.sender} در {self.conversation}"

    def _get_encryption_key(self) -> bytes:
        user_key = f"{self.sender.pk}-{settings.SECRET_KEY}"
        key_hash = hashlib.sha256(user_key.encode()).digest()
        return base64.urlsafe_b64encode(key_hash)

    def set_content(self, raw_content: str) -> None:
        key = self._get_encryption_key()
        f = Fernet(key)
        self.encrypted_content = f.encrypt(raw_content.encode()).decode()

    def get_content(self) -> str:
        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            return f.decrypt(self.encrypted_content.encode()).decode()
        except Exception:
            return '[پیام قابل رمزگشایی نیست]'
