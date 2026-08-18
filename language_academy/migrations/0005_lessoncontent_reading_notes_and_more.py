import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("language_academy", "0004_quizsession"),
    ]

    operations = [
        migrations.AddField(
            model_name="lessoncontent",
            name="reading_notes",
            field=models.TextField(
                blank=True,
                help_text="Key notes about the reading",
                null=True,
                verbose_name="نکات متن",
            ),
        ),
        migrations.AddField(
            model_name="lessoncontent",
            name="reading_text",
            field=models.TextField(
                blank=True,
                help_text="Reading passage text",
                null=True,
                verbose_name="متن خواندن",
            ),
        ),
        migrations.AddField(
            model_name="lessoncontent",
            name="reading_translation",
            field=models.TextField(
                blank=True,
                help_text="Persian translation of reading text",
                null=True,
                verbose_name="ترجمه متن",
            ),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="allow_skip",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="example_sentences",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="featured_image",
            field=models.ImageField(blank=True, null=True, upload_to="lesson_images/"),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="featured_video",
            field=models.FileField(blank=True, null=True, upload_to="lesson_videos/"),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="featured_video_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="grammar_examples",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="grammar_notes",
            field=ckeditor.fields.RichTextField(blank=True),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="introduction_audio",
            field=models.FileField(
                blank=True, null=True, upload_to="lesson_audio/intros/"
            ),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="is_interactive",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="key_takeaways",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="learning_objectives",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="lessoncontent",
            name="summary",
            field=ckeditor.fields.RichTextField(),
        ),
    ]
