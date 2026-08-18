from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0003_remove_comment_post_alter_comment_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="is_approved",
            field=models.BooleanField(default=False, verbose_name="تایید شده"),
        ),
    ]
