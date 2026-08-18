from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return ''
    if isinstance(dictionary, dict):
        return dictionary.get(str(key), '')
    return ''


@register.filter
def to_letter(value):
    try:
        num = int(value)
        if 1 <= num <= 26:
            return chr(64 + num)
        return str(num)
    except (ValueError, TypeError):
        return ''


@register.filter
@stringfilter
def get_question_type_display(value):
    types = {
        'mcq': 'چند گزینه‌ای',
        'fill_blank': 'جای خالی',
        'matching': 'تطبیق',
        'ordering': 'ترتیب‌دهی',
        'listening': 'درک شنیداری',
        'writing': 'نوشتاری',
        'speaking': 'گفتاری',
        'dialogue': 'دیالوگ',
        'true_false': 'درست / غلط',
    }
    return types.get(value, value)


@register.filter
def format_percentage(value):
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return "0%"


@register.filter
def get_difficulty_badge(value):
    badges = {
        'A1': '<span class="badge bg-success">A1 - مبتدی</span>',
        'A2': '<span class="badge bg-info">A2 - ابتدایی</span>',
        'B1': '<span class="badge bg-warning">B1 - متوسط</span>',
    }
    return badges.get(value, value)


@register.filter
def get_status_badge(value):
    statuses = {
        'not_started': '<span class="badge bg-secondary">شروع نشده</span>',
        'in_progress': '<span class="badge bg-primary">در حال پیشرفت</span>',
        'completed': '<span class="badge bg-success">تکمیل شده</span>',
    }
    return statuses.get(value, value)


@register.filter
def truncate_text(value, length=100):
    if not value:
        return ''
    if len(value) <= length:
        return value
    return value[:length] + '...'


@register.filter
def get_lesson_type_icon(value):
    icons = {
        'vocabulary': '📚',
        'grammar': '📝',
        'dialogue': '💬',
        'reading': '📖',
        'listening': '🎧',
        'writing': '✍️',
        'speaking': '🗣️',
        'mixed': '🎯',
    }
    return icons.get(value, '📖')


@register.filter
def neg(value):
    try:
        return -int(value)
    except (ValueError, TypeError):
        return 0

@register.filter
def time_format(seconds):
    if not seconds:
        return '0:00'
    try:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    except (ValueError, TypeError):
        return '0:00'

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
