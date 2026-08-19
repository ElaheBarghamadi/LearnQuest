"""پاک‌سازی ارجاع‌های رسانه‌ای که فایل‌شان روی دیسک نیست.

برخی عکس‌ها (مثلاً واژگان) در محیط دیگری آپلود شده‌اند و چون پوشهٔ media
در گیت نیست، روی سیستم شما فایل ندارند و 404 می‌دهند. این اسکریپت همهٔ
فیلدهای ImageField/FileField را چک می‌کند و ارجاع‌های شکسته را خالی می‌کند.

اجرا:  python scripts/fix_missing_media.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
import django
django.setup()

from django.apps import apps
from django.core.files.storage import default_storage

fixed = 0
checked = 0
warned = []

for model in apps.get_models():
    file_fields = [
        (f.name, f) for f in model._meta.fields
        if getattr(f, 'get_internal_type', lambda: '')() in ('FileField', 'ImageField')
    ]
    if not file_fields:
        continue
    for obj in model.objects.all().iterator():
        for fname, field in file_fields:
            value = getattr(obj, fname, None)
            if not value:
                continue
            checked += 1
            try:
                exists = default_storage.exists(value.name)
            except Exception:
                exists = False
            if not exists:
                if field.null:
                    setattr(obj, fname, None)
                    obj.save(update_fields=[fname])
                    fixed += 1
                    print(f'  🔧 {model.__name__}#{obj.pk} — {fname}: {value.name}')
                else:
                    warned.append(f'{model.__name__}#{obj.pk}.{fname} = {value.name} (غیرقابل حذف)')

print(f'\nبررسی شد: {checked} فایل | پاک‌سازی شد: {fixed}')
if warned:
    print('توجه (فیلدهای اجباری):')
    for w in warned:
        print('  ⚠️', w)
print('✅ پایان')
