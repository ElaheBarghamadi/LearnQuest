import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0002_passwordresetotp_delete_passwordresettoken"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserAchievement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="نام دستاورد")),
                (
                    "icon",
                    models.CharField(
                        default="trophy", max_length=50, verbose_name="آیکون"
                    ),
                ),
                (
                    "earned_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="تاریخ دریافت"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="achievements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "دستاورد",
                "verbose_name_plural": "دستاوردها",
            },
        ),
        migrations.CreateModel(
            name="UserActivity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="عنوان")),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")),
                (
                    "icon",
                    models.CharField(
                        default="bell", max_length=50, verbose_name="آیکون"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="زمان فعالیت"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activities",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "فعالیت",
                "verbose_name_plural": "فعالیت\u200cها",
                "ordering": ["-created_at"],
            },
        ),
    ]
