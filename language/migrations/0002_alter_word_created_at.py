import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("language", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="word",
            name="created_at",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="تاریخ ایجاد"
            ),
        ),
    ]
