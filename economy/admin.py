from django.contrib import admin, messages

from .models import (Wallet, Transaction, RewardRule, RewardGrant, ActiveBoost,
                     AuditLog, DailyRewardDay, DailyRewardClaim, Season, SeasonLevel,
                     UserSeasonPass, LeaderboardEntry, PetSpecies, UserPet)
from .services import grant_coins, grant_gems, audit


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'coins', 'gems', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('coins', 'gems', 'updated_at')
    actions = ['add_100_coins', 'remove_100_coins', 'add_10_gems']

    @admin.action(description='🪙 واریز ۱۰۰ سکه (با ثبت در دفتر و ممیز)')
    def add_100_coins(self, request, queryset):
        for w in queryset.select_related('user'):
            grant_coins(w.user, 100, source='admin_adjust', idempotency_key=None,
                        metadata={'by': request.user.username}, actor=request.user)
            audit('admin_adjust', user=w.user, actor=request.user, details={'delta_coins': +100})
        self.message_user(request, f'{queryset.count()} کیف پول شارژ شد.', messages.SUCCESS)

    @admin.action(description='🪙 کسر ۱۰۰ سکه (با ثبت در دفتر و ممیز)')
    def remove_100_coins(self, request, queryset):
        from .services import spend, InsufficientFunds
        import uuid
        for w in queryset.select_related('user'):
            try:
                spend(w.user, 'coin', 100, source='admin_adjust',
                      idempotency_key=f'admin:adj:{w.user_id}:{uuid.uuid4().hex[:12]}',
                      metadata={'by': request.user.username}, actor=request.user)
            except InsufficientFunds:
                pass
            audit('admin_adjust', user=w.user, actor=request.user, details={'delta_coins': -100})
        self.message_user(request, 'انجام شد.', messages.SUCCESS)

    @admin.action(description='💎 واریز ۱۰ الماس (با ثبت در دفتر و ممیز)')
    def add_10_gems(self, request, queryset):
        for w in queryset.select_related('user'):
            grant_gems(w.user, 10, source='admin_adjust',
                       metadata={'by': request.user.username}, actor=request.user)
            audit('admin_adjust', user=w.user, actor=request.user, details={'delta_gems': +10})
        self.message_user(request, 'انجام شد.', messages.SUCCESS)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'currency', 'amount', 'balance_after', 'source', 'created_at')
    list_filter = ('type', 'currency', 'source', 'created_at')
    search_fields = ('user__username', 'source_id', 'idempotency_key')
    readonly_fields = [f.name for f in Transaction._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RewardRule)
class RewardRuleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'currency', 'default_amount', 'daily_limit', 'is_active')
    list_filter = ('currency', 'is_active')
    search_fields = ('code', 'name')


@admin.register(RewardGrant)
class RewardGrantAdmin(admin.ModelAdmin):
    list_display = ('user', 'rule_code', 'period_key', 'granted_at')
    list_filter = ('rule_code', 'granted_at')
    search_fields = ('user__username',)


@admin.register(ActiveBoost)
class ActiveBoostAdmin(admin.ModelAdmin):
    list_display = ('user', 'boost_type', 'multiplier', 'expires_at', 'created_at')
    list_filter = ('boost_type',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'actor', 'ip', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'actor__username')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


@admin.register(DailyRewardDay)
class DailyRewardDayAdmin(admin.ModelAdmin):
    list_display = ('day', 'coins', 'xp', 'gems')


@admin.register(DailyRewardClaim)
class DailyRewardClaimAdmin(admin.ModelAdmin):
    list_display = ('user', 'claim_date', 'day_index', 'streak')
    list_filter = ('claim_date',)
    readonly_fields = ('user', 'claim_date', 'day_index', 'streak', 'claimed_at')


class SeasonLevelInline(admin.TabularInline):
    model = SeasonLevel
    extra = 1


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'emoji', 'starts_at', 'ends_at', 'is_active', 'pass_price_gems')
    list_filter = ('is_active',)
    inlines = [SeasonLevelInline]


@admin.register(UserSeasonPass)
class UserSeasonPassAdmin(admin.ModelAdmin):
    list_display = ('user', 'season', 'has_pass', 'season_xp')
    list_filter = ('season', 'has_pass')


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ('period', 'rank', 'user', 'xp', 'computed_at')
    list_filter = ('period',)


@admin.register(PetSpecies)
class PetSpeciesAdmin(admin.ModelAdmin):
    list_display = ('name', 'emoji', 'rarity', 'product_slug')


@admin.register(UserPet)
class UserPetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'user', 'level', 'is_active', 'last_fed_at')
    list_filter = ('species', 'is_active', 'level')
    search_fields = ('name', 'user__username')
