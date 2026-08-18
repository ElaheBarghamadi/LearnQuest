import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
                (
                    "achievement_type",
                    models.CharField(
                        choices=[
                            ("memory_10", "۱۰ بازی حافظه"),
                            ("puzzle_10", "۱۰ بازی پازل"),
                            ("sudoku_10", "۱۰ بازی سودوکو"),
                            ("iq_10", "۱۰ بازی تست هوش"),
                            ("memory_master", "استاد حافظه"),
                            ("puzzle_master", "استاد پازل"),
                            ("sudoku_master", "استاد سودوکو"),
                            ("iq_master", "نابغه هوش"),
                        ],
                        max_length=30,
                        verbose_name="نوع دستاورد",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="نام دستاورد")),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")),
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
                "ordering": ["-earned_at"],
                "unique_together": {("user", "achievement_type")},
            },
        ),
        migrations.CreateModel(
            name="UserGameStats",
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
                (
                    "game_name",
                    models.CharField(
                        choices=[
                            ("memory", "بازی حافظه"),
                            ("puzzle", "پازل عددی"),
                            ("sudoku", "سودوکو"),
                            ("iq_test", "تست هوش"),
                        ],
                        max_length=20,
                        verbose_name="نام بازی",
                    ),
                ),
                (
                    "games_played",
                    models.IntegerField(default=0, verbose_name="تعداد بازی انجام شده"),
                ),
                (
                    "games_completed",
                    models.IntegerField(default=0, verbose_name="تعداد بازی کامل شده"),
                ),
                (
                    "best_score",
                    models.IntegerField(default=0, verbose_name="بهترین امتیاز"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="تاریخ به\u200cروزرسانی"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="game_stats",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "آمار بازی",
                "verbose_name_plural": "آمار بازی\u200cها",
                "ordering": ["-updated_at"],
                "unique_together": {("user", "game_name")},
            },
        ),
    ]
