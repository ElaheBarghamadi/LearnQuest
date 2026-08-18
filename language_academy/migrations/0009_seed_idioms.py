from django.db import migrations


def seed_idioms(apps, schema_editor):
    Idiom = apps.get_model('language_academy', 'Idiom')
    from language_academy.idiom_bank import IDIOMS
    for level, expression, fa, definition, example, topic in IDIOMS:
        Idiom.objects.update_or_create(
            expression=expression, level=level,
            defaults=dict(translation_fa=fa, definition_en=definition,
                          example_en=example, topic=topic, is_active=True))


def unseed_idioms(apps, schema_editor):
    Idiom = apps.get_model('language_academy', 'Idiom')
    from language_academy.idiom_bank import IDIOMS
    Idiom.objects.filter(expression__in={i[1] for i in IDIOMS}).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('language_academy', '0008_aichallenge_idiom_placementattempt_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_idioms, unseed_idioms),
    ]
