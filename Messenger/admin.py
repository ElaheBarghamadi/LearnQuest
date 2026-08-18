from django.contrib import admin, messages as admin_messages
from django.utils.html import format_html

from .models import BlockedUser, Conversation, Message


class ParticipantInline(admin.TabularInline):
    model = Conversation.participants.through
    extra = 0
    verbose_name = 'عضو'
    verbose_name_plural = 'اعضای مکالمه'
    can_delete = True


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    max_num = 15
    ordering = ('-created_at',)
    fields = ('sender', 'preview', 'created_at', 'is_read')
    readonly_fields = ('sender', 'preview', 'created_at', 'is_read')
    verbose_name = 'پیام'
    verbose_name_plural = 'آخرین پیام‌ها (رمزگشایی‌شده)'
    can_delete = False

    @admin.display(description='متن پیام 🔓')
    def preview(self, obj):
        txt = obj.get_content()
        return txt[:40] + ('…' if len(txt) > 40 else '')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title_col', 'kind_col', 'owner_col', 'members_col',
                    'messages_col', 'unread_col', 'updated_at')
    list_filter = ('is_group', 'created_at', 'updated_at')
    search_fields = ('name', 'participants__username', 'created_by__username')
    date_hierarchy = 'created_at'
    inlines = [ParticipantInline, MessageInline]
    actions = ['action_regenerate_invite', 'action_delete_empty']
    readonly_fields = ('kind_col', 'members_col', 'messages_col', 'invite_display')

    fieldsets = (
        ('مشخصات', {'fields': ('name', 'is_group', 'created_by', 'kind_col')}),
        ('لینک دعوت', {'fields': ('invite_display', 'invite_token'),
                       'classes': ('collapse',)}),
        ('آمار', {'fields': ('members_col', 'messages_col'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('participants', 'messages')

    @admin.display(description='عنوان')
    def title_col(self, obj):
        if obj.is_group:
            return f'👥 {obj.name or "گروه بدون‌نام"}'
        names = [u.username for u in obj.participants.all()[:2]]
        return '💬 ' + ' ↔ '.join(names)

    @admin.display(description='نوع')
    def kind_col(self, obj):
        if obj.is_group:
            return format_html('<span style="background:#fef3c7;color:#b45309;border-radius:8px;padding:2px 9px;font-weight:700">گروه</span>')
        return format_html('<span style="background:#e0f2fe;color:#0369a1;border-radius:8px;padding:2px 9px;font-weight:700">دونفره</span>')

    @admin.display(description='مدیر')
    def owner_col(self, obj):
        return obj.created_by or '—'

    @admin.display(description='اعضا')
    def members_col(self, obj):
        return obj.participants.count()

    @admin.display(description='پیام‌ها')
    def messages_col(self, obj):
        return obj.messages.count()

    @admin.display(description='نخوانده')
    def unread_col(self, obj):
        n = obj.messages.filter(is_read=False).count()
        if n:
            return format_html('<span style="background:#fee2e2;color:#b91c1c;border-radius:8px;padding:2px 8px;font-weight:700">{}</span>', n)
        return '۰'

    @admin.display(description='لینک دعوت')
    def invite_display(self, obj):
        if obj.is_group and obj.invite_token:
            url = f'/messenger/join/{obj.invite_token}/'
            return format_html('<a href="{}" target="_blank" style="direction:ltr">{}</a>', url, url)
        return '— (فقط برای گروه)'

    @admin.action(description='🔗 بازتولید لینک دعوت گروه‌های انتخابی')
    def action_regenerate_invite(self, request, queryset):
        n = 0
        for conv in queryset.filter(is_group=True):
            conv.invite_token = None
            conv.save()
            n += 1
        self.message_user(request, f'لینک دعوت {n} گروه بازتولید شد (لینک‌های قبلی بی‌اعتبار شدند).',
                          admin_messages.SUCCESS)

    @admin.action(description='🧹 حذف گروه‌های بدون عضو')
    def action_delete_empty(self, request, queryset):
        n = 0
        for conv in queryset:
            if conv.participants.count() == 0:
                conv.delete()
                n += 1
        self.message_user(request, f'{n} مکالمهٔ خالی حذف شد.', admin_messages.WARNING)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conv_col', 'preview_col', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'conversation__name')
    date_hierarchy = 'created_at'
    list_select_related = ('sender', 'conversation')
    readonly_fields = [f.name for f in Message._meta.fields] + ['content_display']

    fieldsets = (
        ('مشخصات', {'fields': ('conversation', 'sender', 'created_at', 'is_read')}),
        ('متن پیام 🔓 (رمزگشایی‌شده)', {'fields': ('content_display',)}),
    )

    @admin.display(description='مکالمه')
    def conv_col(self, obj):
        conv = obj.conversation
        return f'👥 {conv.name}' if conv.is_group and conv.name else f'💬 #{conv.pk}'

    @admin.display(description='متن 🔓')
    def preview_col(self, obj):
        txt = obj.get_content()
        return txt[:55] + ('…' if len(txt) > 55 else '')

    @admin.display(description='متن کامل پیام')
    def content_display(self, obj):
        return obj.get_content()

    def has_add_permission(self, request):
        return False


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'arrow', 'blocked', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('blocker__username', 'blocked__username')
    date_hierarchy = 'created_at'
    actions = ['action_unblock']

    @admin.display(description='')
    def arrow(self, obj):
        return '⛔'

    @admin.action(description='✔ رفع بلاک موارد انتخابی')
    def action_unblock(self, request, queryset):
        n = queryset.count()
        queryset.delete()
        self.message_user(request, f'{n} بلاک رفع شد.', admin_messages.SUCCESS)
