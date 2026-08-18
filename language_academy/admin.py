from django.contrib import admin

from .models import (AIChallenge, Idiom, PlacementAttempt, UserLanguageEstimate)


@admin.register(Idiom)
class IdiomAdmin(admin.ModelAdmin):
    list_display = ('expression', 'level', 'topic', 'is_active')
    list_filter = ('level', 'topic', 'is_active')
    search_fields = ('expression', 'translation_fa')


@admin.register(UserLanguageEstimate)
class UserLanguageEstimateAdmin(admin.ModelAdmin):
    list_display = ('user', 'cefr_level', 'source', 'updated_at')
    list_filter = ('cefr_level', 'source')


@admin.register(PlacementAttempt)
class PlacementAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'chosen_level', 'score', 'verdict', 'recommended_level', 'used_ai', 'created_at')
    list_filter = ('chosen_level', 'verdict')


@admin.register(AIChallenge)
class AIChallengeAdmin(admin.ModelAdmin):
    list_display = ('user', 'source', 'is_correct', 'xp_awarded', 'created_at')
    list_filter = ('source', 'is_correct')
