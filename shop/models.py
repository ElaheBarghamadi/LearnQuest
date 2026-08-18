from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=80, verbose_name='نام')
    slug = models.SlugField(unique=True, allow_unicode=True)
    emoji = models.CharField(max_length=8, default='🛍️')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='children')
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'دسته‌بندی فروشگاه'
        verbose_name_plural = 'دسته‌بندی‌های فروشگاه'
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.emoji} {self.name}'


class Product(models.Model):
    PRODUCT_TYPES = [
        ('cosmetic', 'آرایشی'),
        ('consumable', 'مصرفی'),
        ('booster', 'بوستر زمانی'),
        ('unlock', 'بازکننده محتوا'),
        ('bundle', 'بسته (باندل)'),
        ('currency_pack', 'بسته ارز (آینده)'),
    ]
    name = models.CharField(max_length=120, verbose_name='نام محصول')
    slug = models.SlugField(unique=True, allow_unicode=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,
                                 related_name='products', verbose_name='دسته')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, verbose_name='نوع')
    effect_type = models.CharField(max_length=40, verbose_name='کد اثر',
                                   help_text='مثل frame / username_color / xp_booster / pet / mystery_box / exclusive_lesson')
    effect_payload = models.JSONField(default=dict, blank=True, verbose_name='پیلود اثر',
                                      help_text='مثل {"frame_class":"frame-gold"} یا {"multiplier":2,"hours":24}')
    description = models.TextField(blank=True)
    preview_emoji = models.CharField(max_length=8, blank=True, default='')
    image = models.ImageField(upload_to='shop_products/', null=True, blank=True)

    price_coins = models.PositiveIntegerField(default=0, verbose_name='قیمت (سکه)')
    price_gems = models.PositiveIntegerField(default=0, verbose_name='قیمت (الماس)')
    discount_percent = models.PositiveSmallIntegerField(default=0, verbose_name='تخفیف ٪')
    discount_ends_at = models.DateTimeField(null=True, blank=True)

    is_featured = models.BooleanField(default=False, verbose_name='ویژه')
    is_active = models.BooleanField(default=True)
    stock_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name='موجودی محدود (خالی=نامحدود)')
    sold_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=0, verbose_name='سقف خرید هر کاربر (۰=نامحدود)')
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)

    bundle_items = models.ManyToManyField('self', symmetrical=False, blank=True,
                                          related_name='bundled_in', verbose_name='اقلام داخل باندل')
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'is_featured'], name='prod_active_feat_idx'),
            models.Index(fields=['category', 'is_active'], name='prod_cat_idx'),
            models.Index(fields=['price_coins'], name='prod_price_idx'),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_product_type_display()})'


    def active_discount(self) -> int:
        if self.discount_percent and (not self.discount_ends_at or self.discount_ends_at > timezone.now()):
            return self.discount_percent
        return 0

    def final_price_coins(self) -> int:
        d = self.active_discount()
        return int(self.price_coins * (100 - d) / 100)

    def final_price_gems(self) -> int:
        d = self.active_discount()
        return int(self.price_gems * (100 - d) / 100)


    def is_available(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.available_from and self.available_from > now:
            return False
        if self.available_until and self.available_until < now:
            return False
        if self.stock_limit is not None and self.sold_count >= self.stock_limit:
            return False
        return True

    def remaining_stock(self):
        return None if self.stock_limit is None else max(0, self.stock_limit - self.sold_count)


class Purchase(models.Model):
    STATUS = [('completed', 'تکمیل‌شده'), ('refunded', 'بازگشت‌داده‌شده'), ('failed', 'ناموفق')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchases')
    coins_paid = models.PositiveIntegerField(default=0)
    gems_paid = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS, default='completed')
    idempotency_key = models.CharField(max_length=100, unique=True)
    transaction = models.ForeignKey('economy.Transaction', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='purchases')
    created_at = models.DateTimeField(auto_now_add=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'خرید'
        verbose_name_plural = 'خریدها'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'created_at'], name='purchase_user_idx')]

    def __str__(self):
        return f'#{self.pk} {self.user.username} ← {self.product.name}'


class InventoryItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inventory')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='inventory_items')
    quantity = models.PositiveIntegerField(default=1)
    equipped = models.BooleanField(default=False)
    source = models.CharField(max_length=30, default='shop')
    acquired_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'آیتم موجودی'
        verbose_name_plural = 'موجودی کاربران'
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='uniq_inventory_user_product')]
        indexes = [models.Index(fields=['user', 'equipped'], name='inv_user_equipped_idx')]

    def __str__(self):
        return f'{self.user.username} — {self.product.name} ×{self.quantity}'


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'علاقه‌مندی'
        verbose_name_plural = 'علاقه‌مندی‌ها'
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='uniq_wishlist')]


class RecentlyViewed(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'بازدید اخیر'
        verbose_name_plural = 'بازدیدهای اخیر'
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='uniq_recent_view')]
        ordering = ['-viewed_at']
