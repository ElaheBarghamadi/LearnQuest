from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0004_alter_comment_is_approved"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="is_approved",
            field=models.BooleanField(default=True, verbose_name="تایید شده"),
        ),
    ]
