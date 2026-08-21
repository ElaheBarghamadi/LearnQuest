import json
import os

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

from ..models import (
    World, Chapter, Lesson, LessonContent, Vocabulary,
    VocabularyCategory, Quiz, Exam, Badge, Certificate,
    UserWorldProgress, UserChapterProgress, UserLessonProgress,
    Question, QuestionChoice, QuizAttempt, ExamAttempt
)
from shop.models import Product
from ..forms import (
    WorldForm, ChapterForm, LessonForm, LessonContentForm,
    VocabularyForm, VocabularyCategoryForm, QuizForm, ExamForm, BadgeForm
)

User = get_user_model()


@staff_member_required
def cms_dashboard(request):
    context = {
        'total_worlds': World.objects.count(),
        'total_chapters': Chapter.objects.filter(is_published=True).count(),
        'total_lessons': Lesson.objects.filter(is_published=True).count(),
        'total_vocabulary': Vocabulary.objects.count(),
        'total_users': User.objects.count(),
        'total_products': Product.objects.count(),
        'total_certificates': Certificate.objects.count(),
        'active_users': User.objects.filter(last_active__gte=timezone.now() - timezone.timedelta(days=7)).count(),
        'recent_worlds': World.objects.order_by('-created_at')[:5],
        'recent_lessons': Lesson.objects.select_related('chapter__world').order_by('-created_at')[:10],
        'all_lessons': Lesson.objects.select_related('chapter__world').filter(is_published=True).order_by('chapter__world__order', 'chapter__order', 'order'),
        'title': 'CMS Dashboard'
    }
    return render(request, 'admin_cms/dashboard.html', context)


@staff_member_required
def world_list(request):
    worlds = (World.objects
              .annotate(
                  chapters_count=Count('chapters', distinct=True),
                  lessons_count=Count('chapters__lessons', distinct=True),
                  published_lessons=Count('chapters__lessons',
                                          filter=Q(chapters__lessons__is_published=True),
                                          distinct=True))
              .prefetch_related('chapters__lessons')
              .order_by('order'))

    q = request.GET.get('q', '').strip()
    if q:
        worlds = worlds.filter(Q(name__icontains=q) | Q(name_fa__icontains=q)
                               | Q(description__icontains=q))

    status = request.GET.get('status', '')
    if status == 'published':
        worlds = worlds.filter(is_published=True)
    elif status == 'draft':
        worlds = worlds.filter(is_published=False)

    for world in worlds:
        world.chapters_sorted = sorted(world.chapters.all(), key=lambda c: c.order)

    return render(request, 'admin_cms/worlds/list.html', {
        'worlds': worlds,
        'q': q,
        'status': status,
        'stats': {
            'total': World.objects.count(),
            'published': World.objects.filter(is_published=True).count(),
            'chapters': Chapter.objects.count(),
            'lessons': Lesson.objects.count(),
        },
    })


@staff_member_required
@require_POST
def world_toggle_publish(request, world_id):
    world = get_object_or_404(World, id=world_id)
    world.is_published = not world.is_published
    world.save(update_fields=['is_published', 'updated_at'])
    return JsonResponse({'success': True, 'is_published': world.is_published,
                         'message': f'«{world.name}» ' + ('منتشر شد ✅' if world.is_published else 'به پیش‌نویس برگشت 📝')})


@staff_member_required
@require_POST
def world_move(request, world_id, direction):
    world = get_object_or_404(World, id=world_id)
    step = -1 if direction == 'up' else 1
    if step < 0:
        neighbor = World.objects.filter(order__lt=world.order).order_by('-order').first()
    else:
        neighbor = World.objects.filter(order__gt=world.order).order_by('order').first()
    if neighbor:
        o1, o2 = world.order, neighbor.order
        with transaction.atomic():
            World.objects.filter(pk=world.pk).update(order=-1)
            World.objects.filter(pk=neighbor.pk).update(order=o1)
            World.objects.filter(pk=world.pk).update(order=o2)
        world.order, neighbor.order = o2, o1
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'جابه‌جایی ممکن نیست'}, status=400)


@staff_member_required
def world_create(request):
    if request.method == 'POST':
        form = WorldForm(request.POST, request.FILES)
        if form.is_valid():
            world = form.save()
            messages.success(request, f'World "{world.name}" created!')
            return redirect('admin_cms:world_list')
    else:
        form = WorldForm()
    return render(request, 'admin_cms/worlds/form.html', {'form': form, 'title': 'Create World'})


@staff_member_required
def world_edit(request, world_id):
    world = get_object_or_404(World, id=world_id)
    if request.method == 'POST':
        form = WorldForm(request.POST, request.FILES, instance=world)
        if form.is_valid():
            form.save()
            messages.success(request, f'World "{world.name}" updated!')
            return redirect('admin_cms:world_list')
    else:
        form = WorldForm(instance=world)
    return render(request, 'admin_cms/worlds/edit.html', {
        'form': form, 'world': world, 'chapters': world.chapters.all().order_by('order')
    })


@staff_member_required
def world_delete(request, world_id):
    world = get_object_or_404(World, id=world_id)
    world.delete()
    messages.success(request, 'World deleted!')
    return redirect('admin_cms:world_list')


@staff_member_required
def chapter_create(request, world_id):
    world = get_object_or_404(World, id=world_id)
    if request.method == 'POST':
        form = ChapterForm(request.POST, request.FILES)
        if form.is_valid():
            chapter = form.save(commit=False)
            chapter.world = world
            if Chapter.objects.filter(world=world, order=chapter.order).exists():
                form.add_error('order', f'فصلی با این ترتیب (order={chapter.order}) در این جهان وجود دارد.')
            else:
                try:
                    chapter.save()
                except IntegrityError:
                    form.add_error('order', 'فصلی با این ترتیب در این جهان وجود دارد (تداخل در دیتابیس).')
                else:
                    messages.success(request, f'Chapter "{chapter.name}" created!')
                    return redirect('admin_cms:world_edit', world_id=world.id)
    else:
        form = ChapterForm(initial={'order': world.chapters.count() + 1})
    return render(request, 'admin_cms/chapters/form.html', {'form': form, 'world': world})


@staff_member_required
def chapter_edit(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    if request.method == 'POST':
        form = ChapterForm(request.POST, request.FILES, instance=chapter)
        if form.is_valid():
            if Chapter.objects.filter(world=chapter.world, order=form.cleaned_data['order']) \
                    .exclude(pk=chapter.pk).exists():
                form.add_error('order', 'فصلی با این ترتیب در این جهان وجود دارد.')
            else:
                try:
                    form.save()
                except IntegrityError:
                    form.add_error('order', 'فصلی با این ترتیب در این جهان وجود دارد (تداخل در دیتابیس).')
                else:
                    messages.success(request, f'Chapter "{chapter.name}" updated!')
                    return redirect('admin_cms:world_edit', world_id=chapter.world.id)
    else:
        form = ChapterForm(instance=chapter)
    return render(request, 'admin_cms/chapters/form.html', {
        'form': form, 'chapter': chapter,
        'lessons': chapter.lessons.all().order_by('order'),
    })


@staff_member_required
def chapter_delete(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    world_id = chapter.world.id
    chapter.delete()
    messages.success(request, 'Chapter deleted!')
    return redirect('admin_cms:world_edit', world_id=world_id)


@staff_member_required
@require_POST
def chapter_toggle_publish(request, chapter_id):
    """نمایش/عدم نمایش فصل در سایت (یک‌کلیک، بدون ریلود)."""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    chapter.is_published = not chapter.is_published
    chapter.save(update_fields=['is_published'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'is_published': chapter.is_published})
    messages.success(request,
                     f'Chapter "{chapter.name}" now {"visible" if chapter.is_published else "hidden"}')
    return redirect('admin_cms:world_edit', world_id=chapter.world.id)


@staff_member_required
@require_POST
def lesson_toggle_publish(request, lesson_id):
    """نمایش/عدم نمایش درس در سایت (یک‌کلیک، بدون ریلود)."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    lesson.is_published = not lesson.is_published
    lesson.save(update_fields=['is_published'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'is_published': lesson.is_published})
    messages.success(request,
                     f'Lesson "{lesson.name}" now {"visible" if lesson.is_published else "hidden"}')
    return redirect('admin_cms:chapter_edit', chapter_id=lesson.chapter.id)


@staff_member_required
@require_POST
def vocabulary_toggle_active(request, vocab_id):
    """فعال/غیرفعال کردن واژه (نمایش در سایت)."""
    vocab = get_object_or_404(Vocabulary, id=vocab_id)
    vocab.is_active = not vocab.is_active
    vocab.save(update_fields=['is_active'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'is_active': vocab.is_active})
    messages.success(request,
                     f'Vocabulary "{vocab.word}" now {"active" if vocab.is_active else "inactive"}')
    return redirect('admin_cms:vocabulary_list')


def _save_lesson_content(content_form, lesson):
    c = content_form.save(commit=False)
    c.lesson = lesson
    c.save()
    width = content_form.cleaned_data.get('image_width')
    align = content_form.cleaned_data.get('image_align') or 'center'
    disp = c.display_options if isinstance(c.display_options, dict) else {}
    changed = False
    if width and disp.get('image_width') != width:
        disp['image_width'] = width
        changed = True
    if align in ('right', 'center', 'left') and disp.get('image_align') != align:
        disp['image_align'] = align
        changed = True
    if changed:
        c.display_options = disp
        c.save(update_fields=['display_options'])
    return c


@staff_member_required
def lesson_create(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    if request.method == 'POST':
        form = LessonForm(request.POST)
        content_form = LessonContentForm(request.POST, request.FILES)
        if form.is_valid() and content_form.is_valid():
            with transaction.atomic():
                lesson = form.save(commit=False)
                lesson.chapter = chapter
                if Lesson.objects.filter(chapter=chapter, order=lesson.order).exists():
                    form.add_error('order', f'درسی با این ترتیب (order={lesson.order}) در این فصل وجود دارد.')
                else:
                    try:
                        lesson.save()
                    except IntegrityError:
                        form.add_error('order', 'درسی با این ترتیب در این فصل وجود دارد (تداخل در دیتابیس).')
                    else:
                        _save_lesson_content(content_form, lesson)
                        messages.success(request, f'Lesson "{lesson.name}" created!')
                        return redirect('admin_cms:chapter_edit', chapter_id=chapter.id)
    else:
        form = LessonForm(initial={'order': chapter.lessons.count() + 1})
        content_form = LessonContentForm()
    return render(request, 'admin_cms/lessons/form.html',
                  {'form': form, 'content_form': content_form, 'chapter': chapter,
                   'title': f'New Lesson — {chapter.name}'})


@staff_member_required
def lesson_edit(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    content = LessonContent.objects.filter(lesson=lesson).first()
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        content_form = LessonContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid() and content_form.is_valid():
            with transaction.atomic():
                if Lesson.objects.filter(chapter=lesson.chapter, order=form.cleaned_data['order']) \
                        .exclude(pk=lesson.pk).exists():
                    form.add_error('order', 'درسی با این ترتیب در این فصل وجود دارد.')
                else:
                    try:
                        form.save()
                    except IntegrityError:
                        form.add_error('order', 'درسی با این ترتیب در این فصل وجود دارد (تداخل در دیتابیس).')
                    else:
                        _save_lesson_content(content_form, lesson)
                        messages.success(request, f'Lesson "{lesson.name}" updated!')
                        return redirect('admin_cms:chapter_edit', chapter_id=lesson.chapter.id)
    else:
        form = LessonForm(instance=lesson)
        initial = {}
        if content and isinstance(content.display_options, dict):
            w = content.display_options.get('image_width')
            if isinstance(w, int) and 20 <= w <= 100:
                initial['image_width'] = w
            a = content.display_options.get('image_align')
            if a in ('right', 'center', 'left'):
                initial['image_align'] = a
        content_form = LessonContentForm(instance=content, initial=initial)
    return render(request, 'admin_cms/lessons/form.html',
                  {'form': form, 'content_form': content_form, 'lesson': lesson,
                   'title': f'Edit: {lesson.name}'})


@staff_member_required
def lesson_delete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    chapter_id = lesson.chapter.id
    lesson.delete()
    messages.success(request, 'Lesson deleted!')
    return redirect('admin_cms:chapter_edit', chapter_id=chapter_id)


@staff_member_required
def vocabulary_list(request):
    vocab_list = Vocabulary.objects.all()
    category = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search = request.GET.get('search')

    if category:
        vocab_list = vocab_list.filter(categories__id=category)
    if difficulty:
        vocab_list = vocab_list.filter(difficulty=difficulty)
    if search:
        vocab_list = vocab_list.filter(Q(word__icontains=search) | Q(meaning__icontains=search))

    return render(request, 'admin_cms/vocabulary/list.html', {
        'vocabularies': Paginator(vocab_list, 50).get_page(request.GET.get('page', 1)),
        'categories': VocabularyCategory.objects.all(),
        'current_category': category, 'current_difficulty': difficulty, 'search_query': search
    })


@staff_member_required
def vocabulary_create(request):
    if request.method == 'POST':
        form = VocabularyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vocabulary created!')
            return redirect('admin_cms:vocabulary_list')
    else:
        form = VocabularyForm()
    return render(request, 'admin_cms/vocabulary/form.html', {'form': form, 'title': 'Create Vocabulary'})


@staff_member_required
def vocabulary_edit(request, vocab_id):
    vocab = get_object_or_404(Vocabulary, id=vocab_id)
    if request.method == 'POST':
        form = VocabularyForm(request.POST, request.FILES, instance=vocab)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vocabulary updated!')
            return redirect('admin_cms:vocabulary_list')
    else:
        form = VocabularyForm(instance=vocab)
    return render(request, 'admin_cms/vocabulary/form.html',
                  {'form': form, 'vocabulary': vocab, 'title': 'Edit Vocabulary'})


@staff_member_required
def vocabulary_categories(request):
    if request.method == 'POST':
        form = VocabularyCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created!')
            return redirect('admin_cms:vocabulary_categories')
    else:
        form = VocabularyCategoryForm()
    return render(request, 'admin_cms/vocabulary/categories.html', {
        'categories': VocabularyCategory.objects.all().order_by('order'), 'form': form
    })


def exam_delete(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    exam_title = exam.title
    exam.delete()
    messages.success(request, f'Exam "{exam_title}" deleted successfully!')
    return redirect('admin_cms:exam_list')


def vocabulary_delete(request, vocab_id):
    vocab = get_object_or_404(Vocabulary, id=vocab_id)
    word = vocab.word
    vocab.delete()
    messages.success(request, f'Vocabulary "{word}" deleted successfully!')
    return redirect('admin_cms:vocabulary_list')


def badge_delete(request, badge_id):
    badge = get_object_or_404(Badge, id=badge_id)
    badge_name = badge.name
    badge.delete()
    messages.success(request, f'Badge "{badge_name}" deleted successfully!')
    return redirect('admin_cms:badge_list')


def badge_edit(request, badge_id):
    badge = get_object_or_404(Badge, id=badge_id)

    if request.method == 'POST':
        form = BadgeForm(request.POST, request.FILES, instance=badge)
        if form.is_valid():
            form.save()
            messages.success(request, f'Badge "{badge.name}" updated successfully!')
            return redirect('admin_cms:badge_list')
    else:
        form = BadgeForm(instance=badge)

    context = {
        'form': form,
        'badge': badge,
        'title': f'Edit {badge.name}'
    }
    return render(request, 'admin_cms/badges/form.html', context)

@staff_member_required
def quiz_list(request):
    return render(request, 'admin_cms/quizzes/list.html',
                  {'quizzes': Quiz.objects.select_related('lesson__chapter__world').all()})


@staff_member_required
def quiz_create(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save()
            messages.success(request, f'Quiz "{quiz.title}" created successfully!')
            return redirect('admin_cms:quiz_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuizForm()

    context = {
        'form': form,
        'title': 'Create Quiz'
    }
    return render(request, 'admin_cms/quizzes/form.html', context)
@staff_member_required
def quiz_edit(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated!')
            return redirect('admin_cms:quiz_list')
    else:
        form = QuizForm(instance=quiz)
    return render(request, 'admin_cms/quizzes/form.html', {'form': form, 'quiz': quiz, 'title': 'Edit Quiz'})


@staff_member_required
def quiz_delete(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz.delete()
    messages.success(request, 'Quiz deleted!')
    return redirect('admin_cms:quiz_list')


@staff_member_required
def question_list(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    return render(request, 'admin_cms/quizzes/questions.html',
                  {'quiz': quiz, 'questions': quiz.questions.all().order_by('order')})


@staff_member_required
def question_create(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        question = Question.objects.create(
            quiz=quiz, question_text=request.POST.get('question_text'),
            question_type=request.POST.get('question_type'), points=request.POST.get('points', 10),
            blank_answer=request.POST.get('blank_answer', ''), order=quiz.questions.count() + 1
        )
        if question.question_type == 'mcq':
            for i, text in enumerate(request.POST.getlist('choice_text[]')):
                if text.strip():
                    QuestionChoice.objects.create(
                        question=question, choice_text=text,
                        is_correct=(str(i) == request.POST.get('correct_choice')), order=i
                    )
        messages.success(request, 'Question created!')
        return redirect('admin_cms:question_list', quiz_id=quiz.id)
    return render(request, 'admin_cms/quizzes/question_form.html', {'quiz': quiz})


@staff_member_required
def question_edit(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        question.question_text = request.POST.get('question_text')
        question.question_type = request.POST.get('question_type')
        question.points = request.POST.get('points', 10)
        question.blank_answer = request.POST.get('blank_answer', '')
        question.save()

        if question.question_type == 'mcq':
            question.choices.all().delete()
            for i, text in enumerate(request.POST.getlist('choice_text[]')):
                if text.strip():
                    QuestionChoice.objects.create(
                        question=question, choice_text=text,
                        is_correct=(str(i) == request.POST.get('correct_choice')), order=i
                    )
        messages.success(request, 'Question updated!')
        return redirect('admin_cms:question_list', quiz_id=question.quiz.id)
    return render(request, 'admin_cms/quizzes/question_form.html', {'question': question, 'quiz': question.quiz})


@staff_member_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    quiz_id = question.quiz.id
    question.delete()
    messages.success(request, 'Question deleted!')
    return redirect('admin_cms:question_list', quiz_id=quiz_id)


@staff_member_required
def exam_list(request):
    return render(request, 'admin_cms/exams/list.html', {'exams': Exam.objects.all()})


@staff_member_required
def exam_create(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam created!')
            return redirect('admin_cms:exam_list')
    else:
        form = ExamForm()
    return render(request, 'admin_cms/exams/form.html', {'form': form, 'title': 'Create Exam'})


@staff_member_required
def exam_edit(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam updated!')
            return redirect('admin_cms:exam_list')
    else:
        form = ExamForm(instance=exam)
    return render(request, 'admin_cms/exams/form.html', {'form': form, 'exam': exam, 'title': 'Edit Exam'})


@staff_member_required
def badge_list(request):
    return render(request, 'admin_cms/badges/list.html', {'badges': Badge.objects.all().order_by('order')})


@staff_member_required
def badge_create(request):
    if request.method == 'POST':
        form = BadgeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Badge created!')
            return redirect('admin_cms:badge_list')
    else:
        form = BadgeForm()
    return render(request, 'admin_cms/badges/form.html', {'form': form, 'title': 'Create Badge'})


@staff_member_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    for user in users:
        user.total_lessons = user.academy_lesson_progress.filter(status='completed').count()
    return render(request, 'admin_cms/users/list.html',
                  {'users': Paginator(users, 50).get_page(request.GET.get('page', 1))})


@staff_member_required
def user_progress(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin_cms/users/progress.html', {
        'target_user': user,
        'world_progress': UserWorldProgress.objects.filter(user=user).select_related('world'),
        'lesson_progress': UserLessonProgress.objects.filter(user=user).select_related('lesson')[:50]
    })


@staff_member_required
def analytics_dashboard(request):
    total_users = User.objects.count()
    world_stats = []
    for world in World.objects.filter(is_published=True):
        completed = UserWorldProgress.objects.filter(world=world, is_completed=True).count()
        world_stats.append({'name': world.name, 'completed': completed, 'total': total_users,
                            'percentage': (completed / total_users * 100) if total_users > 0 else 0})

    return render(request, 'admin_cms/analytics/dashboard.html', {
        'total_users': total_users,
        'active_users': User.objects.filter(last_active__gte=timezone.now() - timezone.timedelta(days=7)).count(),
        'total_lessons_completed': UserLessonProgress.objects.filter(status='completed').count(),
        'world_stats': world_stats,
        'daily_completions': []
    })


@staff_member_required
def cms_settings(request):
    return render(request, 'admin_cms/settings.html', {'title': 'CMS Settings'})


from ..models import ExamQuestion


def exam_question_list(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.exam_questions.all().order_by('order')

    context = {
        'exam': exam,
        'questions': questions,
        'title': f'Questions for {exam.title}'
    }
    return render(request, 'admin_cms/exams/questions.html', context)


def exam_question_create(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == 'POST':
        question = ExamQuestion.objects.create(
            exam=exam,
            question=request.POST.get('question'),
            question_type=request.POST.get('question_type'),
            correct_answer=request.POST.get('correct_answer'),
            options=request.POST.getlist('options'),
            points=request.POST.get('points', 10),
            order=exam.exam_questions.count() + 1
        )
        messages.success(request, 'Question created successfully!')
        return redirect('admin_cms:exam_question_list', exam_id=exam.id)

    context = {
        'exam': exam,
        'title': f'Add Question to {exam.title}'
    }
    return render(request, 'admin_cms/exams/question_form.html', context)


def exam_question_edit(request, question_id):
    question = get_object_or_404(ExamQuestion, id=question_id)
    exam = question.exam

    if request.method == 'POST':
        question.question = request.POST.get('question')
        question.question_type = request.POST.get('question_type')
        question.correct_answer = request.POST.get('correct_answer')
        question.options = request.POST.getlist('options')
        question.points = request.POST.get('points', 10)
        question.save()
        messages.success(request, 'Question updated successfully!')
        return redirect('admin_cms:exam_question_list', exam_id=exam.id)

    context = {
        'question': question,
        'exam': exam,
        'title': f'Edit Question'
    }
    return render(request, 'admin_cms/exams/question_form.html', context)


def exam_question_delete(request, question_id):
    question = get_object_or_404(ExamQuestion, id=question_id)
    exam_id = question.exam.id
    question.delete()
    messages.success(request, 'Question deleted successfully!')
    return redirect('admin_cms:exam_question_list', exam_id=exam_id)


import re as _vre

_HEX_RE = _vre.compile(r'^#[0-9a-fA-F]{6}$')
_SCRIPT_RE = _vre.compile(r'<\s*/?\s*script[^>]*>', _vre.I)
_ONATTR_RE = _vre.compile(r'\son\w+\s*=\s*"[^"]*"|\son\w+\s*=\s*\'[^\']*\'|\son\w+\s*=\s*[^\s>]+', _vre.I)

_VE_LESSON_TEXT = {'lesson.name': 'name', 'lesson.name_fa': 'name_fa'}
_VE_LESSON_INT = {'lesson.xp_reward': 'xp_reward', 'lesson.coin_reward': 'coin_reward',
                  'lesson.est_time': 'estimated_time_minutes'}
_VE_CONTENT_TEXT = {'content.introduction': 'introduction', 'content.grammar_notes': 'grammar_notes',
                    'content.reading_text': 'reading_text', 'content.reading_translation': 'reading_translation',
                    'content.reading_notes': 'reading_notes', 'content.summary': 'summary'}
_VE_CONTENT_RICH = {'introduction', 'grammar_notes', 'summary'}
_VE_CONTENT_LIST = {'objectives': 'learning_objectives', 'takeaways': 'key_takeaways',
                    'grammar_examples': 'grammar_examples', 'example_sentences': 'example_sentences'}
_VE_SECTION_KEYS = {'intro', 'vocab', 'grammar', 'reading', 'practice', 'quiz'}
_VE_VOCAB_FIELDS = {'word': 'word', 'pronunciation': 'pronunciation', 'meaning': 'meaning',
                    'meaning_fa': 'meaning_fa'}
_VE_QUIZ_TEXT = {'quiz.title': 'title', 'quiz.description': 'description'}
_VE_QUIZ_SCORE = {'quiz.passing_score': 'passing_score'}
_VE_QUIZ_INT = {'quiz.time_limit_minutes': 'time_limit_minutes', 'quiz.xp_reward': 'xp_reward',
                'quiz.coin_reward': 'coin_reward', 'quiz.max_attempts': 'max_attempts'}
_VE_Q_TEXT = {'question_text': 'question_text', 'explanation': 'explanation', 'hint': 'hint'}
_VE_BLOCK_KINDS = {'note', 'alert', 'tip', 'btn'}


def _ve_clean_blocks(value):
    if not isinstance(value, list) or len(value) > 40:
        return None
    import uuid as _uuid
    out = []
    for raw in value:
        if not isinstance(raw, dict):
            return None
        kind = str(raw.get('kind') or '')
        if kind not in _VE_BLOCK_KINDS:
            return None
        text = str(raw.get('text') or '').strip()[:2000]
        if not text:
            return None
        bid = str(raw.get('id') or '').strip()[:24] or _uuid.uuid4().hex[:12]
        entry = {'id': bid, 'kind': kind, 'text': text}
        if kind == 'btn':
            entry['title'] = str(raw.get('title') or '').strip()[:200]
            entry['body'] = str(raw.get('body') or '').strip()[:6000]
        out.append(entry)
    return out


def _ve_clean_text(value, limit):
    if not isinstance(value, str):
        return None
    return value.strip()[:limit]


def _ve_clean_rich(value):
    if not isinstance(value, str):
        return None
    value = _SCRIPT_RE.sub('', value)
    value = _ONATTR_RE.sub('', value)
    return value.strip()[:50000]


def _ve_clean_list(value, item_limit=2000):
    if not isinstance(value, list) or len(value) > 60:
        return None
    out = []
    for item in value:
        if not isinstance(item, str):
            return None
        out.append(item.strip()[:item_limit])
    return [x for x in out if x]


def _ve_clean_hex(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if _HEX_RE.match(value) else None


def _ve_clean_id_list(value, cap=200):
    if not isinstance(value, list) or len(value) > cap:
        return None
    out = []
    for x in value:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            return None
    return out


@staff_member_required
@require_POST
def lesson_visual_save(request, lesson_id):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)
    updates = payload.get('updates')
    if not isinstance(updates, dict) or len(updates) > 400:
        return JsonResponse({'ok': False, 'error': 'invalid_updates'}, status=400)

    result = {'applied': 0, 'skipped': 0}
    with transaction.atomic():
        lesson = get_object_or_404(Lesson.objects.select_for_update(), id=lesson_id)
        content, _ = LessonContent.objects.get_or_create(lesson=lesson, defaults={
            'introduction': '', 'summary': '',
            'learning_objectives': [], 'grammar_examples': [], 'example_sentences': [],
            'key_takeaways': [],
        })
        lesson_dirty = False
        content_dirty = set()
        display = dict(content.display_options or {})
        styles = dict(display.get('styles') or {})
        quiz = Quiz.objects.filter(lesson=lesson).first()
        quiz_dirty = set()

        for key, value in updates.items():
            if not isinstance(key, str) or len(key) > 80:
                result['skipped'] += 1
                continue
            if key in _VE_LESSON_TEXT:
                cleaned = _ve_clean_text(value, 100)
                if cleaned is None:
                    result['skipped'] += 1
                    continue
                setattr(lesson, _VE_LESSON_TEXT[key], cleaned)
                lesson_dirty = True
                result['applied'] += 1
            elif key in _VE_LESSON_INT:
                try:
                    num = int(value)
                except (TypeError, ValueError):
                    result['skipped'] += 1
                    continue
                if not 0 <= num <= 10000:
                    result['skipped'] += 1
                    continue
                setattr(lesson, _VE_LESSON_INT[key], num)
                lesson_dirty = True
                result['applied'] += 1
            elif key in _VE_CONTENT_TEXT:
                field = _VE_CONTENT_TEXT[key]
                cleaned = _ve_clean_rich(value) if field in _VE_CONTENT_RICH else _ve_clean_text(value, 50000)
                if cleaned is None:
                    result['skipped'] += 1
                    continue
                setattr(content, field, cleaned)
                content_dirty.add(field)
                result['applied'] += 1
            elif key in _VE_CONTENT_LIST:
                cleaned = _ve_clean_list(value)
                if cleaned is None:
                    result['skipped'] += 1
                    continue
                setattr(content, _VE_CONTENT_LIST[key], cleaned)
                content_dirty.add(_VE_CONTENT_LIST[key])
                result['applied'] += 1
            elif key in ('display.accent', 'display.accent2'):
                cleaned = _ve_clean_hex(value)
                if cleaned is None:
                    result['skipped'] += 1
                    continue
                display['accent' if key == 'display.accent' else 'accent2'] = cleaned
                result['applied'] += 1
            elif key in ('display.vocab_order', 'display.excluded_vocab'):
                cleaned = _ve_clean_id_list(value)
                if cleaned is None:
                    result['skipped'] += 1
                    continue
                display['vocab_order' if key == 'display.vocab_order' else 'excluded_vocab'] = cleaned
                result['applied'] += 1
            elif key == 'display.image_width':
                try:
                    width = int(value)
                except (TypeError, ValueError):
                    result['skipped'] += 1
                    continue
                if not 20 <= width <= 100:
                    result['skipped'] += 1
                    continue
                display['image_width'] = width
                result['applied'] += 1
            elif key == 'display.image_align':
                if value not in ('right', 'center', 'left'):
                    result['skipped'] += 1
                    continue
                display['image_align'] = value
                result['applied'] += 1
            elif key.startswith('style.') and key[6:] in _VE_SECTION_KEYS:
                if not isinstance(value, dict):
                    result['skipped'] += 1
                    continue
                entry = {}
                if 'color' in value:
                    c = _ve_clean_hex(value.get('color'))
                    if c is None:
                        result['skipped'] += 1
                        continue
                    entry['color'] = c
                if 'bg' in value:
                    b = _ve_clean_hex(value.get('bg'))
                    if b is None:
                        result['skipped'] += 1
                        continue
                    entry['bg'] = b
                styles[key[6:]] = entry
                result['applied'] += 1
            elif key.startswith('vocab.') or key.startswith('vocabex.'):
                parts = key.split('.')
                if len(parts) < 2 or not parts[1].isdigit():
                    result['skipped'] += 1
                    continue
                vocab = Vocabulary.objects.filter(id=int(parts[1]), is_active=True).first()
                if not vocab:
                    result['skipped'] += 1
                    continue
                if parts[0] == 'vocabex':
                    cleaned = _ve_clean_text(value, 1000)
                    if cleaned is None or not cleaned:
                        result['skipped'] += 1
                        continue
                    example = vocab.examples.first()
                    if example:
                        example.sentence = cleaned
                        example.save(update_fields=['sentence'])
                    else:
                        from ..models import VocabularyExample as _VEx
                        _VEx.objects.create(vocabulary=vocab, sentence=cleaned, order=0)
                    result['applied'] += 1
                else:
                    if len(parts) != 3 or parts[2] not in _VE_VOCAB_FIELDS:
                        result['skipped'] += 1
                        continue
                    limit = 120 if parts[2] == 'word' else 1200
                    cleaned = _ve_clean_text(value, limit)
                    if cleaned is None or (parts[2] == 'word' and not cleaned):
                        result['skipped'] += 1
                        continue
                    setattr(vocab, _VE_VOCAB_FIELDS[parts[2]], cleaned)
                    vocab.save(update_fields=[_VE_VOCAB_FIELDS[parts[2]]])
                    result['applied'] += 1
            elif key == 'new_vocab' or key.startswith('new_vocab.'):
                if not isinstance(value, dict):
                    result['skipped'] += 1
                    continue
                word = _ve_clean_text(str(value.get('word') or ''), 120)
                meaning = _ve_clean_text(str(value.get('meaning') or ''), 1200)
                if not word or not meaning:
                    result['skipped'] += 1
                    continue
                vocab = Vocabulary.objects.create(
                    word=word,
                    pronunciation=_ve_clean_text(str(value.get('pronunciation') or ''), 120) or '',
                    meaning=meaning,
                    meaning_fa=_ve_clean_text(str(value.get('meaning_fa') or ''), 1200) or '',
                    difficulty=lesson.chapter.world.difficulty_level or 'A1',
                    is_active=True,
                )
                category = VocabularyCategory.objects.filter(name__iexact=lesson.name).first()
                if category:
                    vocab.categories.add(category)
                example_text = _ve_clean_text(str(value.get('example') or ''), 1000)
                if example_text:
                    from ..models import VocabularyExample as _VEx
                    _VEx.objects.create(vocabulary=vocab, sentence=example_text, order=0)
                result['applied'] += 1
            elif key == 'quiz.create':
                if not Quiz.objects.filter(lesson=lesson).exists():
                    quiz = Quiz.objects.create(
                        lesson=lesson, title=f'{lesson.name} Quiz', description='',
                        passing_score=70, time_limit_minutes=10, is_published=True)
                result['applied'] += 1
            elif key in _VE_QUIZ_TEXT or key in _VE_QUIZ_INT or key in _VE_QUIZ_SCORE:
                if quiz is None:
                    result['skipped'] += 1
                    continue
                if key in _VE_QUIZ_TEXT:
                    field = _VE_QUIZ_TEXT[key]
                    cleaned = _ve_clean_text(value, 200 if field == 'title' else 4000)
                    if cleaned is None:
                        result['skipped'] += 1
                        continue
                    setattr(quiz, field, cleaned)
                else:
                    field = _VE_QUIZ_SCORE.get(key) or _VE_QUIZ_INT.get(key)
                    try:
                        num = int(value)
                    except (TypeError, ValueError):
                        result['skipped'] += 1
                        continue
                    cap = 100 if key in _VE_QUIZ_SCORE else 100000
                    if not 0 <= num <= cap:
                        result['skipped'] += 1
                        continue
                    setattr(quiz, field, num)
                quiz_dirty.add(field)
                result['applied'] += 1
            elif key == 'display.custom_blocks':
                cleaned = _ve_clean_blocks(value)
                if cleaned is None:
                    result['skipped'] += 1
                    continue
                display['custom_blocks'] = cleaned
                result['applied'] += 1
            elif key.startswith('q.') and not key.startswith('qc.'):
                parts = key.split('.')
                if len(parts) != 3 or not parts[1].isdigit() or quiz is None:
                    result['skipped'] += 1
                    continue
                question = Question.objects.filter(id=int(parts[1]), quiz=quiz).first()
                if not question:
                    result['skipped'] += 1
                    continue
                if parts[2] in _VE_Q_TEXT:
                    cleaned = _ve_clean_text(value, 5000)
                    if cleaned is None or (parts[2] == 'question_text' and not cleaned):
                        result['skipped'] += 1
                        continue
                    setattr(question, _VE_Q_TEXT[parts[2]], cleaned)
                elif parts[2] == 'points':
                    try:
                        num = int(value)
                    except (TypeError, ValueError):
                        result['skipped'] += 1
                        continue
                    if not 1 <= num <= 1000:
                        result['skipped'] += 1
                        continue
                    question.points = num
                    parts = [parts[0], parts[1], 'points']
                else:
                    result['skipped'] += 1
                    continue
                question.save(update_fields=['points'] if parts[2] == 'points' else [_VE_Q_TEXT[parts[2]]])
                result['applied'] += 1
            elif key.startswith('qc.'):
                parts = key.split('.')
                if len(parts) != 3 or not parts[1].isdigit() or quiz is None:
                    result['skipped'] += 1
                    continue
                choice = QuestionChoice.objects.filter(id=int(parts[1]), question__quiz=quiz).first()
                if not choice:
                    result['skipped'] += 1
                    continue
                if parts[2] == 'choice_text':
                    cleaned = _ve_clean_text(value, 500)
                    if cleaned is None or not cleaned:
                        result['skipped'] += 1
                        continue
                    choice.choice_text = cleaned
                    choice.save(update_fields=['choice_text'])
                elif parts[2] == 'is_correct':
                    if not value:
                        result['skipped'] += 1
                        continue
                    QuestionChoice.objects.filter(question=choice.question).update(is_correct=False)
                    choice.is_correct = True
                    choice.save(update_fields=['is_correct'])
                else:
                    result['skipped'] += 1
                    continue
                result['applied'] += 1
            elif key.startswith('new_question.'):
                if quiz is None or not isinstance(value, dict):
                    result['skipped'] += 1
                    continue
                text = _ve_clean_text(str(value.get('question_text') or ''), 2000)
                raw_choices = value.get('choices')
                if not text or not isinstance(raw_choices, list) or not 2 <= len(raw_choices) <= 6:
                    result['skipped'] += 1
                    continue
                choices = []
                for rc in raw_choices:
                    ct = _ve_clean_text(str(rc or ''), 500)
                    if not ct:
                        break
                    choices.append(ct)
                else:
                    try:
                        correct_idx = int(value.get('correct', 0))
                    except (TypeError, ValueError):
                        correct_idx = 0
                    if 0 <= correct_idx < len(choices):
                        last = Question.objects.filter(quiz=quiz).order_by('-order').first()
                        question = Question.objects.create(
                            lesson=lesson, quiz=quiz, question_type='mcq',
                            question_text=text, points=10,
                            order=(last.order + 1) if last else 1)
                        for i, ct in enumerate(choices):
                            QuestionChoice.objects.create(
                                question=question, choice_text=ct,
                                is_correct=(i == correct_idx), order=i + 1)
                        result['applied'] += 1
                        continue
                result['skipped'] += 1
            elif key.startswith('del_question.'):
                qid = key.split('.')[1] if len(key.split('.')) == 2 else ''
                if quiz is None or not qid.isdigit():
                    result['skipped'] += 1
                    continue
                deleted, _ = Question.objects.filter(id=int(qid), quiz=quiz).delete()
                if deleted:
                    result['applied'] += 1
                else:
                    result['skipped'] += 1
            else:
                result['skipped'] += 1

        display['styles'] = styles
        content.display_options = display
        content_dirty.add('display_options')
        if lesson_dirty:
            lesson.save()
        if content_dirty:
            content.save(update_fields=list(content_dirty))
        if quiz is not None and quiz_dirty:
            quiz.save(update_fields=list(quiz_dirty))
    return JsonResponse({'ok': True, **result})


_ST_TEXT = {'name': 100, 'name_fa': 100, 'description': 4000}


@staff_member_required
@require_POST
def academy_visual_save(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)
    updates = payload.get('updates')
    if not isinstance(updates, dict) or len(updates) > 300:
        return JsonResponse({'ok': False, 'error': 'invalid_updates'}, status=400)

    result = {'applied': 0, 'skipped': 0}

    def _reorder(model, scope, ids):
        rows = list(model.objects.filter(**scope))
        by_pk = {o.pk: o for o in rows}
        if any(pk not in by_pk for pk in ids):
            return False
        for o in rows:
            model.objects.filter(pk=o.pk).update(order=100000 + (o.order or 0))
        for i, pk in enumerate(ids):
            model.objects.filter(pk=pk).update(order=i + 1)
        return True

    with transaction.atomic():
        for key, value in updates.items():
            if not isinstance(key, str) or len(key) > 80:
                result['skipped'] += 1
                continue
            parts = key.split('.')
            if parts[0] in ('world', 'chapter', 'lesson') and len(parts) == 3 and parts[1].isdigit() and parts[2] in _ST_TEXT:
                model = {'world': World, 'chapter': Chapter, 'lesson': Lesson}[parts[0]]
                obj = model.objects.select_for_update().filter(id=int(parts[1])).first()
                cleaned = _ve_clean_text(value, _ST_TEXT[parts[2]])
                if obj is None or cleaned is None or (parts[2] == 'name' and not cleaned):
                    result['skipped'] += 1
                    continue
                setattr(obj, parts[2], cleaned)
                obj.save(update_fields=[parts[2]])
                result['applied'] += 1
            elif parts[0] == 'reorder' and len(parts) == 2 and parts[1] in ('worlds', 'chapters', 'lessons'):
                ids = _ve_clean_id_list(value)
                if ids is None or not ids:
                    result['skipped'] += 1
                    continue
                if parts[1] == 'worlds':
                    ok = _reorder(World, {}, ids)
                elif parts[1] == 'chapters':
                    ws = set(Chapter.objects.filter(pk__in=ids).values_list('world_id', flat=True))
                    ok = len(ws) == 1 and _reorder(Chapter, {'world_id': ws.pop()}, ids)
                else:
                    cs = set(Lesson.objects.filter(pk__in=ids).values_list('chapter_id', flat=True))
                    ok = len(cs) == 1 and _reorder(Lesson, {'chapter_id': cs.pop()}, ids)
                result['applied' if ok else 'skipped'] += 1
            elif parts[0] == 'new_chapter' and isinstance(value, dict):
                try:
                    world = World.objects.select_for_update().get(id=int(value.get('world')))
                except (World.DoesNotExist, TypeError, ValueError):
                    result['skipped'] += 1
                    continue
                name = _ve_clean_text(str(value.get('name') or ''), 100) or 'New Chapter'
                last = Chapter.objects.filter(world=world).order_by('-order').first()
                Chapter.objects.create(
                    world=world, name=name, description='Describe this chapter…',
                    order=(last.order + 1) if last else 1, is_published=True)
                result['applied'] += 1
            elif parts[0] == 'new_lesson' and isinstance(value, dict):
                try:
                    chapter = Chapter.objects.select_for_update().get(id=int(value.get('chapter')))
                except (Chapter.DoesNotExist, TypeError, ValueError):
                    result['skipped'] += 1
                    continue
                name = _ve_clean_text(str(value.get('name') or ''), 100) or 'New Lesson'
                last = Lesson.objects.filter(chapter=chapter).order_by('-order').first()
                lesson = Lesson.objects.create(
                    chapter=chapter, name=name, lesson_type='mixed',
                    order=(last.order + 1) if last else 1, is_published=True)
                LessonContent.objects.get_or_create(lesson=lesson, defaults={
                    'introduction': '', 'summary': '',
                    'learning_objectives': [], 'grammar_examples': [],
                    'example_sentences': [], 'key_takeaways': []})
                result['applied'] += 1
            else:
                result['skipped'] += 1
    return JsonResponse({'ok': True, **result})


@staff_member_required
@require_POST
def lesson_visual_upload(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    target = request.POST.get('target', '')
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'ok': False, 'error': 'no_file'}, status=400)
    if file.size > 5 * 1024 * 1024:
        return JsonResponse({'ok': False, 'error': 'too_large'}, status=400)
    content_type = (getattr(file, 'content_type', '') or '').lower()
    ext = os.path.splitext(file.name or '')[1].lower()
    if not content_type.startswith('image/') or ext not in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
        return JsonResponse({'ok': False, 'error': 'bad_type'}, status=400)

    import uuid as _uuid
    fname = f"ve_{lesson_id}_{_uuid.uuid4().hex[:10]}{ext}"
    with transaction.atomic():
        if target == 'featured':
            content, _ = LessonContent.objects.get_or_create(lesson=lesson, defaults={
                'introduction': '', 'summary': '',
                'learning_objectives': [], 'grammar_examples': [], 'example_sentences': [],
                'key_takeaways': [],
            })
            content.featured_image.save(fname, file, save=True)
            return JsonResponse({'ok': True, 'url': content.featured_image.url})
        if target == '__lesson_block__':
            # عکس داخل ویرایشگر بلوکی — در مسیر رسانهٔ درس ذخیره می‌شود
            from django.core.files.storage import default_storage
            from django.conf import settings as dj_settings
            rel = f'lesson_blocks/{fname}'
            saved = default_storage.save(rel, file)
            return JsonResponse({'ok': True, 'url': dj_settings.MEDIA_URL + saved})
        if target.startswith('vocab_') and target[6:].isdigit():
            vocab = get_object_or_404(Vocabulary, id=int(target[6:]), is_active=True)
            vocab.image.save(fname, file, save=True)
            return JsonResponse({'ok': True, 'url': vocab.image.url})
    return JsonResponse({'ok': False, 'error': 'bad_target'}, status=400)


@staff_member_required
def shop_product_list(request):
    from shop.models import Product, Purchase, Category as ShopCategory
    qs = Product.objects.select_related('category').order_by('-is_featured', '-created_at')
    q = request.GET.get('q', '').strip()
    ptype = request.GET.get('type', '').strip()
    status = request.GET.get('status', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q) | Q(effect_type__icontains=q))
    if ptype in dict(Product.PRODUCT_TYPES):
        qs = qs.filter(product_type=ptype)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status == 'featured':
        qs = qs.filter(is_featured=True)

    from django.db.models import Sum, Count
    totals = Product.objects.aggregate(
        total=Count('id'), active=Count('id', filter=Q(is_active=True)),
        featured=Count('id', filter=Q(is_featured=True)),
        sold=Sum('sold_count'))
    revenue = Purchase.objects.filter(status='completed').aggregate(
        coins=Sum('coins_paid'), gems=Sum('gems_paid'), cnt=Count('id'))

    return render(request, 'admin_cms/shop/products.html', {
        'products': Paginator(qs, 20).get_page(request.GET.get('page', 1)),
        'product_types': Product.PRODUCT_TYPES,
        'categories': ShopCategory.objects.all(),
        'q': q, 'current_type': ptype, 'current_status': status,
        'totals': totals, 'revenue': revenue,
    })


@staff_member_required
def shop_product_create(request):
    from shop.forms import ProductForm
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                product = form.save()
            messages.success(request, f'Product "{product.name}" created!')
            return redirect('admin_cms:shop_product_list')
    else:
        form = ProductForm(initial={'is_active': True})
    return render(request, 'admin_cms/shop/product_form.html',
                  {'form': form, 'title': 'Create Product'})


@staff_member_required
def shop_product_edit(request, product_id):
    from shop.forms import ProductForm
    from shop.models import Product
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            with transaction.atomic():
                product = form.save()
            messages.success(request, f'Product "{product.name}" updated!')
            return redirect('admin_cms:shop_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_cms/shop/product_form.html',
                  {'form': form, 'product': product, 'title': f'Edit: {product.name}'})


@require_POST
@staff_member_required
def shop_product_toggle(request, product_id):
    from shop.models import Product
    with transaction.atomic():
        product = get_object_or_404(Product.objects.select_for_update(), id=product_id)
        product.is_active = not product.is_active
        product.save(update_fields=['is_active'])
    messages.success(request, f'Product "{product.name}" is now {"active" if product.is_active else "inactive"}.')
    return redirect(request.META.get('HTTP_REFERER') or 'admin_cms:shop_product_list')


@require_POST
@staff_member_required
def shop_product_delete(request, product_id):
    from shop.models import Product
    from django.db.models import ProtectedError
    product = get_object_or_404(Product, id=product_id)
    name = product.name
    try:
        with transaction.atomic():
            product.delete()
        messages.success(request, f'Product "{name}" deleted.')
    except ProtectedError:
        messages.error(request, f'«{name}» خرید دارد و قابل حذف نیست؛ به‌جایش غیرفعالش کنید.')
    return redirect('admin_cms:shop_product_list')


@staff_member_required
def certificate_manage(request):
    from ..models import Certificate
    qs = Certificate.objects.select_related('user', 'world').order_by('-issued_at')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(certificate_number__icontains=q))
    worlds = World.objects.all().order_by('order', 'id')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        world_id = request.POST.get('world_id') or ''
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            messages.error(request, f'کاربری با نام «{username}» پیدا نشد.')
        elif world_id and not world_id.isdigit():
            messages.error(request, 'جهان انتخاب‌شده معتبر نیست.')
        else:
            world = World.objects.filter(id=int(world_id)).first() if world_id else None
            if world_id and not world:
                messages.error(request, 'جهان انتخاب‌شده معتبر نیست.')
            else:
                with transaction.atomic():
                    cert, created = Certificate.objects.get_or_create(user=user, world=world)
                    if world:
                        wp, _ = UserWorldProgress.objects.get_or_create(user=user, world=world)
                        if not wp.certificate_issued:
                            wp.certificate_issued = True
                            wp.save(update_fields=['certificate_issued'])
                if created:
                    messages.success(request, f'گواهی «{cert.certificate_number}» برای {user.username} صادر شد.')
                else:
                    messages.info(request, f'گواهی «{cert.certificate_number}» از قبل برای {user.username} صادر شده بود.')
                return redirect('admin_cms:certificate_manage')

    return render(request, 'admin_cms/certificates/list.html', {
        'certificates': Paginator(qs, 25).get_page(request.GET.get('page', 1)),
        'worlds': worlds, 'q': q,
    })


from blog.models import Article as BlogArticle, Category as BlogCategory
from blog.forms import ArticleForm as BlogArticleForm, CategoryQuickForm as BlogCategoryQuickForm


@staff_member_required
def blog_article_list(request):
    qs = BlogArticle.objects.select_related('category').order_by('-published_at', '-id')
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('cat', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(excerpt__icontains=q))
    if cat and cat.isdigit():
        qs = qs.filter(category_id=int(cat))
    return render(request, 'admin_cms/blog/list.html', {
        'articles': Paginator(qs, 20).get_page(request.GET.get('page', 1)),
        'categories': BlogCategory.objects.all().order_by('name'),
        'q': q, 'cat': cat,
        'total': BlogArticle.objects.count(),
    })


def _blog_article_save(request, form, article_id=None):
    if form.is_valid():
        article = form.save()
        messages.success(request, f'مقالهٔ «{article.title}» {"ویرایش" if article_id else "منتشر"} شد.')
        return redirect('admin_cms:blog_article_list')
    return None


@staff_member_required
def blog_article_create(request):
    if request.method == 'POST':
        form = BlogArticleForm(request.POST, request.FILES)
        resp = _blog_article_save(request, form)
        if resp:
            return resp
    else:
        from django.utils import timezone as _tz
        form = BlogArticleForm(initial={'published_at': _tz.localtime(_tz.now()).strftime('%Y-%m-%dT%H:%M')})
    return render(request, 'admin_cms/blog/form.html', {'form': form, 'title': 'مقالهٔ جدید'})


@staff_member_required
@require_POST
def blog_image_upload(request):
    """آپلود عکس داخل متن مقاله — با AJAX از ویرایشگر."""
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'ok': False, 'error': 'no_file'}, status=400)
    if file.size > 5 * 1024 * 1024:
        return JsonResponse({'ok': False, 'error': 'too_large'}, status=400)
    content_type = (getattr(file, 'content_type', '') or '').lower()
    ext = os.path.splitext(file.name or '')[1].lower()
    if not content_type.startswith('image/') or ext not in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
        return JsonResponse({'ok': False, 'error': 'bad_type'}, status=400)

    from django.core.files.storage import default_storage
    from django.conf import settings as dj_settings
    import uuid as _uuid
    fname = f'blog_inline_{_uuid.uuid4().hex[:10]}{ext}'
    rel = f'blog_images/{fname}'
    default_storage.save(rel, file)
    return JsonResponse({'ok': True, 'url': dj_settings.MEDIA_URL + rel})


@staff_member_required
def blog_article_edit(request, article_id):
    article = get_object_or_404(BlogArticle, id=article_id)
    if request.method == 'POST':
        form = BlogArticleForm(request.POST, request.FILES, instance=article)
        resp = _blog_article_save(request, form, article_id)
        if resp:
            return resp
    else:
        form = BlogArticleForm(instance=article, initial={
            'published_at': article.published_at.strftime('%Y-%m-%dT%H:%M') if article.published_at else ''
        })
    return render(request, 'admin_cms/blog/form.html', {'form': form, 'article': article, 'title': f'ویرایش: {article.title}'})


@staff_member_required
@require_POST
def blog_article_delete(request, article_id):
    article = get_object_or_404(BlogArticle, id=article_id)
    article.delete()
    messages.success(request, 'مقاله حذف شد.')
    return redirect('admin_cms:blog_article_list')


@staff_member_required
@require_POST
def blog_category_quick_create(request):
    form = BlogCategoryQuickForm(request.POST)
    if form.is_valid():
        cat = form.save()
        messages.success(request, f'دستهٔ «{cat.name}» ساخته شد.')
    else:
        messages.error(request, 'ساخت دسته نامعتبر بود.')
    return redirect(request.POST.get('next') or 'admin_cms:blog_article_list')
