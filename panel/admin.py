from django.contrib import admin

from .models import PanelAdjustment


@admin.register(PanelAdjustment)
class PanelAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'target', 'amount', 'actor', 'short_note', 'created_at')
    list_filter = ('target', 'created_at')
    search_fields = ('user__username', 'actor__username', 'note')
    readonly_fields = ('created_at', 'idempotency_key')
    ordering = ('-created_at',)

    def short_note(self, obj):
        return (obj.note or '—')[:40]
    short_note.short_description = 'دلیل'
