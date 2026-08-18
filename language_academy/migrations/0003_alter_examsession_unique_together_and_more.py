from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("language_academy", "0002_examsession"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="examsession",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="examsession",
            name="attempt_id",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
