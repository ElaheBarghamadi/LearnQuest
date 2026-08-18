from django.db import migrations

DISCOUNTS = {
    'frame-ice': 15,
    'theme-dark': 20,
    'ucolor-ocean': 15,
    'badge-star': 25,
    'title-star-student': 20,
    'wallpaper-pack-1': 30,
    'lucky-spin': 10,
    'mystery-box': 20,
    'sticker-pack-study': 15,
    'emoji-pack-fun': 15,
}

FEATURED = ['starter-bundle', 'mystery-box', 'season-pass-1', 'xp-booster-15']


def forwards(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    for slug, d in DISCOUNTS.items():
        Product.objects.filter(slug=slug, discount_percent=0).update(discount_percent=d)
    Product.objects.filter(slug__in=FEATURED).update(is_featured=True)
    Product.objects.filter(slug='exclusive-lesson-business-travel', preview_emoji='').update(preview_emoji='✈️')
    for p in Product.objects.filter(sold_count=0):
        seed = sum(ord(c) for c in p.slug) + p.pk * 13
        p.sold_count = 8 + seed % 113
        p.save(update_fields=['sold_count'])


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_academy_free_heal'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
