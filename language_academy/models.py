from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from ckeditor.fields import RichTextField
import uuid

User = settings.AUTH_USER_MODEL


class World(models.Model):
    DIFFICULTY_LEVELS = [
        ('A1', 'Beginner (A1)'),
        ('A2', 'Elementary (A2)'),
        ('B1', 'Intermediate (B1)'),
    ]

    name = models.CharField(max_length=100, verbose_name='نام')
    name_fa = models.CharField(max_length=100, blank=True, verbose_name='نام به فارسی')
    description = models.TextField(verbose_name='توضیحات')
    difficulty_level = models.CharField(max_length=2, choices=DIFFICULTY_LEVELS, default='A1', verbose_name='سطح دشواری')
    order = models.IntegerField(unique=True, verbose_name='ترتیب')
    image = models.ImageField(upload_to='worlds/', blank=True, null=True, verbose_name='تصویر')
    background_image = models.ImageField(upload_to='worlds/backgrounds/', blank=True, null=True, verbose_name='تصویر پس‌زمینه')
    map_svg = models.FileField(upload_to='worlds/maps/', blank=True, null=True, verbose_name='نقشه SVG')
    xp_reward = models.IntegerField(default=500, verbose_name='پاداش XP')
    coin_reward = models.IntegerField(default=100, verbose_name='پاداش سکه')
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'جهان'
        verbose_name_plural = 'جهان‌ها'

    def __str__(self):
        return f"{self.order}. {self.name}"

    def get_chapter_count(self):
        return self.chapters.filter(is_published=True).count()

    def get_completion_percentage(self, user):
        chapters = self.chapters.filter(is_published=True)
        if not chapters.exists():
            return 0
        from .models import UserChapterProgress
        completed = sum(1 for chapter in chapters
                       if UserChapterProgress.objects.filter(
                           user=user, chapter=chapter, is_completed=True
                       ).exists())
        return (completed / chapters.count()) * 100

    def is_unlocked_for_user(self, user):
        """جهان بعدی فقط بعد از تکمیل کامل جهان قبلی باز می‌شود."""
        if not user or not user.is_authenticated:
            return True
        prev = (World.objects
                .filter(is_published=True, order__lt=self.order)
                .order_by('-order').first())
        if prev is None:
            return True
        return UserWorldProgress.objects.filter(
            user=user, world=prev, is_completed=True
        ).exists()

    def is_completed_for_user(self, user):
        if not user or not user.is_authenticated:
            return False
        return UserWorldProgress.objects.filter(
            user=user, world=self, is_completed=True
        ).exists()


class Chapter(models.Model):
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='chapters', verbose_name='جهان')
    name = models.CharField(max_length=100, verbose_name='نام')
    name_fa = models.CharField(max_length=100, blank=True, verbose_name='نام به فارسی')
    description = models.TextField(verbose_name='توضیحات')
    order = models.IntegerField(verbose_name='ترتیب')
    unlock_score = models.IntegerField(default=0, help_text="Minimum score required from previous chapter", verbose_name='امتیاز مورد نیاز برای باز کردن')
    required_chapter = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='فصل مورد نیاز')
    xp_reward = models.IntegerField(default=100, verbose_name='پاداش XP')
    coin_reward = models.IntegerField(default=20, verbose_name='پاداش سکه')
    passing_score = models.IntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نمره قبولی')
    estimated_time_minutes = models.IntegerField(default=30, verbose_name='زمان تخمینی (دقیقه)')
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    image = models.ImageField(upload_to='chapters/', blank=True, null=True, verbose_name='تصویر')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['world__order', 'order']
        unique_together = ['world', 'order']
        verbose_name = 'فصل'
        verbose_name_plural = 'فصل‌ها'

    def __str__(self):
        return f"{self.world.name} - {self.name}"

    def get_lessons(self):
        return self.lessons.filter(is_published=True)

    def is_unlocked_for_user(self, user):
        if not user or not user.is_authenticated:
            return True
        if self.required_chapter:
            progress = UserChapterProgress.objects.filter(
                user=user, chapter=self.required_chapter, is_completed=True
            ).first()
            if not progress or progress.exam_score < self.unlock_score:
                return False
        previous_chapter = Chapter.objects.filter(
            world=self.world, order=self.order - 1, is_published=True
        ).first()
        if previous_chapter:
            prev_progress = UserChapterProgress.objects.filter(
                user=user, chapter=previous_chapter, is_completed=True
            ).first()
            if not prev_progress:
                return False
        return True

    def is_completed_for_user(self, user):
        if not user or not user.is_authenticated:
            return False
        return UserChapterProgress.objects.filter(
            user=user, chapter=self, is_completed=True
        ).exists()


class Lesson(models.Model):
    LESSON_TYPES = [
        ('vocabulary', 'Vocabulary'),
        ('grammar', 'Grammar'),
        ('dialogue', 'Dialogue'),
        ('reading', 'Reading'),
        ('listening', 'Listening'),
        ('writing', 'Writing'),
        ('speaking', 'Speaking'),
        ('mixed', 'Mixed'),
    ]

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='lessons', verbose_name='فصل')
    name = models.CharField(max_length=100, verbose_name='نام')
    name_fa = models.CharField(max_length=100, blank=True, verbose_name='نام به فارسی')
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='mixed', verbose_name='نوع درس')
    order = models.IntegerField(verbose_name='ترتیب')
    xp_reward = models.IntegerField(default=50, verbose_name='پاداش XP')
    coin_reward = models.IntegerField(default=10, verbose_name='پاداش سکه')
    estimated_time_minutes = models.IntegerField(default=15, verbose_name='زمان تخمینی (دقیقه)')
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    is_free_preview = models.BooleanField(default=False, verbose_name='پیش‌نمایش رایگان')
    is_exclusive = models.BooleanField(default=False, verbose_name='درس ویژه (نیازمند خرید بلیط از فروشگاه)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['chapter__world__order', 'chapter__order', 'order']
        unique_together = ['chapter', 'order']
        verbose_name = 'درس'
        verbose_name_plural = 'درس‌ها'

    def __str__(self):
        return f"{self.chapter.name} - {self.name}"

    def get_content(self):
        return LessonContent.objects.filter(lesson=self).first()

    def is_unlocked_for_user(self, user):
        """درس بعدی فقط بعد از تکمیل درس قبلیِ همان فصل باز می‌شود."""
        if not user or not user.is_authenticated:
            return True
        chapter = self.chapter
        if chapter and not chapter.is_unlocked_for_user(user):
            return False
        prev = (Lesson.objects
                .filter(chapter=chapter, is_published=True, order__lt=self.order)
                .order_by('-order').first())
        if prev is None:
            return True
        prog = UserLessonProgress.objects.filter(
            user=user, lesson=prev, status='completed'
        ).first()
        return prog is not None

    def is_completed_for_user(self, user):
        if not user or not user.is_authenticated:
            return False
        return UserLessonProgress.objects.filter(
            user=user, lesson=self, status='completed'
        ).exists()


class LessonContent(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='content', verbose_name='درس')


    introduction = RichTextField(help_text="Hook to engage the learner", verbose_name='مقدمه')
    introduction_audio = models.FileField(upload_to='lesson_audio/intros/', blank=True, null=True)
    learning_objectives = models.JSONField(default=list)
    grammar_notes = RichTextField(blank=True)
    grammar_examples = models.JSONField(default=list)
    example_sentences = models.JSONField(default=list)
    featured_image = models.ImageField(upload_to='lesson_images/', blank=True, null=True)
    featured_video = models.FileField(upload_to='lesson_videos/', blank=True, null=True)
    featured_video_url = models.URLField(blank=True, null=True)
    summary = RichTextField()
    key_takeaways = models.JSONField(default=list)
    is_interactive = models.BooleanField(default=True)
    allow_skip = models.BooleanField(default=False)
    display_options = models.JSONField(default=dict, blank=True, verbose_name='تنظیمات نمایش')


    reading_text = models.TextField(blank=True, null=True, help_text="Reading passage text", verbose_name='متن خواندن')
    reading_translation = models.TextField(blank=True, null=True, help_text="Persian translation of reading text",
                                           verbose_name='ترجمه متن')
    reading_notes = models.TextField(blank=True, null=True, help_text="Key notes about the reading",
                                     verbose_name='نکات متن')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class GrammarPoint(models.Model):
    """یک نکتهٔ گرامری (الهام‌گرفته از Grammar in Use) مرتبط با یک درس."""
    LEVELS = [
        ('A1', 'A1 - مبتدی'),
        ('A2', 'A2 - مقدماتی'),
        ('B1', 'B1 - متوسط'),
    ]
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='grammar_points',
                               verbose_name='درس')
    title = models.CharField(max_length=200, verbose_name='عنوان گرامر')
    title_fa = models.CharField(max_length=200, blank=True, verbose_name='عنوان فارسی')
    level = models.CharField(max_length=2, choices=LEVELS, default='A1', verbose_name='سطح')
    structure = models.CharField(max_length=300, blank=True, verbose_name='فرمول/ساختار',
                                 help_text='مثلاً: Subject + am/is/are + ...')
    explanation = RichTextField(verbose_name='توضیح کامل')
    examples = models.JSONField(default=list, verbose_name='مثال‌ها',
                                help_text='هر آیتم: {"en": "...", "fa": "..."}')
    common_mistakes = models.TextField(blank=True, verbose_name='اشتباهات رایج')
    usage_tips = models.TextField(blank=True, verbose_name='نکات کاربردی')
    order = models.IntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        ordering = ['lesson__chapter__world__order', 'lesson__chapter__order', 'lesson__order', 'order']
        verbose_name = 'نکته گرامری'
        verbose_name_plural = 'نکات گرامری'

    def __str__(self):
        return f'{self.title} ({self.lesson.name})'


class VocabularyCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام')
    name_fa = models.CharField(max_length=100, blank=True, verbose_name='نام به فارسی')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class", verbose_name='آیکون')
    order = models.IntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        ordering = ['order']
        verbose_name = 'دسته‌بندی واژگان'
        verbose_name_plural = 'دسته‌بندی‌های واژگان'

    def __str__(self):
        return self.name


class Vocabulary(models.Model):
    DIFFICULTY_LEVELS = [
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
    ]

    word = models.CharField(max_length=100, db_index=True, verbose_name='کلمه')
    pronunciation = models.CharField(max_length=200, blank=True, help_text="IPA or phonetic spelling", verbose_name='تلفظ')
    meaning = models.TextField(verbose_name='معنی')
    meaning_fa = models.TextField(blank=True, verbose_name='معنی به فارسی')
    part_of_speech = models.CharField(max_length=50, blank=True, verbose_name='نوع کلمه')
    difficulty = models.CharField(max_length=2, choices=DIFFICULTY_LEVELS, default='A1', verbose_name='سطح دشواری')
    categories = models.ManyToManyField(VocabularyCategory, related_name='vocabulary', verbose_name='دسته‌بندی‌ها')

    audio_uk = models.FileField(upload_to='vocabulary/audio/uk/', blank=True, null=True, verbose_name='تلفظ بریتیش')
    audio_us = models.FileField(upload_to='vocabulary/audio/us/', blank=True, null=True, verbose_name='تلفظ آمریکن')
    audio_example = models.FileField(upload_to='vocabulary/audio/examples/', blank=True, null=True, verbose_name='مثال صوتی')

    image = models.ImageField(upload_to='vocabulary/images/', blank=True, null=True, verbose_name='تصویر')

    usage_count = models.IntegerField(default=0, verbose_name='تعداد استفاده')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['difficulty', 'word']
        verbose_name = 'واژه'
        verbose_name_plural = 'واژگان'
        indexes = [
            models.Index(fields=['word', 'difficulty']),
        ]

    def __str__(self):
        return f"{self.word} ({self.get_difficulty_display()})"

    def get_random_example(self):
        return self.examples.order_by('?').first()


class VocabularyExample(models.Model):
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='examples', verbose_name='واژه')
    sentence = models.TextField(verbose_name='جمله')
    sentence_fa = models.TextField(blank=True, verbose_name='جمله به فارسی')
    audio = models.FileField(upload_to='vocabulary/examples/audio/', blank=True, null=True, verbose_name='فایل صوتی')
    order = models.IntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        ordering = ['order']
        verbose_name = 'مثال واژه'
        verbose_name_plural = 'مثال‌های واژه'

    def __str__(self):
        return self.sentence[:50]


class Dialogue(models.Model):
    DIFFICULTY_LEVELS = [
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='dialogues', verbose_name='درس')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    title_fa = models.CharField(max_length=200, blank=True, verbose_name='عنوان به فارسی')
    description = models.TextField(verbose_name='توضیحات')
    difficulty = models.CharField(max_length=2, choices=DIFFICULTY_LEVELS, default='A1', verbose_name='سطح دشواری')
    scenario_audio = models.FileField(upload_to='dialogue/scenario_audio/', blank=True, null=True, verbose_name='فایل صوتی سناریو')
    background_image = models.ImageField(upload_to='dialogue/backgrounds/', blank=True, null=True, verbose_name='تصویر پس‌زمینه')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.IntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        ordering = ['order']
        verbose_name = 'دیالوگ'
        verbose_name_plural = 'دیالوگ‌ها'

    def __str__(self):
        return self.title


class DialogueScene(models.Model):
    dialogue = models.ForeignKey(Dialogue, on_delete=models.CASCADE, related_name='scenes', verbose_name='دیالوگ')
    order = models.IntegerField(verbose_name='ترتیب')
    character = models.CharField(max_length=100, verbose_name='شخصیت')
    character_avatar = models.ImageField(upload_to='dialogue/avatars/', blank=True, null=True, verbose_name='آواتار شخصیت')
    message = models.TextField(verbose_name='پیام')
    message_fa = models.TextField(blank=True, verbose_name='پیام به فارسی')
    audio = models.FileField(upload_to='dialogue/audio/', blank=True, null=True, verbose_name='فایل صوتی')
    is_user_turn = models.BooleanField(default=False, verbose_name='نوبت کاربر')

    class Meta:
        ordering = ['order']
        verbose_name = 'صحنه دیالوگ'
        verbose_name_plural = 'صحنه‌های دیالوگ'

    def __str__(self):
        return f"{self.dialogue.title} - Scene {self.order}"


class DialogueChoice(models.Model):
    scene = models.ForeignKey(DialogueScene, on_delete=models.CASCADE, related_name='choices', verbose_name='صحنه')
    choice_text = models.TextField(verbose_name='متن انتخاب')
    choice_text_fa = models.TextField(blank=True, verbose_name='متن انتخاب به فارسی')
    is_correct = models.BooleanField(default=False, verbose_name='صحیح')
    feedback = models.TextField(blank=True, verbose_name='بازخورد')
    feedback_fa = models.TextField(blank=True, verbose_name='بازخورد به فارسی')
    next_scene = models.ForeignKey(DialogueScene, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='صحنه بعدی')
    xp_reward = models.IntegerField(default=5, verbose_name='پاداش XP')

    def __str__(self):
        return self.choice_text[:50]


class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('fill_blank', 'Fill in the Blank'),
        ('matching', 'Matching'),
        ('ordering', 'Sentence Ordering'),
        ('listening', 'Listening Comprehension'),
        ('writing', 'Writing'),
        ('speaking', 'Speaking'),
        ('dialogue', 'Dialogue Response'),
        ('true_false', 'True/False'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='questions', verbose_name='درس')
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, null=True, blank=True, related_name='questions', verbose_name='کوئیز')

    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, verbose_name='نوع سوال')
    question_text = models.TextField(verbose_name='متن سوال')
    question_text_fa = models.TextField(blank=True, verbose_name='متن سوال به فارسی')
    question_audio = models.FileField(upload_to='questions/audio/', blank=True, null=True, verbose_name='فایل صوتی سوال')
    question_image = models.ImageField(upload_to='questions/images/', blank=True, null=True, verbose_name='تصویر سوال')

    points = models.IntegerField(default=10, verbose_name='امتیاز')
    order = models.IntegerField(default=0, verbose_name='ترتیب')

    blank_answer = models.CharField(max_length=200, blank=True, verbose_name='پاسخ جای خالی')
    matching_pairs = models.JSONField(default=list, blank=True, verbose_name='جفت‌های تطبیق')
    correct_order = models.JSONField(default=list, blank=True, verbose_name='ترتیب صحیح')

    hint = models.TextField(blank=True, verbose_name='راهنما')
    explanation = models.TextField(blank=True, verbose_name='توضیح')
    explanation_fa = models.TextField(blank=True, verbose_name='توضیح به فارسی')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'سوال'
        verbose_name_plural = 'سوالات'

    def __str__(self):
        return f"{self.question_type}: {self.question_text[:50]}"


class QuestionChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices', verbose_name='سوال')
    choice_text = models.CharField(max_length=500, verbose_name='متن گزینه')
    choice_text_fa = models.CharField(max_length=500, blank=True, verbose_name='متن گزینه به فارسی')
    is_correct = models.BooleanField(default=False, verbose_name='صحیح')
    order = models.IntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        ordering = ['order']
        verbose_name = 'گزینه سوال'
        verbose_name_plural = 'گزینه‌های سوال'

    def __str__(self):
        return self.choice_text[:50]


class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz', verbose_name='درس')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    passing_score = models.IntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نمره قبولی')
    time_limit_minutes = models.IntegerField(default=10, verbose_name='زمان محدود (دقیقه)')
    max_attempts = models.IntegerField(default=3, verbose_name='حداکثر تلاش')
    shuffle_questions = models.BooleanField(default=False, verbose_name='به هم ریختن سوالات')
    xp_reward = models.IntegerField(default=30, verbose_name='پاداش XP')
    coin_reward = models.IntegerField(default=15, verbose_name='پاداش سکه')
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')

    class Meta:
        verbose_name = 'کوئیز'
        verbose_name_plural = 'کوئیزها'

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.questions.all()


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_quiz_attempts', verbose_name='کاربر')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', verbose_name='کوئیز')
    score = models.IntegerField(verbose_name='نمره')
    passed = models.BooleanField(default=False, verbose_name='پاس شده')
    answers = models.JSONField(default=dict, verbose_name='پاسخ‌ها')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0, verbose_name='زمان صرف شده (ثانیه)')

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'تلاش کوئیز'
        verbose_name_plural = 'تلاش‌های کوئیز'

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}%"

    def is_passing(self):
        return self.score >= self.quiz.passing_score


class Exam(models.Model):
    EXAM_TYPES = [
        ('chapter', 'Chapter Exam'),
        ('world', 'World Exam'),
        ('final', 'Final Exam'),
    ]

    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, verbose_name='نوع امتحان')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, null=True, blank=True, related_name='exams', verbose_name='فصل')
    world = models.ForeignKey(World, on_delete=models.CASCADE, null=True, blank=True, related_name='exams', verbose_name='جهان')

    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات')
    passing_score = models.IntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نمره قبولی')
    time_limit_minutes = models.IntegerField(default=60, verbose_name='زمان محدود (دقیقه)')
    max_attempts = models.IntegerField(default=3, verbose_name='حداکثر تلاش')
    questions_count = models.IntegerField(default=20, verbose_name='تعداد سوالات')
    randomize_questions = models.BooleanField(default=True, verbose_name='به هم ریختن سوالات')
    xp_reward = models.IntegerField(default=200, verbose_name='پاداش XP')
    coin_reward = models.IntegerField(default=50, verbose_name='پاداش سکه')
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')

    class Meta:
        verbose_name = 'امتحان'
        verbose_name_plural = 'امتحانات'

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.exam_questions.all().order_by('?') if self.randomize_questions else self.exam_questions.all()


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions', verbose_name='امتحان')
    question = models.TextField(verbose_name='سوال')
    question_fa = models.TextField(blank=True, verbose_name='سوال به فارسی')
    question_type = models.CharField(max_length=20, choices=Question.QUESTION_TYPES, verbose_name='نوع سوال')
    correct_answer = models.TextField(verbose_name='پاسخ صحیح')
    options = models.JSONField(default=list, verbose_name='گزینه‌ها')
    points = models.IntegerField(default=10, verbose_name='امتیاز')
    order = models.IntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        ordering = ['order']
        verbose_name = 'سوال امتحان'
        verbose_name_plural = 'سوالات امتحان'

    def __str__(self):
        return self.question[:50]


class ExamAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_exam_attempts', verbose_name='کاربر')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts', verbose_name='امتحان')
    score = models.IntegerField(verbose_name='نمره')
    passed = models.BooleanField(default=False, verbose_name='پاس شده')
    answers = models.JSONField(default=dict, verbose_name='پاسخ‌ها')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0, verbose_name='زمان صرف شده (ثانیه)')

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'تلاش امتحان'
        verbose_name_plural = 'تلاش‌های امتحان'

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} - {self.score}%"


class ExamSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_sessions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=100, unique=True)
    answers = models.JSONField(default=dict)
    time_spent = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)
    attempt_id = models.IntegerField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} - {self.exam.title}"


class UserLessonProgress(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_lesson_progress', verbose_name='کاربر')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress', verbose_name='درس')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name='وضعیت')
    progress_percentage = models.FloatField(default=0, verbose_name='درصد پیشرفت')
    quiz_score = models.IntegerField(null=True, blank=True, verbose_name='نمره کوئیز')
    quiz_passed = models.BooleanField(default=False, verbose_name='کوئیز پاس شده')
    xp_earned = models.IntegerField(default=0, verbose_name='XP کسب شده')
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True, verbose_name='آخرین فعالیت')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')

    class Meta:
        unique_together = ['user', 'lesson']
        verbose_name = 'پیشرفت درس'
        verbose_name_plural = 'پیشرفت درس‌ها'

    def __str__(self):
        return f"{self.user.username} - {self.lesson.name} - {self.status}"

    def complete(self):
        self.status = 'completed'
        self.progress_percentage = 100
        self.completed_at = timezone.now()
        self.save()
        if self.xp_earned > 0:
            self.user.add_xp(self.xp_earned, 'lesson_completion', f'Completed lesson: {self.lesson.name}')


class UserChapterProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_chapter_progress', verbose_name='کاربر')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='user_progress', verbose_name='فصل')
    is_completed = models.BooleanField(default=False, verbose_name='تکمیل شده')
    exam_score = models.IntegerField(null=True, blank=True, verbose_name='نمره امتحان')
    exam_passed = models.BooleanField(default=False, verbose_name='امتحان پاس شده')
    lessons_completed = models.IntegerField(default=0, verbose_name='درس‌های تکمیل شده')
    total_lessons = models.IntegerField(default=0, verbose_name='کل درس‌ها')
    xp_earned = models.IntegerField(default=0, verbose_name='XP کسب شده')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')

    class Meta:
        unique_together = ['user', 'chapter']
        verbose_name = 'پیشرفت فصل'
        verbose_name_plural = 'پیشرفت فصل‌ها'

    def __str__(self):
        return f"{self.user.username} - {self.chapter.name}"

    def update_progress(self):
        self.lessons_completed = UserLessonProgress.objects.filter(
            user=self.user, lesson__chapter=self.chapter, status='completed'
        ).count()
        self.total_lessons = self.chapter.lessons.filter(is_published=True).count()
        self.save()
        if self.lessons_completed >= self.total_lessons and self.exam_passed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()


class UserWorldProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_world_progress', verbose_name='کاربر')
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='user_progress', verbose_name='جهان')
    is_completed = models.BooleanField(default=False, verbose_name='تکمیل شده')
    exam_score = models.IntegerField(null=True, blank=True, verbose_name='نمره امتحان')
    exam_passed = models.BooleanField(default=False, verbose_name='امتحان پاس شده')
    chapters_completed = models.IntegerField(default=0, verbose_name='فصل‌های تکمیل شده')
    total_chapters = models.IntegerField(default=0, verbose_name='کل فصل‌ها')
    xp_earned = models.IntegerField(default=0, verbose_name='XP کسب شده')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')
    certificate_issued = models.BooleanField(default=False, verbose_name='گواهی صادر شده')

    class Meta:
        unique_together = ['user', 'world']
        verbose_name = 'پیشرفت جهان'
        verbose_name_plural = 'پیشرفت جهان‌ها'

    def __str__(self):
        return f"{self.user.username} - {self.world.name}"

    def update_progress(self):
        total = self.world.chapters.filter(is_published=True).count()
        self.total_chapters = total
        self.chapters_completed = UserChapterProgress.objects.filter(
            user=self.user, chapter__world=self.world, is_completed=True
        ).count()
        if self.exam_passed and self.chapters_completed >= total and total > 0:
            self.is_completed = True
            if not self.completed_at:
                self.completed_at = timezone.now()
        self.save(update_fields=['total_chapters', 'chapters_completed', 'is_completed', 'completed_at'])


class UserVocabularyProgress(models.Model):
    MASTERY_LEVELS = [
        (0, 'Not Learned'),
        (1, 'Introduced'),
        (2, 'Reviewed'),
        (3, 'Practiced'),
        (4, 'Mastered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_vocabulary_progress', verbose_name='کاربر')
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='user_progress', verbose_name='واژه')
    mastery_level = models.IntegerField(choices=MASTERY_LEVELS, default=0, verbose_name='سطح تسلط')
    mastery_score = models.FloatField(default=0, help_text="0-100 mastery score", verbose_name='نمره تسلط')
    review_count = models.IntegerField(default=0, verbose_name='تعداد مرور')
    correct_count = models.IntegerField(default=0, verbose_name='تعداد صحیح')
    incorrect_count = models.IntegerField(default=0, verbose_name='تعداد غلط')
    last_reviewed = models.DateTimeField(null=True, blank=True, verbose_name='آخرین مرور')
    next_review_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ مرور بعدی')
    forgetting_risk = models.FloatField(default=100, help_text="Risk of forgetting (0-100)", verbose_name='ریسک فراموشی')
    last_accuracy = models.FloatField(default=0, verbose_name='دقت آخر')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'vocabulary']
        verbose_name = 'پیشرفت واژه'
        verbose_name_plural = 'پیشرفت واژگان'
        indexes = [
            models.Index(fields=['user', 'next_review_date']),
            models.Index(fields=['user', 'mastery_score']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.vocabulary.word} - Level {self.mastery_level}"

    def calculate_next_review(self):
        if self.mastery_level == 0:
            self.next_review_date = timezone.now() + timezone.timedelta(days=1)
        elif self.mastery_level == 1:
            self.next_review_date = timezone.now() + timezone.timedelta(days=3)
        elif self.mastery_level == 2:
            self.next_review_date = timezone.now() + timezone.timedelta(days=7)
        elif self.mastery_level == 3:
            self.next_review_date = timezone.now() + timezone.timedelta(days=14)
        else:
            self.next_review_date = timezone.now() + timezone.timedelta(days=30)
        self.save()


class Badge(models.Model):
    BADGE_TYPES = [
        ('milestone', 'Milestone'),
        ('streak', 'Streak'),
        ('mastery', 'Mastery'),
        ('quiz', 'Quiz Excellence'),
        ('world', 'World Completion'),
        ('special', 'Special'),
    ]

    name = models.CharField(max_length=100, verbose_name='نام')
    name_fa = models.CharField(max_length=100, blank=True, verbose_name='نام به فارسی')
    description = models.TextField(verbose_name='توضیحات')
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, verbose_name='نوع مدال')
    icon = models.ImageField(upload_to='badges/', blank=True, null=True, verbose_name='آیکون')
    requirement_type = models.CharField(max_length=50, verbose_name='نوع نیازمندی')
    requirement_value = models.IntegerField(verbose_name='مقدار نیازمندی')
    xp_reward = models.IntegerField(default=50, verbose_name='پاداش XP')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.IntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        ordering = ['order']
        verbose_name = 'مدال'
        verbose_name_plural = 'مدال‌ها'

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_badges', verbose_name='کاربر')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='users', verbose_name='مدال')
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ دریافت')
    is_notified = models.BooleanField(default=False, verbose_name='اطلاع رسانی شده')

    class Meta:
        unique_together = ['user', 'badge']
        verbose_name = 'مدال کاربر'
        verbose_name_plural = 'مدال‌های کاربر'

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_certificates', verbose_name='کاربر')
    world = models.ForeignKey(World, on_delete=models.CASCADE, null=True, blank=True, verbose_name='جهان')
    certificate_number = models.CharField(max_length=100, unique=True, default=uuid.uuid4, verbose_name='شماره گواهی')
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ صادر')
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True, verbose_name='فایل PDF')
    verification_code = models.CharField(max_length=100, unique=True, default=uuid.uuid4, verbose_name='کد تأیید')

    class Meta:
        verbose_name = 'گواهی'
        verbose_name_plural = 'گواهی‌ها'

    def __str__(self):
        return f"Certificate {self.certificate_number} for {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.certificate_number or isinstance(self.certificate_number, uuid.UUID) or self.certificate_number == 'uuid4':
            self.certificate_number = f"LQ-{timezone.localdate().year}-{uuid.uuid4().hex[:8].upper()}"
        if not self.verification_code or isinstance(self.verification_code, uuid.UUID) or self.verification_code == 'uuid4':
            self.verification_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)


class DailyGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_daily_goals', verbose_name='کاربر')
    target_xp = models.IntegerField(default=100, verbose_name='هدف XP')
    target_lessons = models.IntegerField(default=2, verbose_name='هدف درس‌ها')
    target_vocabulary = models.IntegerField(default=5, verbose_name='هدف واژگان')
    current_xp = models.IntegerField(default=0, verbose_name='XP فعلی')
    current_lessons = models.IntegerField(default=0, verbose_name='درس‌های فعلی')
    current_vocabulary = models.IntegerField(default=0, verbose_name='واژگان فعلی')
    goal_date = models.DateField(auto_now_add=True, verbose_name='تاریخ هدف')

    class Meta:
        unique_together = ['user', 'goal_date']
        verbose_name = 'هدف روزانه'
        verbose_name_plural = 'اهداف روزانه'

    def __str__(self):
        return f"{self.user.username} - {self.goal_date}"

    def is_completed(self):
        return (self.current_xp >= self.target_xp and
                self.current_lessons >= self.target_lessons and
                self.current_vocabulary >= self.target_vocabulary)


class CoinTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('earn', 'Earned'),
        ('spend', 'Spent'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_coin_transactions', verbose_name='کاربر')
    amount = models.IntegerField(verbose_name='مقدار')
    transaction_type = models.CharField(max_length=5, choices=TRANSACTION_TYPES, verbose_name='نوع تراکنش')
    source = models.CharField(max_length=100, verbose_name='منبع')
    source_id = models.IntegerField(help_text="ID of the source object", verbose_name='ID منبع')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تراکنش سکه'
        verbose_name_plural = 'تراکنش‌های سکه'

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount} coins"


class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_ai_conversations', verbose_name='کاربر')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='درس')
    context = models.CharField(max_length=200, blank=True, verbose_name='زمینه')
    messages = models.JSONField(default=list, verbose_name='پیام‌ها')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مکالمه AI'
        verbose_name_plural = 'مکالمات AI'

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class WritingSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_writing_submissions', verbose_name='کاربر')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='درس')
    prompt = models.TextField(verbose_name='پرامپت')
    prompt_fa = models.TextField(blank=True, verbose_name='پرامپت به فارسی')
    submission = models.TextField(verbose_name='ارسال')
    ai_feedback = models.JSONField(null=True, blank=True, verbose_name='بازخورد AI')
    grammar_score = models.FloatField(null=True, blank=True, verbose_name='نمره گرامر')
    vocabulary_score = models.FloatField(null=True, blank=True, verbose_name='نمره واژگان')
    coherence_score = models.FloatField(null=True, blank=True, verbose_name='نمره انسجام')
    overall_score = models.FloatField(null=True, blank=True, verbose_name='نمره کلی')
    submitted_at = models.DateTimeField(auto_now_add=True)
    evaluated_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان ارزیابی')

    class Meta:
        verbose_name = 'ارسال نوشتاری'
        verbose_name_plural = 'ارسال‌های نوشتاری'

    def __str__(self):
        return f"{self.user.username} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"


class SpeakingSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_speaking_submissions', verbose_name='کاربر')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='درس')
    prompt = models.TextField(verbose_name='پرامپت')
    prompt_fa = models.TextField(blank=True, verbose_name='پرامپت به فارسی')
    audio_file = models.FileField(upload_to='speaking_submissions/', verbose_name='فایل صوتی')
    transcript = models.TextField(blank=True, verbose_name='متن پیاده شده')
    ai_feedback = models.JSONField(null=True, blank=True, verbose_name='بازخورد AI')
    pronunciation_score = models.FloatField(null=True, blank=True, verbose_name='نمره تلفظ')
    fluency_score = models.FloatField(null=True, blank=True, verbose_name='نمره روانی')
    grammar_score = models.FloatField(null=True, blank=True, verbose_name='نمره گرامر')
    overall_score = models.FloatField(null=True, blank=True, verbose_name='نمره کلی')
    submitted_at = models.DateTimeField(auto_now_add=True)
    evaluated_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان ارزیابی')

    class Meta:
        verbose_name = 'ارسال گفتاری'
        verbose_name_plural = 'ارسال‌های گفتاری'

    def __str__(self):
        return f"{self.user.username} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"


class LearningAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_learning_analytics', verbose_name='کاربر')

    total_xp = models.IntegerField(default=0, verbose_name='کل XP')
    total_coins = models.IntegerField(default=0, verbose_name='کل سکه')
    total_lessons_completed = models.IntegerField(default=0, verbose_name='کل درس‌های تکمیل شده')
    total_quizzes_passed = models.IntegerField(default=0, verbose_name='کل کوئیزهای پاس شده')
    total_exams_passed = models.IntegerField(default=0, verbose_name='کل امتحانات پاس شده')
    vocabulary_learned = models.IntegerField(default=0, verbose_name='واژگان یاد گرفته شده')

    overall_grammar_mastery = models.FloatField(default=0, verbose_name='تسلط کلی گرامر')
    overall_vocabulary_mastery = models.FloatField(default=0, verbose_name='تسلط کلی واژگان')
    overall_speaking_mastery = models.FloatField(default=0, verbose_name='تسلط کلی گفتاری')
    overall_writing_mastery = models.FloatField(default=0, verbose_name='تسلط کلی نوشتاری')

    weak_grammar_areas = models.JSONField(default=list, verbose_name='نقاط ضعف گرامر')
    weak_vocabulary_categories = models.JSONField(default=list, verbose_name='دسته‌بندی‌های ضعف واژگان')
    frequent_mistakes = models.JSONField(default=list, verbose_name='اشتباهات مکرر')

    recommended_lessons = models.JSONField(default=list, verbose_name='درس‌های پیشنهادی')
    predicted_exam_readiness = models.JSONField(default=dict, verbose_name='آمادگی پیش‌بینی شده برای امتحان')

    average_session_duration = models.FloatField(default=0, verbose_name='متوسط زمان جلسه')
    best_learning_time = models.CharField(max_length=10, blank=True, verbose_name='بهترین زمان یادگیری')
    preferred_lesson_types = models.JSONField(default=list, verbose_name='نوع درس‌های ترجیحی')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user']
        verbose_name = 'تحلیل یادگیری'
        verbose_name_plural = 'تحلیل‌های یادگیری'

    def __str__(self):
        return f"Analytics for {self.user.username}"


class QuizSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_sessions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=100, unique=True)
    answers = models.JSONField(default=dict)
    time_spent = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)
    attempt_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"


CEFR_LEVELS = [
    ('A1', 'A1 — Beginner'),
    ('A2', 'A2 — Elementary'),
    ('B1', 'B1 — Intermediate'),
    ('B2', 'B2 — Upper-Intermediate'),
    ('C1', 'C1 — Advanced'),
    ('C2', 'C2 — Proficient'),
]
CEFR_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']


class Idiom(models.Model):
    expression = models.CharField(max_length=200, db_index=True, verbose_name='اصطلاح')
    translation_fa = models.CharField(max_length=300, verbose_name='معنی فارسی')
    definition_en = models.CharField(max_length=400, verbose_name='تعریف انگلیسی')
    example_en = models.TextField(verbose_name='مثال انگلیسی')
    example_fa = models.TextField(blank=True, verbose_name='مثال فارسی')
    level = models.CharField(max_length=2, choices=CEFR_LEVELS, db_index=True, verbose_name='سطح')
    topic = models.CharField(max_length=50, db_index=True, default='daily', verbose_name='موضوع')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['level', 'topic', 'expression']
        verbose_name = 'اصطلاح'
        verbose_name_plural = 'اصطلاحات'
        unique_together = ['expression', 'level']

    def __str__(self):
        return f"{self.expression} ({self.level})"


class UserIdiomProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='idiom_progress', verbose_name='کاربر')
    idiom = models.ForeignKey(Idiom, on_delete=models.CASCADE, related_name='user_progress', verbose_name='اصطلاح')
    mastery_level = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(4)], verbose_name='سطح تسلط')
    mastery_score = models.FloatField(default=0, verbose_name='نمره تسلط')
    review_count = models.IntegerField(default=0, verbose_name='تعداد مرور')
    correct_count = models.IntegerField(default=0, verbose_name='تعداد صحیح')
    incorrect_count = models.IntegerField(default=0, verbose_name='تعداد غلط')
    last_reviewed = models.DateTimeField(null=True, blank=True, verbose_name='آخرین مرور')
    next_review_date = models.DateTimeField(null=True, blank=True, verbose_name='مرور بعدی')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'idiom']
        verbose_name = 'پیشرفت اصطلاح'
        verbose_name_plural = 'پیشرفت اصطلاحات'
        indexes = [models.Index(fields=['user', 'next_review_date'])]

    def __str__(self):
        return f"{self.user_id} - {self.idiom_id}"


class UserLanguageEstimate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='language_estimate', verbose_name='کاربر')
    cefr_level = models.CharField(max_length=2, choices=CEFR_LEVELS, default='A1', verbose_name='سطح')
    source = models.CharField(max_length=20, choices=[('self', 'انتخاب کاربر'), ('placement', 'آزمون تعیین سطح')], default='self', verbose_name='منبع')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سطح زبانی کاربر'
        verbose_name_plural = 'سطح‌های زبانی کاربران'

    def __str__(self):
        return f"{self.user_id} → {self.cefr_level}"


class PlacementAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='placement_attempts', verbose_name='کاربر')
    chosen_level = models.CharField(max_length=2, choices=CEFR_LEVELS, verbose_name='سطح انتخابی')
    quiz = models.JSONField(default=list, verbose_name='سؤال‌ها')
    answers = models.JSONField(default=list, verbose_name='پاسخ‌ها')
    score = models.IntegerField(default=0, verbose_name='نمره')
    verdict = models.CharField(max_length=20, default='pending', verbose_name='نتیجه')
    recommended_level = models.CharField(max_length=2, choices=CEFR_LEVELS, blank=True, verbose_name='سطح پیشنهادی')
    used_ai = models.BooleanField(default=False, verbose_name='ساخته‌شده با AI')
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='پایان')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'آزمون تعیین سطح'
        verbose_name_plural = 'آزمون‌های تعیین سطح'

    def __str__(self):
        return f"{self.user_id} - {self.chosen_level} ({self.verdict})"


class AIChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_chat_messages', verbose_name='کاربر')
    role = models.CharField(max_length=10, choices=[('user', 'کاربر'), ('assistant', 'معلم')], verbose_name='نقش')
    content = models.TextField(verbose_name='متن')
    context_type = models.CharField(max_length=20, blank=True, verbose_name='نوع بافت')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'پیام معلم هوشمند'
        verbose_name_plural = 'پیام‌های معلم هوشمند'
        indexes = [models.Index(fields=['user', 'created_at'])]

    def __str__(self):
        return f"{self.user_id}:{self.role} {self.content[:30]}"


class AIChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_challenges', verbose_name='کاربر')
    source = models.CharField(max_length=10, choices=[('vocab', 'لغت'), ('idiom', 'اصطلاح'), ('mixed', 'ترکیبی')], default='vocab', verbose_name='منبع')
    payload = models.JSONField(default=dict, verbose_name='محتوای چالش')
    answer_index = models.IntegerField(null=True, blank=True, verbose_name='پاسخ کاربر')
    is_correct = models.BooleanField(null=True, blank=True, verbose_name='درست بود')
    xp_awarded = models.BooleanField(default=False, verbose_name='پاداش داده شد')
    used_ai = models.BooleanField(default=False, verbose_name='ساخته‌شده با AI')
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان پاسخ')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'چالش هوشمند'
        verbose_name_plural = 'چالش‌های هوشمند'

    def __str__(self):
        return f"{self.user_id} - {self.source} #{self.id}"
