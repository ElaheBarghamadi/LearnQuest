from django.core.management.base import BaseCommand
from django.utils import timezone

from shop.models import Category, Product


def C(name, slug, emoji, order):
    return dict(name=name, slug=slug, emoji=emoji, order=order)


CATEGORIES = [
    C('قاب پروفایل', 'frames', '🖼️', 1),
    C('تم و ظاهر', 'themes', '🎨', 2),
    C('رنگ نام کاربری', 'username-colors', '🌈', 3),
    C('نشان و عنوان', 'badges-titles', '🎖️', 4),
    C('افکت پروفایل', 'profile-effects', '✨', 5),
    C('پس‌زمینه و والپیپر', 'backgrounds', '🌄', 6),
    C('شکلک و استیکر', 'emoji-stickers', '😀', 7),
    C('موسیقی و تمرکز', 'music', '🎵', 8),
    C('پک‌های آموزشی', 'edu-packs', '📚', 9),
    C('پت مجازی', 'pets', '🐾', 10),
    C('اکسسوری پت', 'pet-accessories', '🎀', 11),
    C('بوسترها', 'boosters', '⚡', 12),
    C('شانس و جایزه', 'luck', '🎁', 13),
    C('بلیط‌های کمکی', 'tickets', '🎫', 14),
    C('بازکننده محتوا', 'unlocks', '🔓', 15),
    C('بسته‌ها', 'bundles', '📦', 16),
]


def P(slug, name, cat, ptype, effect, payload, coins=0, gems=0, emoji='🎁', desc='',
      featured=False, discount=0, stock=None, per_user=None):
    """Product factory. If `per_user` is None it is auto-computed from
    `effect` so every cosmetic/unlock defaults to per_user_limit=1 and
    every booster/consumable stays repeatable."""
    if per_user is None:
        # keep in sync with shop/management/commands/normalize_limits.py
        one_time = {
            'frame', 'frame_animated',
            'theme', 'theme_dark_variant',
            'username_color',
            'badge', 'title',
            'profile_background',
            'profile_effect', 'profile_card_animated',
            'pet_skin', 'pet_accessory',
            'wallpaper_pack',
            'pet', 'season_pass',
            'exclusive_lesson', 'exclusive_minigame',
            'vocabulary_pack', 'grammar_pack', 'listening_pack', 'speaking_pack',
            'writing_pack', 'pronunciation_pack', 'music_pack',
            'sticker_pack', 'emoji_pack',
            'certificate_special',
        }
        per_user = 1 if effect in one_time else 0
    return dict(slug=slug, name=name, category=cat, product_type=ptype, effect_type=effect,
                effect_payload=payload, price_coins=coins, price_gems=gems,
                preview_emoji=emoji, description=desc, is_featured=featured,
                discount_percent=discount, stock_limit=stock, per_user_limit=per_user)


PRODUCTS = [

    P('frame-gold', 'قاب طلایی', 'frames', 'cosmetic', 'frame', {'css_class': 'frame-gold'},
      coins=500, emoji='🟡', desc='قابی درخشان برای پروفایل حرفه‌ای‌ها.', featured=True),
    P('frame-ice', 'قاب یخی', 'frames', 'cosmetic', 'frame', {'css_class': 'frame-ice'},
      coins=450, emoji='🧊', desc='حال و هوای سرد و خاص برای آواتار تو.'),
    P('frame-emerald', 'قاب زمردی', 'frames', 'cosmetic', 'frame', {'css_class': 'frame-emerald'},
      coins=600, emoji='💚', desc='سبز زمردی روی پروفایل.'),
    P('frame-fire', 'قاب آتشین انیمیشنی', 'frames', 'cosmetic', 'frame_animated', {'css_class': 'frame-fire'},
      gems=8, emoji='🔥', desc='قاب انیمیشنی آتشین؛ فقط برای شجاع‌ها!'),
    P('frame-rainbow', 'قاب رنگین‌کمان چرخان', 'frames', 'cosmetic', 'frame_animated', {'css_class': 'frame-rainbow'},
      gems=15, emoji='🌈', desc='چرخش کامل رنگ‌ها دور آواتارت.', featured=True),
    P('frame-royal', 'قاب سلطنتی (نسخهٔ محدود)', 'frames', 'cosmetic', 'frame', {'css_class': 'frame-royal'},
      gems=12, emoji='👑', desc='نسخهٔ محدود — فقط ۱۰۰ نسخه در کل فروشگاه!', stock=100, per_user=1),


    P('theme-dark', 'تم تیره حرفه‌ای', 'themes', 'cosmetic', 'theme', {'css_class': 'theme-dark'},
      coins=300, emoji='🌙', desc='تم تیرهٔ راحت برای مطالعهٔ شبانه.'),
    P('theme-dark-blue', 'تم تیره آبی', 'themes', 'cosmetic', 'theme_dark_variant', {'css_class': 'theme-dark'},
      coins=350, emoji='🌌', desc='گونهٔ آبی تم تیره.'),
    P('theme-ocean', 'تم اقیانوس', 'themes', 'cosmetic', 'theme', {'css_class': 'theme-ocean'},
      coins=350, emoji='🌊', desc='موج و آب برای آرامش ذهن.'),
    P('theme-forest', 'تم جنگل', 'themes', 'cosmetic', 'theme', {'css_class': 'theme-forest'},
      coins=350, emoji='🌲', desc='سبز طبیعتِ جنگل.'),
    P('theme-sunset', 'تم غروب', 'themes', 'cosmetic', 'theme', {'css_class': 'theme-sunset'},
      coins=400, emoji='🌇', desc='رنگ‌های گرم غروب آفتاب.', featured=True),


    P('ucolor-gold', 'نام کاربری طلایی', 'username-colors', 'cosmetic', 'username_color', {'css_class': 'ucolor-gold'},
      coins=250, emoji='🟡', desc='نامت را طلایی کن.'),
    P('ucolor-ocean', 'نام کاربری آبی اقیانوس', 'username-colors', 'cosmetic', 'username_color', {'css_class': 'ucolor-ocean'},
      coins=200, emoji='🔵', desc='آبی عمیق و کلاس.'),
    P('ucolor-toxic', 'نام کاربری نئون سمی', 'username-colors', 'cosmetic', 'username_color', {'css_class': 'ucolor-toxic'},
      coins=220, emoji='🟢', desc='سبز نئونی برق‌دار.'),
    P('ucolor-rose', 'نام کاربری رز', 'username-colors', 'cosmetic', 'username_color', {'css_class': 'ucolor-rose'},
      coins=220, emoji='🌹', desc='صورتی قرمزِ جذاب.'),
    P('ucolor-royal', 'نام کاربری سلطنتی', 'username-colors', 'cosmetic', 'username_color', {'css_class': 'ucolor-royal'},
      gems=6, emoji='🟣', desc='بنفش سلطنتی با ابهت.'),
    P('ucolor-rainbow', 'نام کاربری رنگین‌کمان', 'username-colors', 'cosmetic', 'username_color', {'css_class': 'ucolor-rainbow'},
      gems=10, emoji='🌈', desc='هر حرف یک رنگ! خاص‌ترین نام سرور.', featured=True),


    P('badge-star', 'نشان ستاره برنزی', 'badges-titles', 'cosmetic', 'badge', {'css_class': 'badge-featured', 'label': '⭐ ستاره'},
      coins=200, emoji='⭐', desc='نشان برنزی برای پروفایل.'),
    P('badge-limited', 'نشان قهرمان محدود', 'badges-titles', 'cosmetic', 'badge', {'css_class': 'badge-limited', 'label': '🏆 قهرمان'},
      gems=8, emoji='🏆', desc='نشان ویژهٔ قهرمانان.'),
    P('title-star-student', 'عنوان «دانشجوی ستاره»', 'badges-titles', 'cosmetic', 'title', {'label': 'دانشجوی ستاره 🌟'},
      coins=300, emoji='🌟', desc='زیر نامت این عنوان نمایش داده می‌شود.'),
    P('title-language-master', 'عنوان «استاد زبان»', 'badges-titles', 'cosmetic', 'title', {'label': 'استاد زبان 🗣️'},
      gems=8, emoji='🗣️', desc='عنوان اختصاصی زبان‌آموزان برتر.'),


    P('effect-sparkle', 'افکت جرقه پروفایل', 'profile-effects', 'cosmetic', 'profile_effect', {'css_class': 'effect-sparkle'},
      gems=5, emoji='✨', desc='آواتارت می‌درخشد.'),
    P('effect-crown', 'افکت تاج', 'profile-effects', 'cosmetic', 'profile_effect', {'css_class': 'effect-crown'},
      gems=9, emoji='👑', desc='تاج سلطنت بالای آواتار.'),
    P('effect-flame', 'افکت شعلهٔ متحرک', 'profile-effects', 'cosmetic', 'profile_card_animated', {'css_class': 'effect-flame'},
      gems=7, emoji='🔥', desc='شعلهٔ انیمیشنی کنار آواتار.', featured=True),


    P('pbg-gradient', 'پس‌زمینهٔ گرادیان بنفش', 'backgrounds', 'cosmetic', 'profile_background', {'css_class': 'pbg-gradient'},
      coins=200, emoji='🟪', desc='گرادیان جذاب برای کارت پروفایل.'),
    P('pbg-sakura', 'پس‌زمینهٔ شکوفه‌های بهاری', 'backgrounds', 'cosmetic', 'profile_background', {'css_class': 'pbg-sakura'},
      coins=250, emoji='🌸', desc='تم بهاریِ لطیف.'),
    P('pbg-space', 'پس‌زمینهٔ فضایی', 'backgrounds', 'cosmetic', 'profile_background', {'css_class': 'pbg-space'},
      gems=6, emoji='🚀', desc='کهکشان روی پروفایل تو.', featured=True),
    P('wallpaper-pack-1', 'پک والپیپر مینیمال (۱۰ تایی)', 'backgrounds', 'cosmetic', 'wallpaper_pack', {'css_class': 'pbg-gradient'},
      coins=300, emoji='🖼️', desc='۱۰ والپیپر مینیمال برای پروفایل.'),


    P('emoji-pack-fun', 'پک شکلک‌های فان', 'emoji-stickers', 'unlock', 'emoji_pack', {'pack': 'fun'},
      coins=150, emoji='😜', desc='۵۰ شکلک فان برای پیامرسان.'),
    P('sticker-pack-study', 'پک استیکر درسی', 'emoji-stickers', 'unlock', 'sticker_pack', {'pack': 'study'},
      coins=180, emoji='📚', desc='۳۰ استیکر انگیزشیِ درس و مطالعه.'),


    P('music-pack-focus', 'پک موسیقی تمرکز', 'music', 'unlock', 'music_pack', {'pack': 'focus'},
      coins=250, emoji='🎧', desc='۱۰ قطعه موسیقی بدون کلام برای تمرکز عمیق.'),


    P('pack-grammar-a2', 'پک گرامر پیشرفته A2', 'edu-packs', 'unlock', 'grammar_pack', {'level': 'A2'},
      coins=350, emoji='📐', desc='گرامر A2 با تمرین‌های تعاملی.'),
    P('pack-vocab-travel', 'پک لغات سفر (۳۰۰ کلمه)', 'edu-packs', 'unlock', 'vocabulary_pack', {'topic': 'travel'},
      coins=350, emoji='✈️', desc='۳۰۰ لغت ضروری سفر.'),
    P('pack-listening-daily', 'پک شنیداری مکالمات روزمره', 'edu-packs', 'unlock', 'listening_pack', {'topic': 'daily'},
      gems=6, emoji='🎙️', desc='فایل‌های شنیداری واقعی با تمرین.'),
    P('pack-speaking-ai', 'پک مکالمه با تمرین تلفظ', 'edu-packs', 'unlock', 'speaking_pack', {'topic': 'pron'},
      gems=8, emoji='🗣️', desc='تمرین مکالمه و تلفظ.'),
    P('pack-writing-essay', 'پک نگارش مقاله', 'edu-packs', 'unlock', 'writing_pack', {'topic': 'essay'},
      coins=400, emoji='✍️', desc='از پاراگراف تا مقالهٔ کامل.'),
    P('pack-pronunciation', 'پک تلفظ استاندارد', 'edu-packs', 'unlock', 'pronunciation_pack', {'topic': 'standard'},
      coins=380, emoji='🔊', desc='تلفظ مثل نیتیو!'),


    P('pet-chick', 'جوجه 🐤', 'pets', 'unlock', 'pet', {},
      coins=800, emoji='🐤', desc='اولین پتت! غذایش بده تا بزرگ شود.', featured=True, per_user=1),
    P('pet-fox', 'روباه 🦊', 'pets', 'unlock', 'pet', {},
      gems=15, emoji='🦊', desc='پت کمیاب و باهوش.', per_user=1),
    P('pet-panda', 'پاندا 🐼', 'pets', 'unlock', 'pet', {},
      gems=25, emoji='🐼', desc='پت حماسی و دوست‌داشتنی.', per_user=1),
    P('pet-dragon', 'اژدهای کوچک 🐲', 'pets', 'unlock', 'pet', {},
      gems=50, emoji='🐲', desc='پت افسانه‌ای — عجله کن دیر نشود!', featured=True, per_user=1),


    P('pet-skin-gold', 'پوستهٔ طلایی پت', 'pet-accessories', 'cosmetic', 'pet_skin', {'css_class': 'effect-sparkle'},
      gems=6, emoji='🌟', desc='پتت را بدرخشان!'),
    P('pet-hat-party', 'کلاه مهمانی پت', 'pet-accessories', 'cosmetic', 'pet_accessory', {'emoji': '🎉'},
      coins=200, emoji='🎩', desc='کلاه بامزهٔ مهمانی.'),
    P('pet-bow-kawaii', 'پاپیون کاوایی', 'pet-accessories', 'cosmetic', 'pet_accessory', {'emoji': '🎀'},
      coins=180, emoji='🎀', desc='پاپیون صورتی ناز.'),


    P('xp-booster-15', 'بوستر XP ×۱٫۵ (۲۴ ساعت)', 'boosters', 'booster', 'xp_booster', {'multiplier': 1.5, 'hours': 24},
      coins=200, emoji='🚀', desc='۲۴ ساعت یک و نیم برابر XP بگیر!', featured=True),
    P('xp-booster-2', 'بوستر XP ×۲ (۱۲ ساعت)', 'boosters', 'booster', 'xp_booster', {'multiplier': 2, 'hours': 12},
      coins=300, emoji='🚀', desc='۱۲ ساعت دوبرابر — برای شب امتحان!'),
    P('coin-booster-15', 'بوستر سکه ×۱٫۵ (۲۴ ساعت)', 'boosters', 'booster', 'coin_booster', {'multiplier': 1.5, 'hours': 24},
      coins=200, emoji='💰', desc='یک و نیم برابر سکه از همهٔ جوایز.'),


    P('mystery-box', 'جعبهٔ مرموز', 'luck', 'consumable', 'mystery_box', {'loot': [
        {'coins': 150, 'weight': 30}, {'coins': 300, 'weight': 20}, {'gems': 3, 'weight': 15},
        {'xp': 100, 'weight': 20}, {'product_slug': 'hint-ticket', 'weight': 8},
        {'product_slug': 'time-card', 'weight': 5}, {'gems': 10, 'weight': 2},
    ]}, coins=150, emoji='🎁', desc='شانست را امتحان کن — از سکه تا الماس!', featured=True),
    P('lucky-spin', 'بلیط گردونهٔ شانس', 'luck', 'consumable', 'lucky_spin', {'loot': [
        {'coins': 50, 'weight': 40}, {'coins': 120, 'weight': 25}, {'xp': 60, 'weight': 20},
        {'gems': 2, 'weight': 10}, {'product_slug': 'extra-hearts', 'weight': 5},
    ]}, coins=100, emoji='🎡', desc='گردونه را بچرخان و جایزه ببر.'),


    P('hint-ticket', 'بلیط راهنمای کوئیز 💡', 'tickets', 'consumable', 'hint_ticket', {},
      coins=60, emoji='💡', desc='در کوئیز دو گزینهٔ غلط را حذف می‌کند.'),
    P('retry-ticket', 'بلیط تلاش مجدد 🎫', 'tickets', 'consumable', 'retry_ticket', {},
      coins=120, emoji='🎫', desc='وقتی تلاش‌های کوئیز تمام شد، یک شانس دیگر!'),
    P('time-card', 'کارت افزایش زمان ⏱', 'tickets', 'consumable', 'time_extension', {'minutes': 5},
      coins=80, emoji='⏱️', desc='+۵ دقیقه به زمان کوئیز.'),
    P('extra-hearts', 'قلب‌های اضافه 💗', 'tickets', 'consumable', 'extra_hearts', {'xp': 20},
      coins=90, emoji='💗', desc='انرژی فوری — مستقیم تبدیل به +۲۰ XP می‌شود'),


    P('season-pass-1', 'سیزن‌پس «بهار دانش» 👑', 'unlocks', 'unlock', 'season_pass', {},
      gems=50, emoji='👑', desc='ردیف جایزهٔ ویژهٔ تمام پله‌های فصل باز می‌شود!', featured=True, per_user=1),
    P('minigame-wordrush', 'مینی‌گیم انحصاری: WordRush', 'unlocks', 'unlock', 'exclusive_minigame', {'game': 'wordrush'},
      coins=300, emoji='🕹️', desc='بازی انحصاری سرعت تایپ کلمات.'),
    P('cert-elite', 'گواهینامهٔ ویژهٔ نخبگان', 'unlocks', 'unlock', 'certificate_special', {'cert': 'elite'},
      gems=12, emoji='🏅', desc='گواهینامهٔ رسمی با طرح طلایی.'),
    P('exclusive-lesson-cafe', 'درس ویژه: مکالمهٔ کافه ☕', 'unlocks', 'unlock', 'exclusive_lesson', {'lesson_id': 0},
      coins=350, emoji='☕', desc='درس انحصاری مکالمهٔ کافه (payload باید به درس واقعی وصل شود).'),
]


class Command(BaseCommand):
    help = 'Seed shop: categories + ~40 sample products'

    def handle(self, *args, **options):
        cats = {}
        for c in CATEGORIES:
            obj, _ = Category.objects.update_or_create(slug=c['slug'], defaults=c)
            cats[c['slug']] = obj
        self.stdout.write(f'  📂 دسته‌بندی‌ها: {len(cats)}')

        n_new = 0
        for p in PRODUCTS:
            data = dict(p)
            data['category'] = cats[data['category']]
            slug = data.pop('slug')
            obj, created = Product.objects.update_or_create(slug=slug, defaults=data)
            n_new += created
        self.stdout.write(f'  🛍 محصولات: {len(PRODUCTS)} (تازه: {n_new})')


        self._bundle()
        self._fix_exclusive_lesson()
        self.stdout.write(self.style.SUCCESS('✅ seed_shop کامل شد'))

    def _bundle(self):
        bundle, _ = Product.objects.update_or_create(
            slug='starter-bundle',
            defaults=dict(
                name='باندل شروع قدرتمند 💪', category=Category.objects.get(slug='bundles'),
                product_type='bundle', effect_type='bundle', effect_payload={},
                price_coins=900, discount_percent=20, preview_emoji='📦', is_featured=True,
                description='قاب طلایی + نام طلایی + بوستر XP + جعبهٔ مرموز — ۲۰٪ تخفیف!'))
        items = Product.objects.filter(slug__in=['frame-gold', 'ucolor-gold', 'xp-booster-15', 'mystery-box'])
        bundle.bundle_items.set(items)
        self.stdout.write('  📦 باندل شروع قدرتمند')

    def _fix_exclusive_lesson(self):
        from language_academy.models import Lesson

        targets = {
            'exclusive-lesson-cafe': 'Cafe Conversation',
            'exclusive-lesson-business-travel': 'Business Travel Pro',
        }
        for slug, lname in targets.items():
            lesson = Lesson.objects.filter(name__icontains=lname).first()
            if not lesson:
                continue
            if not lesson.is_exclusive:
                lesson.is_exclusive = True
                lesson.save(update_fields=['is_exclusive'])
            Product.objects.filter(slug=slug).update(
                effect_payload={'lesson_id': lesson.id},
                name=f'بلیط درس ویژه: {lesson.name}')
            self.stdout.write(f'  🔓 بلیط «{slug}» به درس #{lesson.id} وصل شد')

        ticketed = set()
        for p in Product.objects.filter(is_active=True, effect_type='exclusive_lesson'):
            lid = (p.effect_payload or {}).get('lesson_id')
            if lid:
                ticketed.add(lid)
        stale = Lesson.objects.filter(is_exclusive=True).exclude(pk__in=ticketed)
        healed = stale.update(is_exclusive=False)
        if healed:
            self.stdout.write(f'  🩹 {healed} درس اشتباهاً علامت‌خورده آزاد شد')
        for l in Lesson.objects.filter(pk__in=ticketed, is_exclusive=False):
            l.is_exclusive = True
            l.save(update_fields=['is_exclusive'])

        disabled = Product.objects.filter(effect_type='exclusive_chapter', is_active=True).update(is_active=False)
        if disabled:
            self.stdout.write(f'  🎟 {disabled} بلیط فصل غیرفعال شد (اکادمی رایگان است)')
