from __future__ import annotations

import uuid

import django
from django.conf import settings
from django.db import models
from django.utils import timezone


def _check(q: models.Q, name: str) -> models.CheckConstraint:
    if django.VERSION >= (5, 1):
        return models.CheckConstraint(condition=q, name=name)
    return models.CheckConstraint(check=q, name=name)


CURRENCY_CHOICES = [
    ('coin', 'سکه 🪙'),
    ('gem', 'الماس 💎'),
    ('xp', 'امتیاز تجربه ⭐'),
]


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='wallet', verbose_name='کاربر')
    coins = models.PositiveIntegerField(default=0, verbose_name='سکه')
    gems = models.PositiveIntegerField(default=0, verbose_name='الماس')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'
        constraints = [
            _check(models.Q(coins__gte=0), 'wallet_coins_nonneg'),
            _check(models.Q(gems__gte=0), 'wallet_gems_nonneg'),
        ]

    def __str__(self):
        return f'کیف پول {self.user.username} — {self.coins}🪙 {self.gems}💎'


class Transaction(models.Model):
    TYPES = [
        ('earn', 'کسب'),
        ('spend', 'خرج'),
        ('reward', 'پاداش'),
        ('refund', 'بازگشت وجه'),
        ('admin_adjust', 'تنظیم دستی ادمین'),
        ('consume', 'مصرف آیتم'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='transactions', verbose_name='کاربر')
    currency = models.CharField(max_length=8, choices=CURRENCY_CHOICES, verbose_name='ارز')
    amount = models.IntegerField(verbose_name='مقدار (مثبت/منفی)')
    balance_after = models.IntegerField(verbose_name='موجودی پس از تراکنش')
    type = models.CharField(max_length=20, choices=TYPES, verbose_name='نوع')
    source = models.CharField(max_length=60, verbose_name='منبع')
    source_id = models.CharField(max_length=60, blank=True, default='', verbose_name='شناسه منبع')
    idempotency_key = models.CharField(max_length=100, unique=True, default=uuid.uuid4,
                                       verbose_name='کلید یکتا (ضد تکرار)')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='متادیتا')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='economy_actions', verbose_name='عامل (ادمین)')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at'], name='tx_user_date_idx'),
            models.Index(fields=['user', 'currency', 'created_at'], name='tx_user_cur_date_idx'),
            models.Index(fields=['source', 'source_id'], name='tx_source_idx'),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError('Transaction تغییرناپذیر است (immutable ledger).')
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_type_display()} {self.amount} {self.get_currency_display()} — {self.user.username}'


class RewardRule(models.Model):
    code = models.CharField(max_length=60, unique=True, verbose_name='کد قانون')
    name = models.CharField(max_length=120, verbose_name='نام فارسی')
    currency = models.CharField(max_length=8, choices=CURRENCY_CHOICES, default='xp')
    default_amount = models.PositiveIntegerField(default=10, verbose_name='مقدار پیش‌فرض')
    daily_limit = models.PositiveIntegerField(default=0, verbose_name='سقف روزانه (۰=نامحدود)')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'قانون پاداش'
        verbose_name_plural = 'قوانین پاداش'

    def __str__(self):
        return f'{self.name} (+{self.default_amount} {self.currency})'


class RewardGrant(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='reward_grants')
    rule_code = models.CharField(max_length=100)
    period_key = models.CharField(max_length=60)
    times_used = models.PositiveIntegerField(default=0)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سند پاداش'
        verbose_name_plural = 'اسناد پاداش'
        constraints = [
            models.UniqueConstraint(fields=['user', 'rule_code', 'period_key'], name='uniq_reward_grant'),
        ]
        indexes = [models.Index(fields=['user', 'rule_code', 'granted_at'], name='grant_user_rule_idx')]

    def __str__(self):
        return f'{self.user.username} — {self.rule_code} [{self.period_key}]'


class ActiveBoost(models.Model):
    BOOST_TYPES = [('xp', 'XP ⭐'), ('coin', 'سکه 🪙')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='boosts')
    boost_type = models.CharField(max_length=8, choices=BOOST_TYPES)
    multiplier = models.FloatField(default=1.5)
    expires_at = models.DateTimeField()
    inventory_item_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'بوستر فعال'
        verbose_name_plural = 'بوسترهای فعال'
        ordering = ['-expires_at']
        indexes = [models.Index(fields=['user', 'boost_type', 'expires_at'], name='boost_user_expire_idx')]

    def is_active(self) -> bool:
        return self.expires_at > timezone.now()

    def __str__(self):
        return f'{self.user.username} — {self.get_boost_type_display()} x{self.multiplier} تا {self.expires_at:%H:%M %m/%d}'


class AuditLog(models.Model):
    action = models.CharField(max_length=60, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                             related_name='economy_audit_logs', verbose_name='کاربر هدف')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='economy_audit_acts', verbose_name='عامل')
    details = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'لاگ ممیز'
        verbose_name_plural = 'لاگ‌های ممیز'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} — {self.user} @ {self.created_at:%Y-%m-%d %H:%M}'


class DailyRewardDay(models.Model):
    day = models.PositiveSmallIntegerField(unique=True, verbose_name='روز چرخه (۱..N)')
    coins = models.PositiveIntegerField(default=10)
    xp = models.PositiveIntegerField(default=5)
    gems = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'روز جایزه'
        verbose_name_plural = 'برنامهٔ جایزهٔ روزانه'
        ordering = ['day']

    def __str__(self):
        return f'روز {self.day}: {self.coins}🪙 {self.xp}⭐ {self.gems}💎'


class DailyRewardClaim(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_claims')
    claim_date = models.DateField(verbose_name='روز')
    day_index = models.PositiveSmallIntegerField(default=1, verbose_name='روز چرخه')
    streak = models.PositiveIntegerField(default=1)
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'جایزهٔ گرفته‌شدهٔ روزانه'
        verbose_name_plural = 'جایزه‌های روزانه'
        constraints = [models.UniqueConstraint(fields=['user', 'claim_date'], name='uniq_daily_claim')]

    def __str__(self):
        return f'{self.user.username} — {self.claim_date} (روز {self.day_index})'


class Season(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام فصل')
    emoji = models.CharField(max_length=8, default='🌸')
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    pass_price_gems = models.PositiveIntegerField(default=50, verbose_name='قیمت پس (الماس)')

    class Meta:
        verbose_name = 'فصل'
        verbose_name_plural = 'فصل‌ها'

    def is_running(self) -> bool:
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at

    def __str__(self):
        return f'{self.emoji} {self.name}'


class SeasonLevel(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='levels')
    level_number = models.PositiveSmallIntegerField()
    xp_required = models.PositiveIntegerField(default=100, verbose_name='XP فصل لازم')
    free_reward = models.JSONField(default=dict, blank=True,
                                   help_text='{"coins": 50} یا {"gems": 2} یا {"product_slug": "mystery-box-1"}')
    premium_reward = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'پلهٔ فصل'
        verbose_name_plural = 'پله‌های فصل'
        ordering = ['level_number']
        constraints = [models.UniqueConstraint(fields=['season', 'level_number'], name='uniq_season_level')]

    def __str__(self):
        return f'{self.season} — سطح {self.level_number}'


class UserSeasonPass(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='season_passes')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='participants')
    has_pass = models.BooleanField(default=False, verbose_name='دارای پس ویژه')
    season_xp = models.PositiveIntegerField(default=0)
    claimed_free = models.JSONField(default=list, blank=True, help_text='لیست سطح‌های رایگان گرفته‌شده')
    claimed_premium = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = 'پاس فصل کاربر'
        verbose_name_plural = 'پاس فصل‌ها'
        constraints = [models.UniqueConstraint(fields=['user', 'season'], name='uniq_user_season')]

    def current_level(self) -> int:
        levels = self.season.levels.order_by('level_number')
        lvl = 0
        for sl in levels:
            if self.season_xp >= sl.xp_required:
                lvl = sl.level_number
            else:
                break
        return lvl

    def __str__(self):
        return f'{self.user.username} — {self.season} ({"✅ پس" if self.has_pass else "رایگان"})'


class LeaderboardEntry(models.Model):
    PERIODS = [('global', 'جهانی'), ('weekly', 'هفتگی'), ('season', 'فصل')]
    period = models.CharField(max_length=40)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaderboard_rows')
    xp = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ردیف لیدربرد'
        verbose_name_plural = 'لیدربرد'
        constraints = [models.UniqueConstraint(fields=['period', 'user'], name='uniq_lb_entry')]
        indexes = [models.Index(fields=['period', 'rank'], name='lb_period_rank_idx'),
                   models.Index(fields=['period', '-xp'], name='lb_period_xp_idx')]

    def __str__(self):
        return f'{self.period} #{self.rank} — {self.user.username}'


class PetSpecies(models.Model):
    RARITY = [('common', 'معمولی'), ('rare', 'کمیاب'), ('epic', 'حماسی'), ('legendary', 'افسانه‌ای')]
    name = models.CharField(max_length=60)
    emoji = models.CharField(max_length=8, default='🐣')
    rarity = models.CharField(max_length=12, choices=RARITY, default='common')
    description = models.TextField(blank=True)
    product_slug = models.SlugField(unique=True, verbose_name='اسلاگ محصول در فروشگاه',
                                    help_text='خرید این محصول = اخذ این پت')

    class Meta:
        verbose_name = 'گونهٔ پت'
        verbose_name_plural = 'گونه‌های پت'

    def __str__(self):
        return f'{self.emoji} {self.name} ({self.get_rarity_display()})'


class UserPet(models.Model):
    FEED_XP = 20
    XP_PER_LEVEL = 100
    MAX_LEVEL = 20
    FREE_FEED_HOURS = 6
    FEED_COST = 8

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pets')
    species = models.ForeignKey(PetSpecies, on_delete=models.PROTECT, related_name='pets')
    name = models.CharField(max_length=40, verbose_name='نام پت')
    level = models.PositiveSmallIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=False, verbose_name='پت فعال (نمایش)')
    last_fed_at = models.DateTimeField(default=timezone.now)
    adopted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پت کاربر'
        verbose_name_plural = 'پت‌های کاربران'
        constraints = [models.UniqueConstraint(fields=['user', 'species'], name='uniq_user_pet_species')]

    def hunger(self) -> int:
        hours = (timezone.now() - self.last_fed_at).total_seconds() / 3600
        return max(0, min(100, int(100 - hours * 7)))

    def can_free_feed(self) -> bool:
        return (timezone.now() - self.last_fed_at).total_seconds() >= self.FREE_FEED_HOURS * 3600

    def feed(self) -> dict:
        self.xp += self.FEED_XP
        level_up = False
        new_level = min(self.xp // self.XP_PER_LEVEL + 1, self.MAX_LEVEL)
        if new_level > self.level:
            self.level = new_level
            level_up = True
        self.last_fed_at = timezone.now()
        self.save(update_fields=['xp', 'level', 'last_fed_at'])
        return {'level_up': level_up, 'level': self.level, 'xp': self.xp}

    def __str__(self):
        return f'{self.species.emoji} {self.name} ({self.user.username}) سطح {self.level}'
