from django.contrib import admin


from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Word


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):


    list_display = ['english_word', 'persian_meaning', 'level', 'example_preview', 'created_at', 'status_badge']


    search_fields = ['english_word', 'persian_meaning', 'example_sentence']


    list_filter = ['level', 'created_at']


    list_display_links = ['english_word', 'persian_meaning']


    list_editable = ['level']


    list_per_page = 25


    ordering = ['english_word']


    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('english_word', 'persian_meaning', 'level')
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('example_sentence',),
            'classes': ('wide',),
            'description': 'مثال‌های بیشتر برای درک بهتر کلمه'
        }),
        ('زمان', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


    readonly_fields = ['created_at']


    autocomplete_fields = []


    actions = ['make_level_a1', 'make_level_a2', 'make_level_b1', 'delete_selected']

    def example_preview(self, obj):
        if obj.example_sentence:

            preview = obj.example_sentence[:50]
            if len(obj.example_sentence) > 50:
                preview += '...'
            return format_html('<span title="{}">{}</span>', obj.example_sentence, preview)
        return format_html('<span style="color: gray;">---</span>')

    example_preview.short_description = 'مثال'
    example_preview.allow_tags = True

    def status_badge(self, obj):
        colors = {
            'A1': 'green',
            'A2': 'blue',
            'B1': 'orange',
            'B2': 'purple',
            'C1': 'red',
        }
        color = colors.get(obj.level, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_level_display()
        )

    status_badge.short_description = 'سطح'


    def make_level_a1(self, request, queryset):
        updated = queryset.update(level='A1')
        self.message_user(request, f'{updated} کلمه به سطح A1 تغییر یافت.')

    make_level_a1.short_description = 'تغییر سطح به A1 (مبتدی)'

    def make_level_a2(self, request, queryset):
        updated = queryset.update(level='A2')
        self.message_user(request, f'{updated} کلمه به سطح A2 تغییر یافت.')

    make_level_a2.short_description = 'تغییر سطح به A2 (مقدماتی)'

    def make_level_b1(self, request, queryset):
        updated = queryset.update(level='B1')
        self.message_user(request, f'{updated} کلمه به سطح B1 تغییر یافت.')

    make_level_b1.short_description = 'تغییر سطح به B1 (متوسط)'


    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_at = timezone.now()
        super().save_model(request, obj, form, change)


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form


    date_hierarchy = 'created_at'


    preserve_filters = True


    def get_list_display(self, request):
        return self.list_display

    def get_queryset(self, request):
        return super().get_queryset(request)


class WordInline(admin.TabularInline):
    model = Word
    extra = 1
    fields = ['english_word', 'persian_meaning', 'level']
    show_change_link = True
