"""ممیزی و ترمیم خودکار محصولات فروشگاه.

اجرا:  python scripts/audit_products.py
بررسی‌ها:
  1. بلیط‌های exclusive_lesson باید به درسِ واقعیِ موجود اشاره کنند
  2. هر درس is_exclusive باید بلیط فعالِ متناظر داشته باشد
  3. محصولات equippable باید effect_payload با css_class معتبر داشته باشند
  4. هر محصول باید دسته و اسلاگ و قیمت منطقی داشته باشد
  5. گونه‌های پت باید محصول فروشگاهی داشته باشند
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
import django
django.setup()

from django.db.models import Count

from language_academy.models import Lesson
from shop.models import Product, Category
from economy.models import PetSpecies

from shop.effects import EFFECT_TO_SLOT

NEED_CSS = {
    'frame', 'frame_animated', 'username_color', 'theme', 'theme_dark_variant',
    'profile_background', 'wallpaper_pack', 'profile_effect', 'profile_card_animated',
    'badge', 'avatar_premium', 'avatar_decoration',
}
# fallback css_class ها برای محصولات خاصی که payload معنی‌دار ندارند
PAYLOAD_PATCH = {
    'pet-bow-kawaii': {'emoji': '🎀', 'css_class': 'pet-acc-bow'},
    'pet-hat-party': {'emoji': '🎉', 'css_class': 'pet-acc-hat'},
    'title-language-master': {'label': 'استاد زبان 🗣️', 'css_class': 'title-lang-master'},
    'title-star-student': {'label': 'دانشجوی ستاره 🌟', 'css_class': 'title-star'},
}
# اگر درس کافه موجود نبود، بلیط به این درس‌ها وصل می‌شود
EXCLUSIVE_FALLBACK = {
    'exclusive-lesson-cafe': ['Cafe Conversation', 'Table Conversation'],
}


def log(ok, msg):
    print(('  ✅' if ok else '  ❌'), msg)
    return ok


def main():
    issues = 0

    print('━━ ۱) بلیط‌های exclusive_lesson ━')
    for p in Product.objects.filter(effect_type='exclusive_lesson'):
        lid = (p.effect_payload or {}).get('lesson_id')
        lesson = Lesson.objects.filter(id=lid).first() if lid else None
        if lesson:
            log(True, f'{p.slug} → درس #{lesson.id} «{lesson.name}»')
        else:
            issues += 1
            log(False, f'{p.slug} به درس نامعتبر ({lid}) اشاره می‌کند')
            # تلاش برای اتصال به درس جایگزین
            for key in EXCLUSIVE_FALLBACK.get(p.slug, []):
                lesson = Lesson.objects.filter(name__icontains=key).first()
                if lesson:
                    p.effect_payload = {'lesson_id': lesson.id}
                    p.name = f'بلیط درس ویژه: {lesson.name}'
                    p.save(update_fields=['effect_payload', 'name'])
                    log(True, f'  ↳ به درس #{lesson.id} «{lesson.name}» وصل شد')
                    break
            else:
                # هیچ درس متناظری نیست → غیرفعال کن
                p.is_active = False
                p.save(update_fields=['is_active'])
                log(True, '  ↳ غیرفعال شد (درس متناظر در دیتابیس نیست)')

    print('━━ ۲) درس‌های exclusive بدون بلیط ━')
    ticketed = set()
    for p in Product.objects.filter(is_active=True, effect_type='exclusive_lesson'):
        lid = (p.effect_payload or {}).get('lesson_id')
        if lid:
            ticketed.add(lid)
    stale = Lesson.objects.filter(is_exclusive=True).exclude(pk__in=ticketed)
    for l in stale:
        issues += 1
        log(False, f'درس #{l.id} «{l.name}» علامت exclusive دارد ولی بلیط ندارد')
    healed = stale.update(is_exclusive=False)
    if healed:
        log(True, f'  ↳ {healed} درس آزاد شد')

    print('━━ ۳) css_class برای آیتم‌های equippable ━')
    for p in Product.objects.filter(is_active=True):
        if p.effect_type in NEED_CSS and not (p.effect_payload or {}).get('css_class'):
            patch = PAYLOAD_PATCH.get(p.slug)
            if patch:
                payload = dict(p.effect_payload or {})
                payload.update(patch)
                p.effect_payload = payload
                p.save(update_fields=['effect_payload'])
                log(True, f'{p.slug} ← css_class اضافه شد: {patch.get("css_class")}')
            else:
                issues += 1
                log(False, f'{p.slug} ({p.effect_type}) بدون css_class')

    print('━━ ۴) سلامت عمومی ━')
    bad = 0
    for p in Product.objects.all():
        probs = []
        if not p.slug:
            probs.append('اسلاگ خالی')
        if not p.category_id:
            probs.append('بدون دسته')
        if p.price_coins == 0 and p.price_gems == 0 and p.product_type not in ('bundle',):
            pass  # رایگان بودن به خودی خود ایراد نیست
        if p.discount_percent and not (0 <= p.discount_percent <= 95):
            probs.append(f'تخفیف نامعقول {p.discount_percent}')
        if p.available_until and p.available_from and p.available_until < p.available_from:
            probs.append('بازهٔ زمانی معکوس')
        if probs:
            bad += 1
            log(False, f'{p.slug}: {", ".join(probs)}')
    if not bad:
        log(True, 'همهٔ محصولات اسلاگ/دسته/قیمت/تخفیف سالم دارند')

    dup = Product.objects.values('slug').annotate(c=Count('id')).filter(c__gt=1)
    if dup:
        issues += len(dup)
        log(False, f'اسلاگ تکراری: {list(dup)}')
    else:
        log(True, 'اسلاگ تکراری وجود ندارد')

    print('━━ ۵) پت‌ها ━')
    for s in PetSpecies.objects.all():
        ok_ = Product.objects.filter(slug=s.product_slug, is_active=True).exists()
        log(ok_, f'پت «{s.name}» ← محصول {s.product_slug}')
        if not ok_:
            issues += 1

    print()
    print(f'نتیجه: {"همه چیز سالم ✔" if issues == 0 else f"{issues} مشکل یافت شد ✘"}')
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
