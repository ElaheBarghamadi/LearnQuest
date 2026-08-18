from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random
import uuid


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='ایمیل')
    phone = models.CharField(max_length=15, blank=True, verbose_name='شماره تلفن')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='آواتار')
    xp = models.IntegerField(default=0, verbose_name='امتیاز تجربه')
    level = models.IntegerField(default=1, verbose_name='سطح')
    points = models.IntegerField(default=0, verbose_name='امتیاز')
    coins = models.IntegerField(default=0, verbose_name='سکه')
    streak = models.IntegerField(default=0, verbose_name='روزهای متوالی')
    last_streak_date = models.DateField(null=True, blank=True, verbose_name='آخرین روز ثبت‌شدهٔ استریک')
    last_active = models.DateTimeField(auto_now=True, verbose_name='آخرین فعالیت')


    is_verified = models.BooleanField(default=False, verbose_name='تأیید شده')
    verification_code = models.CharField(max_length=6, blank=True, verbose_name='کد تأیید')
    code_expiration = models.DateTimeField(null=True, blank=True, verbose_name='انقضای کد')


    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='customuser_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='user',
    )

    def update_streak(self):
        today = timezone.localdate()
        if self.last_streak_date == today:
            return self.streak
        yesterday = today - timedelta(days=1)
        self.streak = (self.streak or 0) + 1 if self.last_streak_date == yesterday else 1
        self.last_streak_date = today
        self.save(update_fields=['streak', 'last_streak_date'])
        return self.streak

    def calculate_level(self):
        XP_PER_LEVEL = 200
        MAX_LEVEL = 20

        new_level = (self.xp // XP_PER_LEVEL) + 1
        if new_level > MAX_LEVEL:
            new_level = MAX_LEVEL

        return new_level

    def update_level(self):
        new_level = self.calculate_level()
        if new_level != self.level:
            self.level = new_level
            return True
        return False

    def get_level_progress(self):
        XP_PER_LEVEL = 200
        MAX_LEVEL = 20


        if self.level >= MAX_LEVEL:
            return 100


        xp_for_current_level = (self.level - 1) * XP_PER_LEVEL

        xp_in_current_level = self.xp - xp_for_current_level


        progress = (xp_in_current_level / XP_PER_LEVEL) * 100


        if progress > 100:
            return 100
        if progress < 0:
            return 0
        return progress

    def get_level(self):
        return self.level

    def add_xp(self, amount, source='', source_id=None):
        from economy.services import grant_xp
        result = grant_xp(self, amount, source=source or 'legacy', source_id=source_id)
        try:
            self.refresh_from_db(fields=['xp', 'level'])
        except Exception:
            pass
        return self.xp

    def get_xp_needed_for_next_level(self):
        XP_PER_LEVEL = 200
        MAX_LEVEL = 20

        if self.level >= MAX_LEVEL:
            return 0

        xp_for_current_level = (self.level - 1) * XP_PER_LEVEL
        xp_needed = xp_for_current_level + XP_PER_LEVEL - self.xp

        if xp_needed < 0:
            return 0
        return xp_needed

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='کاربر')
    email = models.EmailField(verbose_name='ایمیل')
    otp_code = models.CharField(max_length=6, verbose_name='کد OTP')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')
    is_used = models.BooleanField(default=False, verbose_name='استفاده شده')

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.email} - {self.otp_code}"

    class Meta:
        verbose_name = 'OTP بازنشانی رمز'
        verbose_name_plural = 'OTP‌های بازنشانی رمز'


class UserActivity(models.Model):
    KEEP_LATEST = 10

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    icon = models.CharField(max_length=50, default='bell', verbose_name='آیکون')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان فعالیت')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        old_ids = list(
            UserActivity.objects.filter(user=self.user, pk__lt=self.pk)
            .order_by('-pk').values_list('pk', flat=True)[self.KEEP_LATEST - 1:]
        )
        if old_ids:
            UserActivity.objects.filter(pk__in=old_ids).delete()

    class Meta:
        verbose_name = 'فعالیت'
        verbose_name_plural = 'فعالیت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
