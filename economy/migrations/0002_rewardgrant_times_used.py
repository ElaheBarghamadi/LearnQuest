from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('economy', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rewardgrant',
            name='times_used',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
