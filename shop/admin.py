from django.contrib import admin, messages

from .models import Category, Product, Purchase, InventoryItem, Wishlist, RecentlyViewed
from .services import refund_purchase


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'emoji', 'slug', 'parent', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class BundleInline(admin.TabularInline):
    model = Product.bundle_items.through
    fk_name = 'from_product'
    extra = 1
    verbose_name = 'آیتم داخل باندل'
    verbose_name_plural = 'آیتم‌های داخل باندل'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'product_type', 'effect_type', 'price_coins',
                    'price_gems', 'discount_percent', 'is_featured', 'is_active',
                    'stock_limit', 'sold_count', 'per_user_limit')
    list_filter = ('product_type', 'category', 'is_active', 'is_featured', 'effect_type')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('sold_count', 'views_count', 'created_at')
    inlines = [BundleInline]
    fieldsets = (
        ('مشخصات', {'fields': ('name', 'slug', 'category', 'product_type', 'description', 'image', 'preview_emoji')}),
        ('رفتار/اثر', {'fields': ('effect_type', 'effect_payload')}),
        ('قیمت و تخفیف', {'fields': ('price_coins', 'price_gems', 'discount_percent', 'discount_ends_at')}),
        ('موجودی و دسترسی', {'fields': ('stock_limit', 'sold_count', 'per_user_limit',
                                        'available_from', 'available_until', 'is_active', 'is_featured')}),
        ('آمار', {'fields': ('views_count', 'created_at'), 'classes': ('collapse',)}),
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'coins_paid', 'gems_paid', 'status', 'created_at', 'refunded_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'product__name', 'idempotency_key')
    readonly_fields = ('user', 'product', 'coins_paid', 'gems_paid', 'idempotency_key',
                       'transaction', 'created_at', 'refunded_at')
    actions = ['refund_selected']
    date_hierarchy = 'created_at'

    @admin.action(description='↩️ بازگشت وجه خرید (refund با تراکنش و لاگ ممیز)')
    def refund_selected(self, request, queryset):
        done = 0
        for p in queryset:
            r = refund_purchase(request.user, p.pk, reason='admin_refund')
            done += int(bool(r.get('ok')))
        self.message_user(request, f'{done} خرید بازگشت شد.', messages.SUCCESS)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'equipped', 'source', 'acquired_at', 'used_at')
    list_filter = ('equipped', 'source', 'product__product_type')
    search_fields = ('user__username', 'product__name')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__username', 'product__name')


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'viewed_at')
    readonly_fields = ('user', 'product', 'viewed_at')
