from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_FRAME = '<rect x="3.5" y="3.5" width="17" height="17" rx="5.5"/><circle cx="12" cy="9.6" r="2.7"/><path d="M6.8 16.9c1.3-2.3 3-3.5 5.2-3.5s3.9 1.2 5.2 3.5"/>'
_PALETTE = '<path d="M12 3a9 9 0 1 0 0 18c1.1 0 2-.9 2-2 0-.5-.2-1-.6-1.4-.3-.4-.5-.8-.5-1.3 0-1.1.9-2 2-2h1.6a3.5 3.5 0 0 0 3.5-3.5C19.6 6.3 16.1 3 12 3z"/><circle cx="7.8" cy="10.4" r="1.1"/><circle cx="11" cy="7.2" r="1.1"/><circle cx="15.1" cy="8.2" r="1.1"/>'
_SUN = '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2.5 12h2M19.5 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'
_MOON = '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>'
_MEDAL = '<circle cx="12" cy="14" r="5.2"/><path d="M12 11.6l.9 1.7 1.9.3-1.4 1.3.3 1.9-1.7-.9-1.7.9.3-1.9-1.4-1.3 1.9-.3z" fill="currentColor" stroke="none"/><path d="m8.7 9.6-2.9-5.4h4L12 8l2.2-3.8h4l-2.9 5.4"/>'
_TAG = '<path d="M3.5 12 12 3.5h8.5V12L12 20.5z"/><circle cx="16.2" cy="7.8" r="1.4"/>'
_SPARKLES = '<path d="M11 3.5 12.8 9l5.7 1.8-5.7 1.8L11 18l-1.8-5.4L3.5 10.8 9.2 9z"/><path d="M18.2 14.5l.8 2.3 2.3.8-2.3.8-.8 2.3-.8-2.3-2.3-.8 2.3-.8z"/>'
_FLAME = '<path d="M12 22c4.4 0 7.5-2.9 7.5-7.2 0-3.1-1.8-5.3-3.6-7.4C14.4 5.6 13 4 13 2c-3 2-4.6 4.5-4.6 7.3 0 1.4.4 2.6 1 3.7-1.3-.3-2.4-1.2-2.9-2.5-1.2 1.5-2 3.3-2 4.8C3.5 19.1 7.6 22 12 22z"/>'
_IMAGE = '<rect x="3" y="5" width="18" height="14" rx="3"/><circle cx="9" cy="10" r="1.8"/><path d="m4.5 17.5 4.5-4.5 3 3 3.5-3.5 4 4"/>'
_SMILEY = '<circle cx="12" cy="12" r="8.5"/><path d="M8.4 14.4c.9 1.2 2.1 1.9 3.6 1.9s2.7-.7 3.6-1.9"/><circle cx="9" cy="9.8" r="1" fill="currentColor" stroke="none"/><circle cx="15" cy="9.8" r="1" fill="currentColor" stroke="none"/>'
_STICKER = '<path d="M5.5 3.5h13a2 2 0 0 1 2 2V13l-7.5 7.5H5.5a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2z"/><path d="M20.5 13H13v7.5"/>'
_MUSIC = '<path d="M9 18V5.5L21 3v13.5"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="18.5" cy="16.5" r="2.5"/>'
_BOOK = '<path d="M2 4.5h6.5A3.5 3.5 0 0 1 12 8v12.5a3 3 0 0 0-3-3H2z"/><path d="M22 4.5h-6.5A3.5 3.5 0 0 0 12 8v12.5a3 3 0 0 1 3-3h7z"/>'
_ABC = '<path d="M3.5 19 8 5l4.5 14"/><path d="M5.3 14h5.4"/><path d="M15.5 19v-8"/><path d="M15.5 14.4c.6-1 1.6-1.5 2.7-1.5 1.6 0 2.6 1.1 2.6 3s-1 3-2.6 3c-1.1 0-2.1-.5-2.7-1.5"/>'
_HEADPHONES = '<path d="M4 14.5a8 8 0 0 1 16 0"/><rect x="3" y="13.5" width="4" height="6.5" rx="2"/><rect x="17" y="13.5" width="4" height="6.5" rx="2"/>'
_MIC = '<rect x="9" y="2.5" width="6" height="11" rx="3"/><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0"/><path d="M12 18v3.5M9 21.5h6"/>'
_PEN = '<path d="M12 20h9"/><path d="M16.4 3.6a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>'
_PAW = '<ellipse cx="7" cy="8" rx="1.7" ry="2.2"/><ellipse cx="12" cy="6.3" rx="1.7" ry="2.2"/><ellipse cx="17" cy="8" rx="1.7" ry="2.2"/><path d="M12 11.5c-3 0-5.5 2.3-5.5 5 0 1.7 1.2 3 3 3 1 0 1.6-.5 2.5-.5s1.5.5 2.5.5c1.8 0 3-1.3 3-3 0-2.7-2.5-5-5.5-5z"/>'
_SHIRT = '<path d="M15.8 3.5 21 6l-1.5 4-2-.8v10.8h-11V9.2l-2 .8L3 6l5.2-2.5a3.8 3.8 0 0 0 7.6 0z"/>'
_BOWTIE = '<path d="M3.5 6.5 11 10.5l-7.5 4zM20.5 6.5 13 10.5l7.5 4z"/><circle cx="12" cy="10.5" r="1.8"/>'
_BOLT = '<path d="M13 2 4.5 13.5H11L9.5 22 19 9.5h-6.5z"/>'
_COINS = '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>'
_GIFT = '<rect x="3.5" y="8" width="17" height="4" rx="1.5"/><path d="M5.5 12v7A1.5 1.5 0 0 0 7 20.5h10a1.5 1.5 0 0 0 1.5-1.5v-7"/><path d="M12 8v12.5"/><path d="M12 8c-1.5 0-4.5-.5-4.5-2.75C7.5 3.5 9.5 3 10.5 3.8 11.7 4.8 12 8 12 8zm0 0c1.5 0 4.5-.5 4.5-2.75 0-1.75-2-2.25-3-1.45C12.3 4.8 12 8 12 8z"/>'
_WHEEL = '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.5"/><path d="M12 3.5v6M12 14.5v6M3.5 12h6M14.5 12h6M5.9 5.9l4.3 4.3M13.8 13.8l4.3 4.3M18.1 5.9l-4.3 4.3M10.2 13.8l-4.3 4.3"/>'
_BULB = '<path d="M9 18h6M10 21.5h4"/><path d="M12 2.5a6 6 0 0 0-3.5 10.9c.8.7 1.3 1.5 1.5 2.6h4c.2-1.1.7-1.9 1.5-2.6A6 6 0 0 0 12 2.5z"/>'
_RETRY = '<path d="M20 11A8 8 0 0 0 5.6 6.6L4 8.5"/><path d="M4 3.5v5h5"/><path d="M4 13a8 8 0 0 0 14.4 4.4L20 15.5"/><path d="M20 20.5v-5h-5"/>'
_CLOCK = '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/>'
_HEART = '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'
_CROWN = '<path d="m3 8 4.5 4L12 5l4.5 7L21 8l-1.6 10.5H4.6z"/><path d="M6.5 21.5h11"/>'
_GAMEPAD = '<rect x="2" y="8" width="20" height="9" rx="4.5"/><path d="M7.2 11.2v3M5.7 12.7h3"/><circle cx="15.6" cy="12" r="1" fill="currentColor" stroke="none"/><circle cx="18" cy="13.7" r="1" fill="currentColor" stroke="none"/>'
_CERT = '<rect x="3.5" y="4" width="17" height="12" rx="2"/><path d="M7 8h7M7 11h9"/><circle cx="17" cy="15" r="2.8"/><path d="M15.6 17 15 21l2-1.3L19 21l-.6-4"/>'
_STARBOOK = '<path d="M2 4.5h6.5A3.5 3.5 0 0 1 12 8v12.5a3 3 0 0 0-3-3H2z"/><path d="M22 4.5h-6.5A3.5 3.5 0 0 0 12 8v12.5a3 3 0 0 1 3-3h7z"/><path d="M12 10.5l.9 1.8 2 .3-1.4 1.4.3 2-1.8-1-1.8 1 .3-2-1.4-1.4 2-.3z" fill="currentColor" stroke="none"/>'
_FLAG = '<path d="M5 3v18"/><path d="M5 4.5c4-2.5 6.5 2 11 0v9c-4.5 2-7-2.5-11 0"/>'
_BOX = '<path d="m12 2.8 8.5 4.2v10L12 21.2 3.5 17V7z"/><path d="M3.5 7 12 11.2 20.5 7"/><path d="M12 11.2v10"/>'

_ICON_MAP = [
    (('frame_animated', 'frame'), _FRAME),
    (('username_color',), _PALETTE),
    (('theme_dark_variant',), _MOON),
    (('theme',), _SUN),
    (('badge',), _MEDAL),
    (('title',), _TAG),
    (('profile_effect',), _SPARKLES),
    (('profile_card_animated',), _FLAME),
    (('profile_background', 'wallpaper_pack'), _IMAGE),
    (('emoji_pack',), _SMILEY),
    (('sticker_pack',), _STICKER),
    (('music_pack', 'listening_pack'), _HEADPHONES),
    (('grammar_pack', 'vocabulary_pack'), _BOOK),
    (('speaking_pack', 'pronunciation_pack'), _MIC),
    (('writing_pack',), _PEN),
    (('pet_skin',), _SHIRT),
    (('pet_accessory',), _BOWTIE),
    (('pet',), _PAW),
    (('xp_booster',), _BOLT),
    (('coin_booster',), _COINS),
    (('mystery_box',), _GIFT),
    (('lucky_spin',), _WHEEL),
    (('hint_ticket',), _BULB),
    (('retry_ticket',), _RETRY),
    (('time_extension',), _CLOCK),
    (('extra_hearts',), _HEART),
    (('season_pass',), _CROWN),
    (('exclusive_minigame',), _GAMEPAD),
    (('certificate_special',), _CERT),
    (('exclusive_lesson',), _STARBOOK),
    (('exclusive_chapter',), _FLAG),
    (('bundle',), _BOX),
    (('abc',), _ABC),
]


def icon_inner(effect_type):
    et = (effect_type or '').strip()
    for keys, svg in _ICON_MAP:
        if et in keys:
            return svg
    return _GIFT


@register.filter
def effect_icon(effect_type):
    return mark_safe(
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>' % icon_inner(effect_type)
    )
