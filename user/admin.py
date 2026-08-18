from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import CustomUser, PasswordResetOTP


class WalletInline(admin.StackedInline):
    from economy.models import Wallet as _W
    model = _W
    extra = 0
    can_delete = False
    readonly_fields = ('coins', 'gems', 'updated_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'level', 'xp', 'coins_col', 'gems_col',
                    'is_verified', 'is_staff', 'date_joined')
    list_filter = ('is_verified', 'level', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'phone')
    list_select_related = ('wallet',)
    inlines = [WalletInline]
    actions = ['action_grant_coins', 'action_grant_gems', 'action_ban', 'action_unban']

    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات LearnQuest', {
            'fields': ('phone', 'avatar', 'xp', 'level', 'points', 'coins', 'streak', 'is_verified')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('اطلاعات اضافی', {'fields': ('email', 'phone')}),
    )

    @admin.display(description='🪙 سکه‌ها')
    def coins_col(self, obj):
        try:
            return obj.wallet.coins
        except Exception:
            return '—'

    @admin.display(description='💎 جم‌ها')
    def gems_col(self, obj):
        try:
            return obj.wallet.gems
        except Exception:
            return '—'

    @admin.action(description='🪙 واریز ۱۰۰ سکه به کاربران (لاگ + اتمیک)')
    def action_grant_coins(self, request, queryset):
        from economy.services import grant_coins, audit
        for u in queryset:
            grant_coins(u, 100, source='admin_adjust',
                        metadata={'by': request.user.username}, actor=request.user)
            audit('admin_adjust', user=u, actor=request.user,
                  details={'delta_coins': +100})
        self.message_user(request, f'۱۰۰ سکه به {queryset.count()} کاربر واریز شد.', messages.SUCCESS)

    @admin.action(description='💎 واریز ۱۰ جم به کاربران (لاگ + اتمیک)')
    def action_grant_gems(self, request, queryset):
        from economy.services import grant_gems, audit
        for u in queryset:
            grant_gems(u, 10, source='admin_adjust',
                       metadata={'by': request.user.username}, actor=request.user)
            audit('admin_adjust', user=u, actor=request.user,
                  details={'delta_gems': +10})
        self.message_user(request, f'۱۰ جم به {queryset.count()} کاربر واریز شد.', messages.SUCCESS)

    @admin.action(description='⛔ بن کردن (غیرفعال‌سازی حساب)')
    def action_ban(self, request, queryset):
        n = queryset.filter(is_superuser=False).update(is_active=False)
        self.message_user(request, f'{n} حساب غیرفعال شد.', messages.WARNING)

    @admin.action(description='✔ رفع بن (فعال‌سازی حساب)')
    def action_unban(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f'{n} حساب فعال شد.', messages.SUCCESS)


@admin.register(PasswordResetOTP)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = [f.name for f in PasswordResetOTP._meta.fields]

    def has_add_permission(self, request):
        return False
