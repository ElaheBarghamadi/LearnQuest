import datetime as _dt

import jdatetime
from django.utils import timezone

FA_DIGIT_MAP = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

MONTHS_FA = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
]

WEEKDAYS_FA = [
    'شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه',
]


def fa_digits(value) -> str:
    return str(value).translate(FA_DIGIT_MAP)


def _as_local(value):
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        if timezone.is_aware(value):
            return timezone.localtime(value)
        return value
    if isinstance(value, _dt.date):
        return _dt.datetime(value.year, value.month, value.day)
    return None


def to_jdatetime(value):
    value = _as_local(value)
    if value is None:
        return None
    try:
        return jdatetime.datetime.fromgregorian(datetime=value)
    except (ValueError, OverflowError, TypeError):
        return None


def jalali_parts(value):
    j = to_jdatetime(value)
    if j is None:
        return None
    return j.year, j.month, j.day


def jalali_date(value, fa: bool = True) -> str:
    parts = jalali_parts(value)
    if not parts:
        return ''
    y, m, d = parts
    out = f'{y}/{m:02d}/{d:02d}'
    return fa_digits(out) if fa else out


def jalali_date_long(value, fa: bool = True) -> str:
    parts = jalali_parts(value)
    if not parts:
        return ''
    y, m, d = parts
    out = f'{d} {MONTHS_FA[m - 1]} {y}'
    return fa_digits(out) if fa else out


def jalali_time(value, fa: bool = True) -> str:
    value = _as_local(value)
    if value is None:
        return ''
    out = value.strftime('%H:%M')
    return fa_digits(out) if fa else out


def jalali_datetime(value, fa: bool = True) -> str:
    d = jalali_date_long(value, fa=fa)
    t = jalali_time(value, fa=fa)
    if not d:
        return ''
    return f'{d} - {t}' if t else d


def jalali_weekday(value) -> str:
    j = to_jdatetime(value)
    if j is None:
        return ''
    return WEEKDAYS_FA[j.weekday()]


def jalali_human(value, fa: bool = True) -> str:
    j = to_jdatetime(value)
    if j is None:
        return ''
    local_now = timezone.localtime(timezone.now())
    today_parts = jalali_parts(local_now)
    day_label = jalali_date_long(value, fa=fa)
    if today_parts and (j.year, j.month, j.day) == today_parts:
        day_label = 'امروز'
    else:
        yesterday = local_now - _dt.timedelta(days=1)
        y_parts = jalali_parts(yesterday)
        if y_parts and (j.year, j.month, j.day) == y_parts:
            day_label = 'دیروز'
    if day_label in ('امروز', 'دیروز'):
        t = jalali_time(value, fa=fa)
        return f'{day_label} {t}'.strip()
    return day_label


def jalali_day_label(value, fa: bool = True) -> str:
    j = to_jdatetime(value)
    if j is None:
        return ''
    weekday = WEEKDAYS_FA[j.weekday()]
    y, m, d = j.year, j.month, j.day
    out = f'{weekday}، {d} {MONTHS_FA[m - 1]} {y}'
    return fa_digits(out) if fa else out
