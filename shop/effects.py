from __future__ import annotations


EQUIP_SLOTS = {
    'frame': 'قاب پروفایل',
    'username_color': 'رنگ نام کاربری',
    'theme': 'تم سایت',
    'profile_background': 'پس‌زمینهٔ پروفایل',
    'profile_effect': 'افکت پروفایل',
    'title': 'عنوان نمایشی',
    'badge': 'نشان پروفایل',
    'avatar_premium': 'آواتار ویژه',
    'avatar_decoration': 'تزئینات آواتار',
    'pet_skin': 'پوستهٔ پت',
    'pet_accessory': 'اکسسوری پت',
}


EFFECT_TO_SLOT = {
    'frame': 'frame', 'frame_animated': 'frame',
    'username_color': 'username_color',
    'theme': 'theme', 'theme_dark_variant': 'theme',
    'profile_background': 'profile_background', 'wallpaper_pack': 'profile_background',
    'profile_effect': 'profile_effect', 'profile_card_animated': 'profile_effect',
    'title': 'title',
    'badge': 'badge', 'badge_profile': 'badge',
    'avatar_premium': 'avatar_premium',
    'avatar_decoration': 'avatar_decoration',
    'pet_skin': 'pet_skin',
    'pet_accessory': 'pet_accessory',
}


SLOT_CAPACITY = {'avatar_decoration': 2, 'pet_accessory': 2}


BOUND_CONSUMABLES = {
    'hint_ticket': 'در صفحهٔ کوئیز با دکمهٔ 💡 استفاده می‌شود',
    'retry_ticket': 'وقتی تلاش کوئیز تمام شد، دکمهٔ تلاش دوباره ظاهر می‌شود',
    'time_extension': 'در صفحهٔ کوئیز با دکمهٔ ⏱ استفاده می‌شود',
}


INSTANT_CONSUMABLES = {
    'xp_booster', 'coin_booster', 'mystery_box', 'lucky_spin', 'extra_hearts',
}


PASSIVE_EFFECTS = {
    'emoji_pack', 'sticker_pack', 'music_pack', 'language_pack',
    'grammar_pack', 'vocabulary_pack', 'listening_pack', 'speaking_pack',
    'writing_pack', 'pronunciation_pack', 'exclusive_lesson', 'exclusive_course',
    'exclusive_minigame', 'exclusive_practice_pack', 'certificate_special',
    'season_pass', 'pet', 'exclusive_chapter',
}


def slot_of(effect_type: str) -> str | None:
    return EFFECT_TO_SLOT.get(effect_type)


def is_equippable(effect_type: str) -> bool:
    return slot_of(effect_type) is not None


def is_directly_consumable(effect_type: str) -> bool:
    return effect_type in INSTANT_CONSUMABLES


def bound_note(effect_type: str) -> str | None:
    return BOUND_CONSUMABLES.get(effect_type)
