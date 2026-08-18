import ckeditor.fields
import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Badge",
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
                ("name", models.CharField(max_length=100, verbose_name="نام")),
                (
                    "name_fa",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="نام به فارسی"
                    ),
                ),
                ("description", models.TextField(verbose_name="توضیحات")),
                (
                    "badge_type",
                    models.CharField(
                        choices=[
                            ("milestone", "Milestone"),
                            ("streak", "Streak"),
                            ("mastery", "Mastery"),
                            ("quiz", "Quiz Excellence"),
                            ("world", "World Completion"),
                            ("special", "Special"),
                        ],
                        max_length=20,
                        verbose_name="نوع مدال",
                    ),
                ),
                (
                    "icon",
                    models.ImageField(
                        blank=True, null=True, upload_to="badges/", verbose_name="آیکون"
                    ),
                ),
                (
                    "requirement_type",
                    models.CharField(max_length=50, verbose_name="نوع نیازمندی"),
                ),
                (
                    "requirement_value",
                    models.IntegerField(verbose_name="مقدار نیازمندی"),
                ),
                ("xp_reward", models.IntegerField(default=50, verbose_name="پاداش XP")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("order", models.IntegerField(default=0, verbose_name="ترتیب")),
            ],
            options={
                "verbose_name": "مدال",
                "verbose_name_plural": "مدال\u200cها",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Dialogue",
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
                (
                    "title_fa",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="عنوان به فارسی"
                    ),
                ),
                ("description", models.TextField(verbose_name="توضیحات")),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("A1", "A1 - Beginner"),
                            ("A2", "A2 - Elementary"),
                            ("B1", "B1 - Intermediate"),
                        ],
                        default="A1",
                        max_length=2,
                        verbose_name="سطح دشواری",
                    ),
                ),
                (
                    "scenario_audio",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="dialogue/scenario_audio/",
                        verbose_name="فایل صوتی سناریو",
                    ),
                ),
                (
                    "background_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="dialogue/backgrounds/",
                        verbose_name="تصویر پس\u200cزمینه",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("order", models.IntegerField(default=0, verbose_name="ترتیب")),
            ],
            options={
                "verbose_name": "دیالوگ",
                "verbose_name_plural": "دیالوگ\u200cها",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="VocabularyCategory",
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
                ("name", models.CharField(max_length=100, verbose_name="نام")),
                (
                    "name_fa",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="نام به فارسی"
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")),
                (
                    "icon",
                    models.CharField(
                        blank=True,
                        help_text="Font Awesome icon class",
                        max_length=50,
                        verbose_name="آیکون",
                    ),
                ),
                ("order", models.IntegerField(default=0, verbose_name="ترتیب")),
            ],
            options={
                "verbose_name": "دسته\u200cبندی واژگان",
                "verbose_name_plural": "دسته\u200cبندی\u200cهای واژگان",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="World",
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
                ("name", models.CharField(max_length=100, verbose_name="نام")),
                (
                    "name_fa",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="نام به فارسی"
                    ),
                ),
                ("description", models.TextField(verbose_name="توضیحات")),
                (
                    "difficulty_level",
                    models.CharField(
                        choices=[
                            ("A1", "Beginner (A1)"),
                            ("A2", "Elementary (A2)"),
                            ("B1", "Intermediate (B1)"),
                        ],
                        default="A1",
                        max_length=2,
                        verbose_name="سطح دشواری",
                    ),
                ),
                ("order", models.IntegerField(unique=True, verbose_name="ترتیب")),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="worlds/", verbose_name="تصویر"
                    ),
                ),
                (
                    "background_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="worlds/backgrounds/",
                        verbose_name="تصویر پس\u200cزمینه",
                    ),
                ),
                (
                    "map_svg",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="worlds/maps/",
                        verbose_name="نقشه SVG",
                    ),
                ),
                (
                    "xp_reward",
                    models.IntegerField(default=500, verbose_name="پاداش XP"),
                ),
                (
                    "coin_reward",
                    models.IntegerField(default=100, verbose_name="پاداش سکه"),
                ),
                (
                    "is_published",
                    models.BooleanField(default=False, verbose_name="منتشر شده"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "جهان",
                "verbose_name_plural": "جهان\u200cها",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Chapter",
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
                ("name", models.CharField(max_length=100, verbose_name="نام")),
                (
                    "name_fa",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="نام به فارسی"
                    ),
                ),
                ("description", models.TextField(verbose_name="توضیحات")),
                ("order", models.IntegerField(verbose_name="ترتیب")),
                (
                    "unlock_score",
                    models.IntegerField(
                        default=0,
                        help_text="Minimum score required from previous chapter",
                        verbose_name="امتیاز مورد نیاز برای باز کردن",
                    ),
                ),
                (
                    "xp_reward",
                    models.IntegerField(default=100, verbose_name="پاداش XP"),
                ),
                (
                    "coin_reward",
                    models.IntegerField(default=20, verbose_name="پاداش سکه"),
                ),
                (
                    "passing_score",
                    models.IntegerField(
                        default=70,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                        verbose_name="نمره قبولی",
                    ),
                ),
                (
                    "estimated_time_minutes",
                    models.IntegerField(default=30, verbose_name="زمان تخمینی (دقیقه)"),
                ),
                (
                    "is_published",
                    models.BooleanField(default=False, verbose_name="منتشر شده"),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="chapters/",
                        verbose_name="تصویر",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "required_chapter",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="language_academy.chapter",
                        verbose_name="فصل مورد نیاز",
                    ),
                ),
                (
                    "world",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chapters",
                        to="language_academy.world",
                        verbose_name="جهان",
                    ),
                ),
            ],
            options={
                "verbose_name": "فصل",
                "verbose_name_plural": "فصل\u200cها",
                "ordering": ["world__order", "order"],
            },
        ),
        migrations.CreateModel(
            name="CoinTransaction",
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
                ("amount", models.IntegerField(verbose_name="مقدار")),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[("earn", "Earned"), ("spend", "Spent")],
                        max_length=5,
                        verbose_name="نوع تراکنش",
                    ),
                ),
                ("source", models.CharField(max_length=100, verbose_name="منبع")),
                (
                    "source_id",
                    models.IntegerField(
                        help_text="ID of the source object", verbose_name="ID منبع"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_coin_transactions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "تراکنش سکه",
                "verbose_name_plural": "تراکنش\u200cهای سکه",
            },
        ),
        migrations.CreateModel(
            name="DialogueScene",
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
                ("order", models.IntegerField(verbose_name="ترتیب")),
                ("character", models.CharField(max_length=100, verbose_name="شخصیت")),
                (
                    "character_avatar",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="dialogue/avatars/",
                        verbose_name="آواتار شخصیت",
                    ),
                ),
                ("message", models.TextField(verbose_name="پیام")),
                (
                    "message_fa",
                    models.TextField(blank=True, verbose_name="پیام به فارسی"),
                ),
                (
                    "audio",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="dialogue/audio/",
                        verbose_name="فایل صوتی",
                    ),
                ),
                (
                    "is_user_turn",
                    models.BooleanField(default=False, verbose_name="نوبت کاربر"),
                ),
                (
                    "dialogue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scenes",
                        to="language_academy.dialogue",
                        verbose_name="دیالوگ",
                    ),
                ),
            ],
            options={
                "verbose_name": "صحنه دیالوگ",
                "verbose_name_plural": "صحنه\u200cهای دیالوگ",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="DialogueChoice",
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
                ("choice_text", models.TextField(verbose_name="متن انتخاب")),
                (
                    "choice_text_fa",
                    models.TextField(blank=True, verbose_name="متن انتخاب به فارسی"),
                ),
                ("is_correct", models.BooleanField(default=False, verbose_name="صحیح")),
                ("feedback", models.TextField(blank=True, verbose_name="بازخورد")),
                (
                    "feedback_fa",
                    models.TextField(blank=True, verbose_name="بازخورد به فارسی"),
                ),
                ("xp_reward", models.IntegerField(default=5, verbose_name="پاداش XP")),
                (
                    "next_scene",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="language_academy.dialoguescene",
                        verbose_name="صحنه بعدی",
                    ),
                ),
                (
                    "scene",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="choices",
                        to="language_academy.dialoguescene",
                        verbose_name="صحنه",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Exam",
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
                    "exam_type",
                    models.CharField(
                        choices=[
                            ("chapter", "Chapter Exam"),
                            ("world", "World Exam"),
                            ("final", "Final Exam"),
                        ],
                        max_length=20,
                        verbose_name="نوع امتحان",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="عنوان")),
                ("description", models.TextField(verbose_name="توضیحات")),
                (
                    "passing_score",
                    models.IntegerField(
                        default=70,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                        verbose_name="نمره قبولی",
                    ),
                ),
                (
                    "time_limit_minutes",
                    models.IntegerField(default=60, verbose_name="زمان محدود (دقیقه)"),
                ),
                (
                    "max_attempts",
                    models.IntegerField(default=3, verbose_name="حداکثر تلاش"),
                ),
                (
                    "questions_count",
                    models.IntegerField(default=20, verbose_name="تعداد سوالات"),
                ),
                (
                    "randomize_questions",
                    models.BooleanField(
                        default=True, verbose_name="به هم ریختن سوالات"
                    ),
                ),
                (
                    "xp_reward",
                    models.IntegerField(default=200, verbose_name="پاداش XP"),
                ),
                (
                    "coin_reward",
                    models.IntegerField(default=50, verbose_name="پاداش سکه"),
                ),
                (
                    "is_published",
                    models.BooleanField(default=False, verbose_name="منتشر شده"),
                ),
                (
                    "chapter",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exams",
                        to="language_academy.chapter",
                        verbose_name="فصل",
                    ),
                ),
                (
                    "world",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exams",
                        to="language_academy.world",
                        verbose_name="جهان",
                    ),
                ),
            ],
            options={
                "verbose_name": "امتحان",
                "verbose_name_plural": "امتحانات",
            },
        ),
        migrations.CreateModel(
            name="ExamAttempt",
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
                ("score", models.IntegerField(verbose_name="نمره")),
                ("passed", models.BooleanField(default=False, verbose_name="پاس شده")),
                (
                    "answers",
                    models.JSONField(default=dict, verbose_name="پاسخ\u200cها"),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "time_spent_seconds",
                    models.IntegerField(default=0, verbose_name="زمان صرف شده (ثانیه)"),
                ),
                (
                    "exam",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="language_academy.exam",
                        verbose_name="امتحان",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_exam_attempts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "تلاش امتحان",
                "verbose_name_plural": "تلاش\u200cهای امتحان",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="ExamQuestion",
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
                ("question", models.TextField(verbose_name="سوال")),
                (
                    "question_fa",
                    models.TextField(blank=True, verbose_name="سوال به فارسی"),
                ),
                (
                    "question_type",
                    models.CharField(
                        choices=[
                            ("mcq", "Multiple Choice"),
                            ("fill_blank", "Fill in the Blank"),
                            ("matching", "Matching"),
                            ("ordering", "Sentence Ordering"),
                            ("listening", "Listening Comprehension"),
                            ("writing", "Writing"),
                            ("speaking", "Speaking"),
                            ("dialogue", "Dialogue Response"),
                            ("true_false", "True/False"),
                        ],
                        max_length=20,
                        verbose_name="نوع سوال",
                    ),
                ),
                ("correct_answer", models.TextField(verbose_name="پاسخ صحیح")),
                (
                    "options",
                    models.JSONField(default=list, verbose_name="گزینه\u200cها"),
                ),
                ("points", models.IntegerField(default=10, verbose_name="امتیاز")),
                ("order", models.IntegerField(default=0, verbose_name="ترتیب")),
                (
                    "exam",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exam_questions",
                        to="language_academy.exam",
                        verbose_name="امتحان",
                    ),
                ),
            ],
            options={
                "verbose_name": "سوال امتحان",
                "verbose_name_plural": "سوالات امتحان",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Lesson",
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
                ("name", models.CharField(max_length=100, verbose_name="نام")),
                (
                    "name_fa",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="نام به فارسی"
                    ),
                ),
                (
                    "lesson_type",
                    models.CharField(
                        choices=[
                            ("vocabulary", "Vocabulary"),
                            ("grammar", "Grammar"),
                            ("dialogue", "Dialogue"),
                            ("reading", "Reading"),
                            ("listening", "Listening"),
                            ("writing", "Writing"),
                            ("speaking", "Speaking"),
                            ("mixed", "Mixed"),
                        ],
                        default="mixed",
                        max_length=20,
                        verbose_name="نوع درس",
                    ),
                ),
                ("order", models.IntegerField(verbose_name="ترتیب")),
                ("xp_reward", models.IntegerField(default=50, verbose_name="پاداش XP")),
                (
                    "coin_reward",
                    models.IntegerField(default=10, verbose_name="پاداش سکه"),
                ),
                (
                    "estimated_time_minutes",
                    models.IntegerField(default=15, verbose_name="زمان تخمینی (دقیقه)"),
                ),
                (
                    "is_published",
                    models.BooleanField(default=False, verbose_name="منتشر شده"),
                ),
                (
                    "is_free_preview",
                    models.BooleanField(
                        default=False, verbose_name="پیش\u200cنمایش رایگان"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "chapter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lessons",
                        to="language_academy.chapter",
                        verbose_name="فصل",
                    ),
                ),
            ],
            options={
                "verbose_name": "درس",
                "verbose_name_plural": "درس\u200cها",
                "ordering": ["chapter__world__order", "chapter__order", "order"],
                "unique_together": {("chapter", "order")},
            },
        ),
        migrations.AddField(
            model_name="dialogue",
            name="lesson",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dialogues",
                to="language_academy.lesson",
                verbose_name="درس",
            ),
        ),
        migrations.CreateModel(
            name="AIConversation",
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
                    "context",
                    models.CharField(blank=True, max_length=200, verbose_name="زمینه"),
                ),
                (
                    "messages",
                    models.JSONField(default=list, verbose_name="پیام\u200cها"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_ai_conversations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
                (
                    "lesson",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="language_academy.lesson",
                        verbose_name="درس",
                    ),
                ),
            ],
            options={
                "verbose_name": "مکالمه AI",
                "verbose_name_plural": "مکالمات AI",
            },
        ),
        migrations.CreateModel(
            name="LessonContent",
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
                    "introduction",
                    ckeditor.fields.RichTextField(
                        help_text="Hook to engage the learner", verbose_name="مقدمه"
                    ),
                ),
                (
                    "introduction_audio",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="lesson_audio/intros/",
                        verbose_name="فایل صوتی مقدمه",
                    ),
                ),
                (
                    "learning_objectives",
                    models.JSONField(
                        default=list,
                        help_text="List of objectives",
                        verbose_name="اهداف یادگیری",
                    ),
                ),
                (
                    "grammar_notes",
                    ckeditor.fields.RichTextField(
                        blank=True, verbose_name="نکات گرامر"
                    ),
                ),
                (
                    "grammar_examples",
                    models.JSONField(
                        default=list,
                        help_text="List of grammar examples",
                        verbose_name="مثال\u200cهای گرامر",
                    ),
                ),
                (
                    "example_sentences",
                    models.JSONField(
                        default=list,
                        help_text="List of example sentence objects",
                        verbose_name="جملات مثال",
                    ),
                ),
                (
                    "featured_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="lesson_images/",
                        verbose_name="تصویر شاخص",
                    ),
                ),
                (
                    "featured_video",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="lesson_videos/",
                        verbose_name="ویدیو شاخص",
                    ),
                ),
                (
                    "featured_video_url",
                    models.URLField(blank=True, null=True, verbose_name="لینک ویدیو"),
                ),
                ("summary", ckeditor.fields.RichTextField(verbose_name="خلاصه")),
                (
                    "key_takeaways",
                    models.JSONField(default=list, verbose_name="نکات کلیدی"),
                ),
                (
                    "is_interactive",
                    models.BooleanField(default=True, verbose_name="تعاملی"),
                ),
                (
                    "allow_skip",
                    models.BooleanField(default=False, verbose_name="اجازه رد کردن"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "lesson",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="content",
                        to="language_academy.lesson",
                        verbose_name="درس",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Question",
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
                    "question_type",
                    models.CharField(
                        choices=[
                            ("mcq", "Multiple Choice"),
                            ("fill_blank", "Fill in the Blank"),
                            ("matching", "Matching"),
                            ("ordering", "Sentence Ordering"),
                            ("listening", "Listening Comprehension"),
                            ("writing", "Writing"),
                            ("speaking", "Speaking"),
                            ("dialogue", "Dialogue Response"),
                            ("true_false", "True/False"),
                        ],
                        max_length=20,
                        verbose_name="نوع سوال",
                    ),
                ),
                ("question_text", models.TextField(verbose_name="متن سوال")),
                (
                    "question_text_fa",
                    models.TextField(blank=True, verbose_name="متن سوال به فارسی"),
                ),
                (
                    "question_audio",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="questions/audio/",
                        verbose_name="فایل صوتی سوال",
                    ),
                ),
                (
                    "question_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="questions/images/",
                        verbose_name="تصویر سوال",
                    ),
                ),
                ("points", models.IntegerField(default=10, verbose_name="امتیاز")),
                ("order", models.IntegerField(default=0, verbose_name="ترتیب")),
                (
                    "blank_answer",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="پاسخ جای خالی"
                    ),
                ),
                (
                    "matching_pairs",
                    models.JSONField(
                        blank=True, default=list, verbose_name="جفت\u200cهای تطبیق"
                    ),
                ),
                (
                    "correct_order",
                    models.JSONField(
                        blank=True, default=list, verbose_name="ترتیب صحیح"
                    ),
                ),
                ("hint", models.TextField(blank=True, verbose_name="راهنما")),
                ("explanation", models.TextField(blank=True, verbose_name="توضیح")),
                (
                    "explanation_fa",
                    models.TextField(blank=True, verbose_name="توضیح به فارسی"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "lesson",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="language_academy.lesson",
                        verbose_name="درس",
                    ),
                ),
            ],
            options={
                "verbose_name": "سوال",
                "verbose_name_plural": "سوالات",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="QuestionChoice",
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
                    "choice_text",
                    models.CharField(max_length=500, verbose_name="متن گزینه"),
                ),
                (
                    "choice_text_fa",
                    models.CharField(
                        blank=True, max_length=500, verbose_name="متن گزینه به فارسی"
                    ),
                ),
                ("is_correct", models.BooleanField(default=False, verbose_name="صحیح")),
                ("order", models.IntegerField(default=0, verbose_name="ترتیب")),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="choices",
                        to="language_academy.question",
                        verbose_name="سوال",
                    ),
                ),
            ],
            options={
                "verbose_name": "گزینه سوال",
                "verbose_name_plural": "گزینه\u200cهای سوال",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Quiz",
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
                    "passing_score",
                    models.IntegerField(
                        default=70,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                        verbose_name="نمره قبولی",
                    ),
                ),
                (
                    "time_limit_minutes",
                    models.IntegerField(default=10, verbose_name="زمان محدود (دقیقه)"),
                ),
                (
                    "max_attempts",
                    models.IntegerField(default=3, verbose_name="حداکثر تلاش"),
                ),
                (
                    "shuffle_questions",
                    models.BooleanField(
                        default=False, verbose_name="به هم ریختن سوالات"
                    ),
                ),
                ("xp_reward", models.IntegerField(default=30, verbose_name="پاداش XP")),
                (
                    "coin_reward",
                    models.IntegerField(default=15, verbose_name="پاداش سکه"),
                ),
                (
                    "is_published",
                    models.BooleanField(default=False, verbose_name="منتشر شده"),
                ),
                (
                    "lesson",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quiz",
                        to="language_academy.lesson",
                        verbose_name="درس",
                    ),
                ),
            ],
            options={
                "verbose_name": "کوئیز",
                "verbose_name_plural": "کوئیزها",
            },
        ),
        migrations.AddField(
            model_name="question",
            name="quiz",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="questions",
                to="language_academy.quiz",
                verbose_name="کوئیز",
            ),
        ),
        migrations.CreateModel(
            name="QuizAttempt",
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
                ("score", models.IntegerField(verbose_name="نمره")),
                ("passed", models.BooleanField(default=False, verbose_name="پاس شده")),
                (
                    "answers",
                    models.JSONField(default=dict, verbose_name="پاسخ\u200cها"),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "time_spent_seconds",
                    models.IntegerField(default=0, verbose_name="زمان صرف شده (ثانیه)"),
                ),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="language_academy.quiz",
                        verbose_name="کوئیز",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_quiz_attempts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "تلاش کوئیز",
                "verbose_name_plural": "تلاش\u200cهای کوئیز",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="SpeakingSubmission",
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
                ("prompt", models.TextField(verbose_name="پرامپت")),
                (
                    "prompt_fa",
                    models.TextField(blank=True, verbose_name="پرامپت به فارسی"),
                ),
                (
                    "audio_file",
                    models.FileField(
                        upload_to="speaking_submissions/", verbose_name="فایل صوتی"
                    ),
                ),
                (
                    "transcript",
                    models.TextField(blank=True, verbose_name="متن پیاده شده"),
                ),
                (
                    "ai_feedback",
                    models.JSONField(blank=True, null=True, verbose_name="بازخورد AI"),
                ),
                (
                    "pronunciation_score",
                    models.FloatField(blank=True, null=True, verbose_name="نمره تلفظ"),
                ),
                (
                    "fluency_score",
                    models.FloatField(blank=True, null=True, verbose_name="نمره روانی"),
                ),
                (
                    "grammar_score",
                    models.FloatField(blank=True, null=True, verbose_name="نمره گرامر"),
                ),
                (
                    "overall_score",
                    models.FloatField(blank=True, null=True, verbose_name="نمره کلی"),
                ),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "evaluated_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="زمان ارزیابی"
                    ),
                ),
                (
                    "lesson",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="language_academy.lesson",
                        verbose_name="درس",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_speaking_submissions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "ارسال گفتاری",
                "verbose_name_plural": "ارسال\u200cهای گفتاری",
            },
        ),
        migrations.CreateModel(
            name="Vocabulary",
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
                    "word",
                    models.CharField(
                        db_index=True, max_length=100, verbose_name="کلمه"
                    ),
                ),
                (
                    "pronunciation",
                    models.CharField(
                        blank=True,
                        help_text="IPA or phonetic spelling",
                        max_length=200,
                        verbose_name="تلفظ",
                    ),
                ),
                ("meaning", models.TextField(verbose_name="معنی")),
                (
                    "meaning_fa",
                    models.TextField(blank=True, verbose_name="معنی به فارسی"),
                ),
                (
                    "part_of_speech",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="نوع کلمه"
                    ),
                ),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("A1", "A1 - Beginner"),
                            ("A2", "A2 - Elementary"),
                            ("B1", "B1 - Intermediate"),
                        ],
                        default="A1",
                        max_length=2,
                        verbose_name="سطح دشواری",
                    ),
                ),
                (
                    "audio_uk",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="vocabulary/audio/uk/",
                        verbose_name="تلفظ بریتیش",
                    ),
                ),
                (
                    "audio_us",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="vocabulary/audio/us/",
                        verbose_name="تلفظ آمریکن",
                    ),
                ),
                (
                    "audio_example",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="vocabulary/audio/examples/",
                        verbose_name="مثال صوتی",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="vocabulary/images/",
                        verbose_name="تصویر",
                    ),
                ),
                (
                    "usage_count",
                    models.IntegerField(default=0, verbose_name="تعداد استفاده"),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "categories",
                    models.ManyToManyField(
                        related_name="vocabulary",
                        to="language_academy.vocabularycategory",
                        verbose_name="دسته\u200cبندی\u200cها",
                    ),
                ),
            ],
            options={
                "verbose_name": "واژه",
                "verbose_name_plural": "واژگان",
                "ordering": ["difficulty", "word"],
            },
        ),
        migrations.CreateModel(
            name="VocabularyExample",
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
                ("sentence", models.TextField(verbose_name="جمله")),
                (
                    "sentence_fa",
                    models.TextField(blank=True, verbose_name="جمله به فارسی"),
                ),
                (
                    "audio",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="vocabulary/examples/audio/",
                        verbose_name="فایل صوتی",
                    ),
                ),
                ("order", models.IntegerField(default=0, verbose_name="ترتیب")),
                (
                    "vocabulary",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="examples",
                        to="language_academy.vocabulary",
                        verbose_name="واژه",
                    ),
                ),
            ],
            options={
                "verbose_name": "مثال واژه",
                "verbose_name_plural": "مثال\u200cهای واژه",
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="UserWorldProgress",
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
                    "is_completed",
                    models.BooleanField(default=False, verbose_name="تکمیل شده"),
                ),
                (
                    "exam_score",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="نمره امتحان"
                    ),
                ),
                (
                    "exam_passed",
                    models.BooleanField(default=False, verbose_name="امتحان پاس شده"),
                ),
                (
                    "chapters_completed",
                    models.IntegerField(
                        default=0, verbose_name="فصل\u200cهای تکمیل شده"
                    ),
                ),
                (
                    "total_chapters",
                    models.IntegerField(default=0, verbose_name="کل فصل\u200cها"),
                ),
                (
                    "xp_earned",
                    models.IntegerField(default=0, verbose_name="XP کسب شده"),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="تاریخ تکمیل"
                    ),
                ),
                (
                    "certificate_issued",
                    models.BooleanField(default=False, verbose_name="گواهی صادر شده"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_world_progress",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
                (
                    "world",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_progress",
                        to="language_academy.world",
                        verbose_name="جهان",
                    ),
                ),
            ],
            options={
                "verbose_name": "پیشرفت جهان",
                "verbose_name_plural": "پیشرفت جهان\u200cها",
            },
        ),
        migrations.CreateModel(
            name="Certificate",
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
                    "certificate_number",
                    models.CharField(
                        default=uuid.uuid4,
                        max_length=100,
                        unique=True,
                        verbose_name="شماره گواهی",
                    ),
                ),
                (
                    "issued_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="تاریخ صادر"),
                ),
                (
                    "pdf_file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="certificates/",
                        verbose_name="فایل PDF",
                    ),
                ),
                (
                    "verification_code",
                    models.CharField(
                        default=uuid.uuid4,
                        max_length=100,
                        unique=True,
                        verbose_name="کد تأیید",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_certificates",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
                (
                    "world",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="language_academy.world",
                        verbose_name="جهان",
                    ),
                ),
            ],
            options={
                "verbose_name": "گواهی",
                "verbose_name_plural": "گواهی\u200cها",
            },
        ),
        migrations.CreateModel(
            name="WritingSubmission",
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
                ("prompt", models.TextField(verbose_name="پرامپت")),
                (
                    "prompt_fa",
                    models.TextField(blank=True, verbose_name="پرامپت به فارسی"),
                ),
                ("submission", models.TextField(verbose_name="ارسال")),
                (
                    "ai_feedback",
                    models.JSONField(blank=True, null=True, verbose_name="بازخورد AI"),
                ),
                (
                    "grammar_score",
                    models.FloatField(blank=True, null=True, verbose_name="نمره گرامر"),
                ),
                (
                    "vocabulary_score",
                    models.FloatField(
                        blank=True, null=True, verbose_name="نمره واژگان"
                    ),
                ),
                (
                    "coherence_score",
                    models.FloatField(
                        blank=True, null=True, verbose_name="نمره انسجام"
                    ),
                ),
                (
                    "overall_score",
                    models.FloatField(blank=True, null=True, verbose_name="نمره کلی"),
                ),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "evaluated_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="زمان ارزیابی"
                    ),
                ),
                (
                    "lesson",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="language_academy.lesson",
                        verbose_name="درس",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_writing_submissions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "ارسال نوشتاری",
                "verbose_name_plural": "ارسال\u200cهای نوشتاری",
            },
        ),
        migrations.CreateModel(
            name="DailyGoal",
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
                ("target_xp", models.IntegerField(default=100, verbose_name="هدف XP")),
                (
                    "target_lessons",
                    models.IntegerField(default=2, verbose_name="هدف درس\u200cها"),
                ),
                (
                    "target_vocabulary",
                    models.IntegerField(default=5, verbose_name="هدف واژگان"),
                ),
                ("current_xp", models.IntegerField(default=0, verbose_name="XP فعلی")),
                (
                    "current_lessons",
                    models.IntegerField(default=0, verbose_name="درس\u200cهای فعلی"),
                ),
                (
                    "current_vocabulary",
                    models.IntegerField(default=0, verbose_name="واژگان فعلی"),
                ),
                (
                    "goal_date",
                    models.DateField(auto_now_add=True, verbose_name="تاریخ هدف"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_daily_goals",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "هدف روزانه",
                "verbose_name_plural": "اهداف روزانه",
                "unique_together": {("user", "goal_date")},
            },
        ),
        migrations.CreateModel(
            name="LearningAnalytics",
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
                ("total_xp", models.IntegerField(default=0, verbose_name="کل XP")),
                ("total_coins", models.IntegerField(default=0, verbose_name="کل سکه")),
                (
                    "total_lessons_completed",
                    models.IntegerField(
                        default=0, verbose_name="کل درس\u200cهای تکمیل شده"
                    ),
                ),
                (
                    "total_quizzes_passed",
                    models.IntegerField(default=0, verbose_name="کل کوئیزهای پاس شده"),
                ),
                (
                    "total_exams_passed",
                    models.IntegerField(default=0, verbose_name="کل امتحانات پاس شده"),
                ),
                (
                    "vocabulary_learned",
                    models.IntegerField(default=0, verbose_name="واژگان یاد گرفته شده"),
                ),
                (
                    "overall_grammar_mastery",
                    models.FloatField(default=0, verbose_name="تسلط کلی گرامر"),
                ),
                (
                    "overall_vocabulary_mastery",
                    models.FloatField(default=0, verbose_name="تسلط کلی واژگان"),
                ),
                (
                    "overall_speaking_mastery",
                    models.FloatField(default=0, verbose_name="تسلط کلی گفتاری"),
                ),
                (
                    "overall_writing_mastery",
                    models.FloatField(default=0, verbose_name="تسلط کلی نوشتاری"),
                ),
                (
                    "weak_grammar_areas",
                    models.JSONField(default=list, verbose_name="نقاط ضعف گرامر"),
                ),
                (
                    "weak_vocabulary_categories",
                    models.JSONField(
                        default=list, verbose_name="دسته\u200cبندی\u200cهای ضعف واژگان"
                    ),
                ),
                (
                    "frequent_mistakes",
                    models.JSONField(default=list, verbose_name="اشتباهات مکرر"),
                ),
                (
                    "recommended_lessons",
                    models.JSONField(
                        default=list, verbose_name="درس\u200cهای پیشنهادی"
                    ),
                ),
                (
                    "predicted_exam_readiness",
                    models.JSONField(
                        default=dict,
                        verbose_name="آمادگی پیش\u200cبینی شده برای امتحان",
                    ),
                ),
                (
                    "average_session_duration",
                    models.FloatField(default=0, verbose_name="متوسط زمان جلسه"),
                ),
                (
                    "best_learning_time",
                    models.CharField(
                        blank=True, max_length=10, verbose_name="بهترین زمان یادگیری"
                    ),
                ),
                (
                    "preferred_lesson_types",
                    models.JSONField(
                        default=list, verbose_name="نوع درس\u200cهای ترجیحی"
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_learning_analytics",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "تحلیل یادگیری",
                "verbose_name_plural": "تحلیل\u200cهای یادگیری",
                "unique_together": {("user",)},
            },
        ),
        migrations.CreateModel(
            name="UserBadge",
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
                    "earned_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="تاریخ دریافت"
                    ),
                ),
                (
                    "is_notified",
                    models.BooleanField(default=False, verbose_name="اطلاع رسانی شده"),
                ),
                (
                    "badge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="users",
                        to="language_academy.badge",
                        verbose_name="مدال",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_badges",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "مدال کاربر",
                "verbose_name_plural": "مدال\u200cهای کاربر",
                "unique_together": {("user", "badge")},
            },
        ),
        migrations.CreateModel(
            name="UserChapterProgress",
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
                    "is_completed",
                    models.BooleanField(default=False, verbose_name="تکمیل شده"),
                ),
                (
                    "exam_score",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="نمره امتحان"
                    ),
                ),
                (
                    "exam_passed",
                    models.BooleanField(default=False, verbose_name="امتحان پاس شده"),
                ),
                (
                    "lessons_completed",
                    models.IntegerField(
                        default=0, verbose_name="درس\u200cهای تکمیل شده"
                    ),
                ),
                (
                    "total_lessons",
                    models.IntegerField(default=0, verbose_name="کل درس\u200cها"),
                ),
                (
                    "xp_earned",
                    models.IntegerField(default=0, verbose_name="XP کسب شده"),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="تاریخ تکمیل"
                    ),
                ),
                (
                    "chapter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_progress",
                        to="language_academy.chapter",
                        verbose_name="فصل",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_chapter_progress",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "پیشرفت فصل",
                "verbose_name_plural": "پیشرفت فصل\u200cها",
                "unique_together": {("user", "chapter")},
            },
        ),
        migrations.CreateModel(
            name="UserLessonProgress",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("not_started", "Not Started"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                        ],
                        default="not_started",
                        max_length=20,
                        verbose_name="وضعیت",
                    ),
                ),
                (
                    "progress_percentage",
                    models.FloatField(default=0, verbose_name="درصد پیشرفت"),
                ),
                (
                    "quiz_score",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="نمره کوئیز"
                    ),
                ),
                (
                    "quiz_passed",
                    models.BooleanField(default=False, verbose_name="کوئیز پاس شده"),
                ),
                (
                    "xp_earned",
                    models.IntegerField(default=0, verbose_name="XP کسب شده"),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                (
                    "last_activity",
                    models.DateTimeField(auto_now=True, verbose_name="آخرین فعالیت"),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="تاریخ تکمیل"
                    ),
                ),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_progress",
                        to="language_academy.lesson",
                        verbose_name="درس",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_lesson_progress",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
            ],
            options={
                "verbose_name": "پیشرفت درس",
                "verbose_name_plural": "پیشرفت درس\u200cها",
                "unique_together": {("user", "lesson")},
            },
        ),
        migrations.CreateModel(
            name="UserVocabularyProgress",
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
                    "mastery_level",
                    models.IntegerField(
                        choices=[
                            (0, "Not Learned"),
                            (1, "Introduced"),
                            (2, "Reviewed"),
                            (3, "Practiced"),
                            (4, "Mastered"),
                        ],
                        default=0,
                        verbose_name="سطح تسلط",
                    ),
                ),
                (
                    "mastery_score",
                    models.FloatField(
                        default=0,
                        help_text="0-100 mastery score",
                        verbose_name="نمره تسلط",
                    ),
                ),
                (
                    "review_count",
                    models.IntegerField(default=0, verbose_name="تعداد مرور"),
                ),
                (
                    "correct_count",
                    models.IntegerField(default=0, verbose_name="تعداد صحیح"),
                ),
                (
                    "incorrect_count",
                    models.IntegerField(default=0, verbose_name="تعداد غلط"),
                ),
                (
                    "last_reviewed",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="آخرین مرور"
                    ),
                ),
                (
                    "next_review_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="تاریخ مرور بعدی"
                    ),
                ),
                (
                    "forgetting_risk",
                    models.FloatField(
                        default=100,
                        help_text="Risk of forgetting (0-100)",
                        verbose_name="ریسک فراموشی",
                    ),
                ),
                ("last_accuracy", models.FloatField(default=0, verbose_name="دقت آخر")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academy_vocabulary_progress",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="کاربر",
                    ),
                ),
                (
                    "vocabulary",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_progress",
                        to="language_academy.vocabulary",
                        verbose_name="واژه",
                    ),
                ),
            ],
            options={
                "verbose_name": "پیشرفت واژه",
                "verbose_name_plural": "پیشرفت واژگان",
                "indexes": [
                    models.Index(
                        fields=["user", "next_review_date"],
                        name="language_ac_user_id_8baba4_idx",
                    ),
                    models.Index(
                        fields=["user", "mastery_score"],
                        name="language_ac_user_id_59f568_idx",
                    ),
                ],
                "unique_together": {("user", "vocabulary")},
            },
        ),
        migrations.AddIndex(
            model_name="vocabulary",
            index=models.Index(
                fields=["word", "difficulty"], name="language_ac_word_a41f26_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="userworldprogress",
            unique_together={("user", "world")},
        ),
        migrations.AlterUniqueTogether(
            name="chapter",
            unique_together={("world", "order")},
        ),
    ]
