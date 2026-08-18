from django.db import migrations


def heal_academy_access(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    Lesson = apps.get_model('language_academy', 'Lesson')

    Product.objects.filter(effect_type='exclusive_chapter').update(is_active=False)

    ticketed = set()
    for payload in Product.objects.filter(
            is_active=True, effect_type='exclusive_lesson').values_list('effect_payload', flat=True):
        lid = (payload or {}).get('lesson_id') if isinstance(payload, dict) else None
        if lid:
            ticketed.add(lid)

    Lesson.objects.filter(is_exclusive=True).exclude(pk__in=ticketed).update(is_exclusive=False)
    if ticketed:
        Lesson.objects.filter(pk__in=ticketed, is_exclusive=False).update(is_exclusive=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
        ('language_academy', '0006_lesson_is_exclusive'),
    ]

    operations = [
        migrations.RunPython(heal_academy_access, noop),
    ]
