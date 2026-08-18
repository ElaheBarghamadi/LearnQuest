from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('language_academy', '0005_lessoncontent_reading_notes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='is_exclusive',
            field=models.BooleanField(default=False, verbose_name='درس ویژه (نیازمند خرید بلیط از فروشگاه)'),
        ),
    ]
