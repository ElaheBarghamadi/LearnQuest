from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_alter_comment_is_approved'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='likes',
            field=models.PositiveIntegerField(default=0, verbose_name='تعداد لایک'),
        ),
    ]
