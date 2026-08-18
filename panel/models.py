import uuid

from django.conf import settings
from django.db import models


class PanelAdjustment(models.Model):
    TARGETS = [
        ('coins', 'سکه 🪙'),
        ('gems', 'الماس 💎'),
        ('xp', 'XP ⚡'),
        ('points', 'امتیاز 🎯'),
        ('streak', 'استریک 🔥'),
        ('item', 'آیتم فروشگاه 🎁'),
        ('status', 'وضعیت حساب 🚦'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='panel_adjustments', verbose_name='کاربر هدف')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='panel_actions',
                              verbose_name='ادمین')
    target = models.CharField(max_length=12, choices=TARGETS, verbose_name='مورد')
    amount = models.IntegerField(default=0, verbose_name='مقدار (+/−)')
    note = models.CharField(max_length=220, blank=True, default='', verbose_name='دلیل')
    extra = models.JSONField(default=dict, blank=True, verbose_name='جزئیات')
    idempotency_key = models.CharField(max_length=100, unique=True, default=uuid.uuid4,
                                       verbose_name='کلید یکتا')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'اقدام پنل'
        verbose_name_plural = 'اقدامات پنل مدیریت'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at'], name='pna_user_date_idx'),
            models.Index(fields=['target', 'created_at'], name='pna_target_date_idx'),
        ]

    def __str__(self):
        return f'{self.get_target_display()} {self.amount:+} برای {self.user.username}'
