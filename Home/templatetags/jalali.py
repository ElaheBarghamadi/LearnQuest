from django import template

from Home.jalali import (
    fa_digits,
    jalali_date,
    jalali_date_long,
    jalali_datetime,
    jalali_day_label,
    jalali_human,
    jalali_time,
)

register = template.Library()


@register.filter
def jdate(value):
    return jalali_date(value)


@register.filter
def jdatelong(value):
    return jalali_date_long(value)


@register.filter
def jdatetime(value):
    return jalali_datetime(value)


@register.filter
def jtime(value):
    return jalali_time(value)


@register.filter
def jhuman(value):
    return jalali_human(value)


@register.filter
def jdaylabel(value):
    return jalali_day_label(value)


@register.filter
def fadigits(value):
    try:
        return fa_digits(value)
    except (ValueError, TypeError):
        return value


@register.filter
def hue(value):
    try:
        return (int(value) * 47) % 360
    except (ValueError, TypeError):
        return 212


ICON_EMOJI = {
    'bell': '🔔',
    'star': '⭐',
    'trophy': '🏆',
    'medal': '🏅',
    'crown': '👑',
    'gamepad': '🎮',
    'brain': '🧠',
    'flask': '🧪',
    'guess': '🔮',
    'language': '🗣️',
    'level-up': '🚀',
    'memory': '🧠',
    'puzzle': '🧩',
    'scramble': '🔤',
    'sudoku': '🔢',
    'bolt': '⚡',
    'fire': '🔥',
    'coin': '🪙',
    'gem': '💎',
    'heart': '💜',
    'gift': '🎁',
    'clock': '🕐',
    'calendar': '📅',
    'edit': '✏️',
    'wallet': '👛',
    'cart': '🛒',
    'envelope': '📧',
    'phone': '📱',
}


@register.filter
def icon_emoji(value, fallback='🔔'):
    return ICON_EMOJI.get(str(value or '').strip(), fallback)
