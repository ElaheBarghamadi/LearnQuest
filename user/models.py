from django.db import models

# Create your models here.
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
    last_active = models.DateTimeField(auto_now=True, verbose_name='آخرین فعالیت')

    # فیلدهای فعال‌سازی
    is_verified = models.BooleanField(default=False, verbose_name='تأیید شده')
    verification_code = models.CharField(max_length=6, blank=True, verbose_name='کد تأیید')
    code_expiration = models.DateTimeField(null=True, blank=True, verbose_name='انقضای کد')

    # حل مشکل related_name
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
            self.expires_at = timezone.now() + timedelta(minutes=10)  # 10 دقیقه اعتبار
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.email} - {self.otp_code}"

    class Meta:
        verbose_name = 'OTP بازنشانی رمز'
        verbose_name_plural = 'OTP‌های بازنشانی رمز'