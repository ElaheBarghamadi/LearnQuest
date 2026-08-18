from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Game", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userachievement",
            name="achievement_type",
            field=models.CharField(
                choices=[
                    ("memory_10", "۱۰ بازی حافظه"),
                    ("puzzle_10", "۱۰ بازی پازل"),
                    ("sudoku_10", "۱۰ بازی سودوکو"),
                    ("iq_10", "۱۰ بازی تست هوش"),
                    ("memory_master", "استاد حافظه"),
                    ("puzzle_master", "استاد پازل"),
                    ("sudoku_master", "استاد سودوکو"),
                    ("iq_master", "نابغه هوش"),
                    ("language_10", "۱۰ بازی وصل کن"),
                    ("guessing_10", "۱۰ بازی حدس کلمه"),
                    ("scramble_10", "۱۰ بازی جورچین"),
                    ("language_master", "استاد زبان"),
                    ("word_genius", "نابغه کلمات"),
                ],
                max_length=30,
                verbose_name="نوع دستاورد",
            ),
        ),
    ]
