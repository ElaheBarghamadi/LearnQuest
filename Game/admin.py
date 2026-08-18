from django.contrib import admin


from django.contrib import admin
from .models import UserGameStats, UserAchievement


@admin.register(UserGameStats)
class UserGameStatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'game_name', 'games_played', 'games_completed', 'best_score', 'updated_at')
    list_filter = ('game_name', 'updated_at')

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'game_name')
        }),
        ('آمار بازی', {
            'fields': ('games_played', 'games_completed', 'best_score')
        }),
        ('زمان', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'achievement_type', 'earned_at')
    list_filter = ('achievement_type', 'earned_at')
    search_fields = ( 'name', 'description')
    readonly_fields = ('earned_at',)

    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('دستاورد', {
            'fields': ('achievement_type', 'name', 'description', 'icon')
        }),
        ('زمان دریافت', {
            'fields': ('earned_at',),
            'classes': ('collapse',)
        }),
    )
