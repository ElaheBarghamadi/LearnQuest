from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.urls import reverse
from django.views.decorators.http import require_http_methods
import json
import uuid

from .models import (
    World, Chapter, Lesson, LessonContent, Vocabulary, GrammarPoint,
    VocabularyCategory, Dialogue, DialogueScene, DialogueChoice,
    Question, Quiz, QuizAttempt,
    Exam, ExamQuestion, ExamAttempt, ExamSession,
    UserLessonProgress, UserChapterProgress, UserWorldProgress,
    UserVocabularyProgress, Badge, UserBadge, Certificate,
    DailyGoal, CoinTransaction, WritingSubmission, SpeakingSubmission, QuizSession
)


def grammar_hub(request):
    """فهرست گرامرها درس‌به‌درس (الهام‌گرفته از Grammar in Use) گروه‌بندی‌شده بر اساس جهان."""
    level_filter = request.GET.get('level', '')
    if level_filter not in ('A1', 'A2', 'B1'):
        level_filter = ''

    worlds = World.objects.filter(is_published=True).order_by('order')
    data = []
    for w in worlds:
        chapters = []
        for ch in w.chapters.filter(is_published=True).order_by('order'):
            lessons = []
            for l in ch.lessons.filter(is_published=True).order_by('order'):
                gps = GrammarPoint.objects.filter(lesson=l).order_by('order')
                if level_filter:
                    gps = gps.filter(level=level_filter)
                if gps.exists():
                    lessons.append({'lesson': l, 'grammar_points': gps})
            if lessons:
                chapters.append({'chapter': ch, 'lessons': lessons})
        data.append({'world': w, 'chapters': chapters})
    levels = ['A1', 'A2', 'B1']
    return render(request, 'language_academy/grammar_hub.html', {
        'worlds_data': data,
        'levels': levels,
        'level_filter': level_filter,
        'total': GrammarPoint.objects.count(),
        'title': 'Grammar Hub — LearnQuest',
    })


def _grant_pass_rewards_once(user, rewardable, kind):
    from economy.services import grant_xp, grant_coins
    period_key = f'{kind}:{rewardable.id}'
    r_xp = grant_xp(user, rewardable.xp_reward, source=f'{kind}_pass', source_id=rewardable.id,
                    rule_code=f'{kind}_pass', period_key=period_key)
    if r_xp.get('already'):
        return 0, 0, False
    coins = 0
    if rewardable.coin_reward:
        r_c = grant_coins(user, rewardable.coin_reward, source=f'{kind}_pass', source_id=rewardable.id,
                          idempotency_key=f'{kind}coin:{user.pk}:{rewardable.id}')
        coins = r_c.get('granted', 0)
    return r_xp.get('granted', 0), coins, True





def world_map(request):
    worlds = World.objects.filter(is_published=True).order_by('order')
    authed = request.user.is_authenticated

    for world in worlds:
        progress = UserWorldProgress.objects.filter(user=request.user, world=world).first() if authed else None
        world.is_completed = progress.is_completed if progress else False
        world.completion_percentage = world.get_completion_percentage(request.user) if authed else 0
        world.xp_earned = progress.xp_earned if progress else 0

        world.is_locked = False

    today_goal = None
    if authed:
        today_goal, _ = DailyGoal.objects.get_or_create(
            user=request.user,
            goal_date=timezone.localdate(),
            defaults={'target_xp': 100, 'target_lessons': 2, 'target_vocabulary': 5}
        )

    exclusive_lessons = []
    from shop.models import Product as _Prod
    from shop.services import has_unlock as _has_unlock
    for l in (Lesson.objects.filter(is_exclusive=True, is_published=True)
              .select_related('chapter__world').order_by('chapter__world__order', 'order')):
        prod = _Prod.objects.filter(is_active=True, effect_type='exclusive_lesson',
                                    effect_payload__lesson_id=l.id).first()
        exclusive_lessons.append({
            'lesson': l,
            'owned': authed and _has_unlock(request.user, 'exclusive_lesson', lesson_id=l.id),
            'product': prod,
        })

    context = {
        'worlds': worlds,
        'exclusive_lessons': exclusive_lessons,
        'total_xp': request.user.xp if authed else 0,
        'total_coins': request.user.coins if authed else 0,
        'streak': request.user.streak if authed else 0,
        'daily_goal': today_goal,
        'is_guest': not authed,
        'visual_edit': bool(request.user.is_staff and request.GET.get('edit') == '1'),
        've_fab': True,
        'title': 'LearnQuest Language Academy'
    }
    return render(request, 'language_academy/world_map.html', context)


def world_detail(request, world_id):
    world = get_object_or_404(World, id=world_id, is_published=True)
    authed = request.user.is_authenticated

    chapters = world.chapters.filter(is_published=True).order_by('order')

    for chapter in chapters:
        progress = UserChapterProgress.objects.filter(user=request.user, chapter=chapter).first() if authed else None
        chapter.is_completed = progress.is_completed if progress else False
        chapter.completion_percentage = ((progress.lessons_completed / progress.total_lessons * 100)
                                         if progress and progress.total_lessons > 0 else 0)
        chapter.is_locked = False

    world_progress = UserWorldProgress.objects.filter(user=request.user, world=world).first() if authed else None

    context = {
        'world': world,
        'chapters': chapters,
        'world_progress': world_progress,
        'is_guest': not authed,
        'visual_edit': bool(request.user.is_staff and request.GET.get('edit') == '1'),
        've_fab': True,
        'title': f'{world.name} - LearnQuest'
    }
    return render(request, 'language_academy/world_detail.html', context)


@login_required
def chapter_detail(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id, is_published=True)

    lessons = chapter.lessons.filter(is_published=True).order_by('order')

    for lesson in lessons:
        progress = UserLessonProgress.objects.filter(user=request.user, lesson=lesson).first()
        lesson.status = progress.status if progress else 'not_started'
        lesson.progress_percentage = progress.progress_percentage if progress else 0

    chapter_progress, _ = UserChapterProgress.objects.get_or_create(user=request.user, chapter=chapter)
    chapter_progress.update_progress()

    chapter_exam = Exam.objects.filter(exam_type='chapter', chapter=chapter, is_published=True).first()
    exam_attempt = ExamAttempt.objects.filter(user=request.user, exam=chapter_exam,
                                              passed=True).first() if chapter_exam else None

    context = {
        'chapter': chapter,
        'lessons': lessons,
        'chapter_progress': chapter_progress,
        'chapter_exam': chapter_exam,
        'exam_attempt': exam_attempt,
        'visual_edit': bool(request.user.is_staff and request.GET.get('edit') == '1'),
        've_fab': True,
        'title': f'{chapter.name} - LearnQuest'
    }
    return render(request, 'language_academy/chapter_detail.html', context)


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
    content = lesson.get_content()

    if getattr(lesson, 'is_exclusive', False):
        from shop.services import has_unlock
        if not has_unlock(request.user, 'exclusive_lesson', lesson_id=lesson.id):
            from shop.models import Product as _Prod
            prod = _Prod.objects.filter(is_active=True, effect_type='exclusive_lesson',
                                        effect_payload__lesson_id=lesson.id).first()
            messages.warning(request, '🔒 This is an exclusive lesson — grab its ticket to unlock it! 🛒')
            if prod:
                return redirect('shop:product', slug=prod.slug)
            return redirect('shop:home')

    progress, _ = UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    if progress.status == 'not_started':
        progress.status = 'in_progress'
        progress.save()

    quiz = Quiz.objects.filter(lesson=lesson, is_published=True).first()
    quiz_attempt = QuizAttempt.objects.filter(user=request.user, quiz=quiz, passed=True).first() if quiz else None

    vocab_qs = Vocabulary.objects.filter(is_active=True, categories__name__iexact=lesson.name).distinct()
    if not vocab_qs.exists():
        vocab_qs = Vocabulary.objects.filter(is_active=True, categories__name__icontains=lesson.name).distinct()
    vocab_list = list(vocab_qs[:12])
    if len(vocab_list) < 8:
        seen = {v.pk for v in vocab_list}
        extras = Vocabulary.objects.filter(
            is_active=True, difficulty=lesson.chapter.world.difficulty_level
        ).exclude(pk__in=seen).order_by('?')[:12 - len(vocab_list)]
        vocab_list.extend(extras)

    display = content.display_options if (content and isinstance(content.display_options, dict)) else {}
    excluded = display.get('excluded_vocab') or []
    if excluded:
        vocab_list = [v for v in vocab_list if v.pk not in excluded]
    vocab_order = [int(x) for x in (display.get('vocab_order') or []) if str(x).isdigit()]
    if vocab_order:
        rank = {pk: i for i, pk in enumerate(vocab_order)}
        vocab_list.sort(key=lambda v: (rank.get(v.pk, 10000), v.pk))

    dstyles = display.get('styles') if isinstance(display.get('styles'), dict) else {}
    image_width = display.get('image_width')
    image_width = image_width if isinstance(image_width, int) and 20 <= image_width <= 100 else 100
    image_align = display.get('image_align')
    if image_align not in ('right', 'center', 'left'):
        image_align = 'center'
    visual_edit = bool(request.user.is_staff and request.GET.get('edit') == '1')

    custom_blocks = display.get('custom_blocks') if isinstance(display.get('custom_blocks'), list) else []
    custom_blocks = [b for b in custom_blocks if isinstance(b, dict) and b.get('kind') in ('note', 'alert', 'tip', 'btn') and b.get('text')]

    edit_quiz = quiz
    quiz_questions = []
    if visual_edit:
        edit_quiz = Quiz.objects.filter(lesson=lesson).first()
        if edit_quiz:
            quiz_questions = list(edit_quiz.questions.prefetch_related('choices').order_by('order'))

    context = {
        'lesson': lesson,
        'content': content,
        'progress': progress,
        'quiz': quiz,
        'quiz_attempt': quiz_attempt,
        'vocabularies': vocab_list,
        'daccent': display.get('accent') or '',
        'daccent2': display.get('accent2') or '',
        'dstyles': dstyles,
        'image_width': image_width,
        'image_align': image_align,
        'custom_blocks': custom_blocks,
        'edit_quiz': edit_quiz,
        'quiz_questions': quiz_questions,
        'visual_edit': visual_edit,
        've_fab': True,
        'title': f'{lesson.name} - LearnQuest'
    }
    return render(request, 'language_academy/lesson_detail.html', context)


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)


    attempts_count = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
    if attempts_count >= quiz.max_attempts:

        from shop.services import consume_item_by_effect
        r = consume_item_by_effect(request.user, 'retry_ticket', source={'quiz': quiz.id})
        if r.get('ok'):
            messages.info(request, '🎫 Retry ticket used — you earned one extra attempt! Good luck 🍀')
        else:
            messages.error(request, f'You can take this quiz at most {quiz.max_attempts} times. (Tip: grab a "Retry Ticket" from the shop 🎫)')
            return redirect('language_academy:lesson_detail', lesson_id=quiz.lesson.id)

    session = QuizSession.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=False
    ).first()

    if not session:
        session = QuizSession.objects.create(
            user=request.user,
            quiz=quiz,
            session_key=str(uuid.uuid4()),
            answers={},
            is_completed=False,
            time_spent=0
        )

    total_seconds = quiz.time_limit_minutes * 60
    elapsed_seconds = session.time_spent
    remaining_seconds = max(0, total_seconds - elapsed_seconds)

    if remaining_seconds <= 0 and not session.is_completed:
        return redirect('language_academy:submit_quiz_auto', session_key=session.session_key)

    questions = quiz.get_questions()
    if quiz.shuffle_questions:
        questions = questions.order_by('?')

    context = {
        'quiz': quiz,
        'questions': questions,
        'attempts_count': attempts_count,
        'remaining_attempts': quiz.max_attempts - attempts_count,
        'session': session,
        'saved_answers': session.answers,
        'remaining_seconds': remaining_seconds,
        'title': f'{quiz.title} - Quiz'
    }
    return render(request, 'language_academy/quiz_take.html', context)


@login_required
@require_http_methods(['POST'])
def save_quiz_answer(request):
    data = json.loads(request.body)
    question_id = data.get('question_id')
    answer = data.get('answer', '').strip()
    session_key = data.get('session_key')

    session = get_object_or_404(QuizSession, session_key=session_key, user=request.user)

    question = get_object_or_404(Question, id=question_id)
    if question.question_type == 'fill_blank':
        answer = answer.strip().lower()

    answers = session.answers
    answers[str(question_id)] = answer
    session.answers = answers
    session.save()

    return JsonResponse({'status': 'success', 'saved': True})


@login_required
@require_http_methods(['POST'])
def save_quiz_time(request):
    data = json.loads(request.body)
    session_key = data.get('session_key')
    time_spent = data.get('time_spent', 0)

    session = get_object_or_404(QuizSession, session_key=session_key, user=request.user)
    session.time_spent = time_spent
    session.save()

    return JsonResponse({'status': 'success'})


@login_required
def submit_quiz_auto(request, session_key):
    session = get_object_or_404(QuizSession, session_key=session_key, user=request.user)

    if session.is_completed:
        return redirect('language_academy:quiz_result', attempt_id=session.attempt_id)

    quiz = session.quiz
    questions = quiz.get_questions()
    total_points = 0
    earned_points = 0
    user_answers = session.answers

    for question in questions:
        total_points += question.points
        user_answer = user_answers.get(str(question.id), '')

        if question.question_type == 'mcq':
            correct = question.choices.filter(is_correct=True).first()
            if correct and user_answer == str(correct.id):
                earned_points += question.points
        elif question.question_type == 'fill_blank':
            user_answer_norm = user_answer.strip().lower()
            correct_answer_norm = question.blank_answer.strip().lower()
            if user_answer_norm == correct_answer_norm:
                earned_points += question.points
        elif question.question_type == 'true_false':
            if user_answer.lower() == question.blank_answer.lower():
                earned_points += question.points

    final_score = int((earned_points / total_points) * 100) if total_points > 0 else 0
    passed = final_score >= quiz.passing_score

    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=final_score,
        passed=passed,
        answers=user_answers,
        completed_at=timezone.now(),
        time_spent_seconds=session.time_spent
    )

    session.is_completed = True
    session.attempt_id = attempt.id
    session.save()

    lesson_progress = UserLessonProgress.objects.filter(user=request.user, lesson=quiz.lesson).first()
    if lesson_progress:
        lesson_progress.quiz_score = final_score
        lesson_progress.quiz_passed = passed
        lesson_progress.save()

    if passed:
        _grant_pass_rewards_once(request.user, quiz, 'quiz')

    messages.warning(request, f'Quiz time is up! Your score: {final_score}%')
    return redirect('language_academy:quiz_result', attempt_id=attempt.id)


@login_required
@require_http_methods(['POST'])
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    session_key = request.POST.get('session_key')

    session = get_object_or_404(QuizSession, session_key=session_key, user=request.user, quiz=quiz)

    if session.is_completed:
        messages.error(request, 'This quiz has already been submitted!')
        return redirect('language_academy:quiz_result', attempt_id=session.attempt_id)

    questions = quiz.get_questions()
    total_points = 0
    earned_points = 0
    user_answers = session.answers

    for question in questions:
        total_points += question.points
        user_answer = user_answers.get(str(question.id), '')

        if question.question_type == 'mcq':
            correct = question.choices.filter(is_correct=True).first()
            if correct and user_answer == str(correct.id):
                earned_points += question.points
        elif question.question_type == 'fill_blank':
            user_answer_norm = user_answer.strip().lower()
            correct_answer_norm = question.blank_answer.strip().lower()
            if user_answer_norm == correct_answer_norm:
                earned_points += question.points
        elif question.question_type == 'true_false':
            if user_answer.lower() == question.blank_answer.lower():
                earned_points += question.points

    final_score = int((earned_points / total_points) * 100) if total_points > 0 else 0
    passed = final_score >= quiz.passing_score

    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=final_score,
        passed=passed,
        answers=user_answers,
        completed_at=timezone.now(),
        time_spent_seconds=session.time_spent
    )

    session.is_completed = True
    session.attempt_id = attempt.id
    session.save()

    lesson = quiz.lesson
    lesson_progress, _ = UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    lesson_progress.quiz_score = final_score
    lesson_progress.quiz_passed = passed

    if passed:
        lesson_progress.status = 'completed'
        lesson_progress.progress_percentage = 100
        lesson_progress.completed_at = timezone.now()

        if lesson_progress.xp_earned == 0:
            from economy.services import grant_xp as _grant_lesson_xp
            _grant_lesson_xp(request.user, lesson.xp_reward, source='lesson_completion',
                             source_id=lesson.id, rule_code='lesson_complete',
                             period_key=f'lesson:{lesson.id}')
            request.user.refresh_from_db(fields=['xp', 'level'])
            lesson_progress.xp_earned = lesson.xp_reward

        q_xp, q_coins, first_pass = _grant_pass_rewards_once(request.user, quiz, 'quiz')
        if not first_pass:
            messages.info(request, '🔁 You already passed this quiz — rewards are only for the first pass.')

        daily_goal, _ = DailyGoal.objects.get_or_create(
            user=request.user,
            goal_date=timezone.localdate(),
            defaults={'target_xp': 100, 'target_lessons': 2, 'target_vocabulary': 5}
        )
        daily_goal.current_lessons += 1
        daily_goal.current_xp += lesson.xp_reward + quiz.xp_reward
        daily_goal.save()

        chapter_progress, _ = UserChapterProgress.objects.get_or_create(
            user=request.user,
            chapter=lesson.chapter
        )
        chapter_progress.update_progress()

        messages.success(request, f'🎉 Congrats! Lesson "{lesson.name}" completed! +{lesson.xp_reward + quiz.xp_reward} XP')
    else:
        lesson_progress.save()
        messages.warning(request, f'{final_score}% — you need {quiz.passing_score}% to pass.')

    lesson_progress.save()

    return redirect('language_academy:quiz_result', attempt_id=attempt.id)


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    return render(request, 'language_academy/quiz_result.html', {'attempt': attempt, 'quiz': attempt.quiz})


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, is_published=True)


    attempt_count = ExamAttempt.objects.filter(user=request.user, exam=exam).count()
    if attempt_count >= exam.max_attempts:
        messages.error(request, 'You have reached the maximum number of allowed attempts.')
        return redirect('language_academy:dashboard')

    session = ExamSession.objects.filter(
        user=request.user,
        exam=exam,
        is_completed=False
    ).first()

    exam_questions = exam.exam_questions.all().order_by('order')

    total_seconds = exam.time_limit_minutes * 60
    elapsed_seconds = session.time_spent if session else 0
    remaining_seconds = max(0, total_seconds - elapsed_seconds)

    if request.method == 'POST':
        answers = {}
        correct_count = 0

        for eq in exam_questions:
            answer_key = f'question_{eq.id}'
            user_answer = request.POST.get(answer_key, '')

            is_correct = user_answer.strip().lower() == eq.correct_answer.strip().lower()
            if is_correct:
                correct_count += 1

            answers[str(eq.id)] = {
                'user_answer': user_answer,
                'is_correct': is_correct,
            }

        total_points = sum(eq.points for eq in exam_questions)
        earned_points = sum(
            eq.points for eq in exam_questions
            if str(eq.id) in answers and answers[str(eq.id)]['is_correct']
        )
        score = (earned_points / total_points * 100) if total_points > 0 else 0
        passed = score >= exam.passing_score

        attempt = ExamAttempt.objects.create(
            user=request.user,
            exam=exam,
            score=score,
            passed=passed,
            answers=answers,
            completed_at=timezone.now(),
            time_spent_seconds=session.time_spent if session else 0,
        )

        if session:
            session.is_completed = True
            session.attempt_id = attempt.id
            session.save()

        if passed:
            if exam.chapter:
                chapter_progress, _ = UserChapterProgress.objects.get_or_create(
                    user=request.user,
                    chapter=exam.chapter
                )
                chapter_progress.exam_passed = True
                chapter_progress.exam_score = score
                chapter_progress.xp_earned += exam.xp_reward
                chapter_progress.save()

                world_progress, _ = UserWorldProgress.objects.get_or_create(
                    user=request.user,
                    world=exam.chapter.world
                )
                completed_chapters = UserChapterProgress.objects.filter(
                    user=request.user,
                    chapter__world=exam.chapter.world,
                    exam_passed=True
                ).count()
                world_progress.chapters_completed = completed_chapters
                world_progress.save()

            elif exam.world:
                world_progress, _ = UserWorldProgress.objects.get_or_create(
                    user=request.user,
                    world=exam.world
                )
                world_progress.exam_passed = True
                world_progress.exam_score = score
                world_progress.xp_earned += exam.xp_reward
                world_progress.save()

        return redirect('language_academy:exam_result', attempt_id=attempt.id)

    if not session:
        session = ExamSession.objects.create(
            user=request.user,
            exam=exam,
            session_key=f"{request.user.id}_{exam.id}_{int(timezone.now().timestamp())}",
            answers={},
            time_spent=0,
            is_completed=False
        )

    context = {
        'exam': exam,
        'questions': exam_questions,
        'session': session,
        'attempt_number': attempt_count + 1,
        'max_attempts': exam.max_attempts,
        'time_limit': exam.time_limit_minutes,
        'remaining_seconds': remaining_seconds,
        'saved_answers': session.answers if session else {},
    }

    return render(request, 'language_academy/exam_take.html', context)


@login_required
def submit_exam_auto(request, session_key):
    session = get_object_or_404(ExamSession, session_key=session_key, user=request.user)

    if session.is_completed:
        return redirect('language_academy:exam_result', attempt_id=session.attempt_id)

    exam = session.exam
    questions = exam.get_questions()
    total_points = 0
    earned_points = 0
    user_answers = session.answers

    for question in questions:
        total_points += question.points
        user_answer = user_answers.get(str(question.id), '')

        if question.question_type == 'mcq':
            if user_answer == question.correct_answer:
                earned_points += question.points
        elif question.question_type == 'fill_blank':
            user_answer_norm = user_answer.strip().lower()
            correct_answer_norm = question.correct_answer.strip().lower()
            if user_answer_norm == correct_answer_norm:
                earned_points += question.points
        elif question.question_type == 'true_false':
            if user_answer.lower() == question.correct_answer.lower():
                earned_points += question.points

    final_score = int((earned_points / total_points) * 100) if total_points > 0 else 0
    passed = final_score >= exam.passing_score

    attempt = ExamAttempt.objects.create(
        user=request.user,
        exam=exam,
        score=final_score,
        passed=passed,
        answers=user_answers,
        completed_at=timezone.now(),
        time_spent_seconds=session.time_spent
    )

    session.is_completed = True
    session.attempt_id = attempt.id
    session.save()

    if passed:
        _grant_pass_rewards_once(request.user, exam, 'exam')

    if exam.chapter:
        chapter_progress = UserChapterProgress.objects.filter(user=request.user, chapter=exam.chapter).first()
        if chapter_progress:
            chapter_progress.exam_score = final_score
            chapter_progress.exam_passed = passed
            chapter_progress.save()
            chapter_progress.update_progress()

    messages.warning(request, f'Exam time is up! Your score: {final_score}%')
    return redirect('language_academy:exam_result', attempt_id=attempt.id)


@login_required
@require_http_methods(['POST'])
def save_exam_answer(request):
    data = json.loads(request.body)
    question_id = data.get('question_id')
    answer = data.get('answer', '').strip()
    session_key = data.get('session_key')

    session = get_object_or_404(ExamSession, session_key=session_key, user=request.user)

    question = get_object_or_404(ExamQuestion, id=question_id)
    if question.question_type == 'fill_blank':
        answer = answer.strip().lower()

    answers = session.answers
    answers[str(question_id)] = answer
    session.answers = answers
    session.save()

    return JsonResponse({'status': 'success', 'saved': True})


@login_required
@require_http_methods(['POST'])
def save_exam_time(request):
    data = json.loads(request.body)
    session_key = data.get('session_key')
    time_spent = data.get('time_spent', 0)

    session = get_object_or_404(ExamSession, session_key=session_key, user=request.user)
    session.time_spent = time_spent
    session.save()

    return JsonResponse({'status': 'success'})


@login_required
@require_http_methods(['POST'])
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    session_key = request.POST.get('session_key')

    session = get_object_or_404(ExamSession, session_key=session_key, user=request.user, exam=exam)

    if session.is_completed:
        messages.error(request, 'This exam has already been submitted!')
        return redirect('language_academy:exam_result', attempt_id=session.attempt_id)

    questions = exam.get_questions()
    total_points = 0
    earned_points = 0
    user_answers = session.answers

    for question in questions:
        total_points += question.points
        user_answer = user_answers.get(str(question.id), '')

        if question.question_type == 'mcq':
            if user_answer == question.correct_answer:
                earned_points += question.points
        elif question.question_type == 'fill_blank':
            user_answer_norm = user_answer.strip().lower()
            correct_answer_norm = question.correct_answer.strip().lower()
            if user_answer_norm == correct_answer_norm:
                earned_points += question.points
        elif question.question_type == 'true_false':
            if user_answer.lower() == question.correct_answer.lower():
                earned_points += question.points

    final_score = int((earned_points / total_points) * 100) if total_points > 0 else 0
    passed = final_score >= exam.passing_score

    attempt = ExamAttempt.objects.create(
        user=request.user,
        exam=exam,
        score=final_score,
        passed=passed,
        answers=user_answers,
        completed_at=timezone.now(),
        time_spent_seconds=session.time_spent
    )

    session.is_completed = True
    session.attempt_id = attempt.id
    session.save()

    if passed:
        _grant_pass_rewards_once(request.user, exam, 'exam')

    if exam.chapter:
        chapter_progress, _ = UserChapterProgress.objects.get_or_create(
            user=request.user,
            chapter=exam.chapter
        )
        chapter_progress.exam_score = final_score
        chapter_progress.exam_passed = passed

        if passed:
            lessons = Lesson.objects.filter(chapter=exam.chapter, is_published=True)
            for lesson in lessons:
                lesson_progress, _ = UserLessonProgress.objects.get_or_create(
                    user=request.user,
                    lesson=lesson
                )
                if lesson_progress.status != 'completed':
                    lesson_progress.status = 'completed'
                    lesson_progress.progress_percentage = 100
                    lesson_progress.completed_at = timezone.now()
                    if lesson_progress.xp_earned == 0:
                        lesson_progress.xp_earned = lesson.xp_reward
                    lesson_progress.save()

            chapter_progress.is_completed = True
            chapter_progress.completed_at = timezone.now()
            chapter_progress.save()
            messages.success(request, f'🎉 Chapter "{exam.chapter.name}" completed!')
        else:
            chapter_progress.save()
            messages.warning(request, f'{final_score}% — you need {exam.passing_score}% to pass.')

    return redirect('language_academy:exam_result', attempt_id=attempt.id)


@login_required
def exam_result(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    exam = attempt.exam

    answers_data = {}
    if isinstance(attempt.answers, str):
        try:
            answers_data = json.loads(attempt.answers)
        except json.JSONDecodeError:
            answers_data = {}
    elif isinstance(attempt.answers, dict):
        answers_data = attempt.answers
    else:
        answers_data = {}

    world = None
    chapter = None

    if exam.world:
        world = exam.world
    elif exam.chapter:
        chapter = exam.chapter
        if chapter:
            world = chapter.world

    exam_questions = exam.exam_questions.all().order_by('order')
    total_questions = exam_questions.count()

    correct_count = 0
    wrong_answers = []

    for eq in exam_questions:
        question_id = str(eq.id)
        user_answer = ''
        is_correct = False

        if question_id in answers_data:
            answer_data = answers_data[question_id]

            if isinstance(answer_data, dict):
                user_answer = answer_data.get('user_answer', '')
                is_correct = answer_data.get('is_correct', False)
            elif isinstance(answer_data, str):
                user_answer = answer_data
                is_correct = user_answer.strip().lower() == eq.correct_answer.strip().lower()
            else:
                user_answer = str(answer_data)
                is_correct = user_answer.strip().lower() == eq.correct_answer.strip().lower()

        if is_correct:
            correct_count += 1
        else:
            wrong_answers.append({
                'question': eq,
                'user_answer': user_answer if user_answer else 'No answer provided',
                'correct_answer': eq.correct_answer,
                'points': eq.points,
            })

    total_points = sum(eq.points for eq in exam_questions)
    earned_points = 0

    for eq in exam_questions:
        question_id = str(eq.id)
        if question_id in answers_data:
            answer_data = answers_data[question_id]
            is_correct = False

            if isinstance(answer_data, dict):
                is_correct = answer_data.get('is_correct', False)
            elif isinstance(answer_data, str):
                is_correct = answer_data.strip().lower() == eq.correct_answer.strip().lower()
            else:
                is_correct = str(answer_data).strip().lower() == eq.correct_answer.strip().lower()

            if is_correct:
                earned_points += eq.points

    score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0


    attempt_number = ExamAttempt.objects.filter(
        user=attempt.user, exam=exam, pk__lte=attempt.pk
    ).count()

    context = {
        'attempt': attempt,
        'exam': exam,
        'world': world,
        'chapter': chapter,
        'attempt_number': attempt_number,
        'max_attempts': exam.max_attempts,
        'total_questions': total_questions,
        'correct_answers': correct_count,
        'score_percentage': score_percentage,
        'passed': attempt.passed,
        'wrong_answers': wrong_answers,
        'total_xp_earned': exam.xp_reward if attempt.passed else 0,
        'total_coins_earned': exam.coin_reward if attempt.passed else 0,
        'exam_questions': exam_questions,
    }

    return render(request, 'language_academy/exam_result.html', context)


@login_required
def vocabulary_list(request):
    vocabularies = Vocabulary.objects.filter(is_active=True)

    category_id = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search = request.GET.get('search')

    if category_id:
        vocabularies = vocabularies.filter(categories__id=category_id)
    if difficulty:
        vocabularies = vocabularies.filter(difficulty=difficulty)
    if search:
        vocabularies = vocabularies.filter(Q(word__icontains=search) | Q(meaning__icontains=search))

    paginator = Paginator(vocabularies, 12)
    page_number = request.GET.get('page', 1)
    vocab_list = paginator.get_page(page_number)

    for vocab in vocab_list:
        progress = UserVocabularyProgress.objects.filter(user=request.user, vocabulary=vocab).first()
        vocab.user_mastery = progress.mastery_score if progress else 0
        vocab.user_level = progress.mastery_level if progress else 0
        vocab.next_review = progress.next_review_date if progress else None

    total_vocab_count = Vocabulary.objects.filter(is_active=True).count()
    learned_count = UserVocabularyProgress.objects.filter(
        user=request.user, mastery_level__gte=2
    ).count()
    mastered_count = UserVocabularyProgress.objects.filter(
        user=request.user, mastery_level__gte=3
    ).count()
    due_count = UserVocabularyProgress.objects.filter(
        user=request.user,
        next_review_date__lte=timezone.now()
    ).count()

    context = {
        'vocabularies': vocab_list,
        'categories': VocabularyCategory.objects.all(),
        'selected_category': category_id,
        'selected_difficulty': difficulty,
        'search_query': search,
        'total_vocab_count': total_vocab_count,
        'learned_count': learned_count,
        'mastered_count': mastered_count,
        'due_count': due_count,
        'title': 'Vocabulary List'
    }
    return render(request, 'language_academy/vocabulary_list.html', context)


@login_required
def vocabulary_review(request):
    due_words = UserVocabularyProgress.objects.filter(
        user=request.user,
        next_review_date__lte=timezone.now()
    ).select_related('vocabulary').order_by('forgetting_risk')[:20]

    if request.method == 'POST':
        word_id = request.POST.get('word_id')
        is_correct = request.POST.get('is_correct') == 'true'
        difficulty = request.POST.get('difficulty', 'medium')

        progress = get_object_or_404(
            UserVocabularyProgress,
            user=request.user,
            vocabulary_id=word_id
        )

        if is_correct:
            bonus = {'easy': 15, 'medium': 10, 'hard': 5}.get(difficulty, 10)
            progress.mastery_score = min(100, progress.mastery_score + bonus)
            progress.correct_count += 1
            progress.review_count += 1

            if progress.mastery_score >= 80 and progress.mastery_level < 4:
                progress.mastery_level = 4
            elif progress.mastery_score >= 60 and progress.mastery_level < 3:
                progress.mastery_level = 3
            elif progress.mastery_score >= 40 and progress.mastery_level < 2:
                progress.mastery_level = 2
            elif progress.mastery_score >= 20 and progress.mastery_level < 1:
                progress.mastery_level = 1

            xp_reward = {'easy': 15, 'medium': 10, 'hard': 5}.get(difficulty, 10)
            request.user.add_xp(xp_reward, 'vocabulary_review', f'Reviewed: {progress.vocabulary.word}')

        else:
            progress.mastery_score = max(0, progress.mastery_score - 10)
            progress.incorrect_count += 1
            progress.review_count += 1

            if progress.mastery_score < 20:
                progress.mastery_level = 0
            elif progress.mastery_score < 40 and progress.mastery_level > 1:
                progress.mastery_level = 1

        progress.last_reviewed = timezone.now()

        if is_correct:
            intervals = [1, 3, 7, 14, 30, 60, 90]
            current_level = min(progress.mastery_level, len(intervals) - 1)
            days = intervals[current_level]
            progress.next_review_date = timezone.now() + timezone.timedelta(days=days)
        else:
            progress.next_review_date = timezone.now() + timezone.timedelta(hours=6)

        progress.save()

        return JsonResponse({
            'success': True,
            'mastery_score': progress.mastery_score,
            'mastery_level': progress.mastery_level,
            'next_review': progress.next_review_date.strftime('%Y-%m-%d %H:%M')
        })

    context = {
        'due_words': due_words,
        'total_words': UserVocabularyProgress.objects.filter(user=request.user).count(),
        'mastered_words': UserVocabularyProgress.objects.filter(
            user=request.user, mastery_level__gte=3
        ).count(),
        'streak_days': request.user.streak,
        'title': 'Vocabulary Review'
    }
    return render(request, 'language_academy/vocabulary_review.html', context)


@login_required
@require_http_methods(['POST'])
def vocabulary_mark_learned(request, word_id):
    word = get_object_or_404(Vocabulary, id=word_id)

    progress, created = UserVocabularyProgress.objects.get_or_create(
        user=request.user,
        vocabulary=word,
        defaults={
            'mastery_level': 4,
            'mastery_score': 100,
            'next_review_date': timezone.now() + timezone.timedelta(days=30),
            'correct_count': 1,
            'review_count': 1,
            'last_reviewed': timezone.now()
        }
    )

    if not created:
        progress.mastery_level = 4
        progress.mastery_score = 100
        progress.next_review_date = timezone.now() + timezone.timedelta(days=30)
        progress.correct_count += 1
        progress.review_count += 1
        progress.last_reviewed = timezone.now()
        progress.save()

    request.user.add_xp(10, 'vocabulary_mark_learned', f'Marked learned: {word.word}')

    return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def vocabulary_add_to_practice(request, word_id):
    word = get_object_or_404(Vocabulary, id=word_id)

    progress, created = UserVocabularyProgress.objects.get_or_create(
        user=request.user,
        vocabulary=word,
        defaults={
            'mastery_level': 0,
            'mastery_score': 0,
            'next_review_date': timezone.now() + timezone.timedelta(days=1)
        }
    )

    if created or progress.mastery_level == 0:
        progress.mastery_level = 1
        progress.mastery_score = 10
        progress.next_review_date = timezone.now() + timezone.timedelta(days=1)
        progress.save()

    return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def vocabulary_add_to_review(request, word_id):
    word = get_object_or_404(Vocabulary, id=word_id)

    progress, created = UserVocabularyProgress.objects.get_or_create(
        user=request.user,
        vocabulary=word,
        defaults={
            'mastery_level': 1,
            'mastery_score': 20,
            'next_review_date': timezone.now() + timezone.timedelta(hours=6)
        }
    )

    if not created:
        progress.next_review_date = timezone.now() + timezone.timedelta(hours=6)
        progress.save()

    return JsonResponse({'success': True})


@login_required
def learner_dashboard(request):
    total_lessons = UserLessonProgress.objects.filter(user=request.user, status='completed').count()
    total_quizzes = QuizAttempt.objects.filter(user=request.user, passed=True).count()
    total_exams = ExamAttempt.objects.filter(user=request.user, passed=True).count()
    worlds_completed = UserWorldProgress.objects.filter(user=request.user, is_completed=True).count()

    worlds_progress = []
    for world in World.objects.filter(is_published=True).order_by('order'):
        progress = UserWorldProgress.objects.filter(user=request.user, world=world).first()
        worlds_progress.append({
            'id': world.id,
            'name': world.name,
            'order': world.order,
            'is_completed': progress.is_completed if progress else False,
            'completion_percentage': world.get_completion_percentage(request.user)
        })

    recent_lessons = UserLessonProgress.objects.filter(user=request.user).select_related('lesson').order_by(
        '-last_activity')[:10]
    badges = UserBadge.objects.filter(user=request.user).select_related('badge').order_by('-earned_at')[:8]
    certificates = Certificate.objects.filter(user=request.user).order_by('-issued_at')[:5]

    today_goal, _ = DailyGoal.objects.get_or_create(
        user=request.user, goal_date=timezone.localdate(),
        defaults={'target_xp': 100, 'target_lessons': 2, 'target_vocabulary': 5}
    )

    context = {
        'total_lessons_completed': total_lessons,
        'total_quizzes_passed': total_quizzes,
        'total_exams_passed': total_exams,
        'worlds_completed': worlds_completed,
        'total_worlds': World.objects.filter(is_published=True).count(),
        'worlds_progress': worlds_progress,
        'recent_lessons': recent_lessons,
        'badges': badges,
        'certificates': certificates,
        'daily_goal': today_goal,
        'level_progress': request.user.get_level_progress(),
        'streak': request.user.streak,
        'title': 'My Dashboard'
    }
    return render(request, 'language_academy/dashboard.html', context)


@login_required
def my_certificates(request):
    certificates = Certificate.objects.filter(user=request.user).select_related('world').order_by('-issued_at')
    return render(request, 'language_academy/certificates.html',
                  {'certificates': certificates, 'title': 'My Certificates'})


@login_required
def certificate_detail(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user)
    return render(request, 'language_academy/certificate_detail.html', {'certificate': certificate})


def certificate_verify(request, code=None):
    certificate = None
    searched = False
    if code:
        code = code.strip().upper()
    elif request.method == 'POST' or request.GET.get('code'):
        code = (request.POST.get('code') or request.GET.get('code') or '').strip().upper()
    if code:
        searched = True
        certificate = (Certificate.objects
                       .filter(verification_code__iexact=code)
                       .select_related('user', 'world')
                       .first())
    return render(request, 'language_academy/certificate_verify.html', {
        'certificate': certificate, 'searched': searched, 'code': code or '',
        'title': 'Verify Certificate',
    })


@login_required
def start_dialogue(request, dialogue_id):
    dialogue = get_object_or_404(Dialogue, id=dialogue_id, is_active=True)
    first_scene = dialogue.scenes.filter(order=1).first()

    if request.method == 'POST':
        choice = get_object_or_404(DialogueChoice, id=request.POST.get('choice_id'))
        if choice.is_correct and choice.xp_reward > 0:
            request.user.add_xp(choice.xp_reward, 'dialogue', f'Correct choice in {dialogue.title}')

        if choice.next_scene:
            return render(request, 'language_academy/dialogue_scene.html', {
                'dialogue': dialogue, 'scene': choice.next_scene
            })
        else:
            messages.success(request, 'Dialogue finished successfully!')
            return redirect('language_academy:lesson_detail', lesson_id=dialogue.lesson.id)

    return render(request, 'language_academy/dialogue_scene.html', {'dialogue': dialogue, 'scene': first_scene})


@login_required
def writing_practice(request, lesson_id=None):
    lesson = get_object_or_404(Lesson, id=lesson_id) if lesson_id else None

    if request.method == 'POST':
        return render(request, 'language_academy/writing_result.html', {
            'prompt': request.POST.get('prompt'),
            'submission': request.POST.get('submission'),
            'lesson': lesson
        })

    prompts = ["Describe your daily routine.", "Write about your last vacation.", "What are your future plans?"]
    return render(request, 'language_academy/writing_practice.html', {'lesson': lesson, 'prompts': prompts})


@login_required
@require_http_methods(['POST'])
def evaluate_writing(request):
    from .services.ai_service import AIService


    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON payload'}, status=400)
        prompt = data.get('prompt', '')
        submission_text = data.get('submission', data.get('text', ''))
    else:
        prompt = request.POST.get('prompt', '') or request.POST.get('custom_prompt', '')
        submission_text = request.POST.get('submission', request.POST.get('text', ''))

    if not prompt or not submission_text:
        return JsonResponse(
            {'success': False, 'error': 'The prompt and submission fields are required'},
            status=400
        )

    submission = WritingSubmission.objects.create(
        user=request.user,
        prompt=prompt,
        submission=submission_text
    )
    evaluation = AIService.evaluate_writing(submission.prompt, submission.submission)

    submission.ai_feedback = evaluation
    submission.overall_score = evaluation.get('overall_score')
    submission.evaluated_at = timezone.now()
    submission.save()

    return JsonResponse(evaluation)


def _maybe_issue_certificate(user, world):
    if not world or not world.is_published:
        return None
    lessons = Lesson.objects.filter(chapter__world=world, chapter__is_published=True, is_published=True)
    total = lessons.count()
    if total == 0:
        return None
    done = UserLessonProgress.objects.filter(user=user, lesson__in=lessons, status='completed').count()
    if done < total:
        return None
    with transaction.atomic():
        wp, _ = UserWorldProgress.objects.select_for_update().get_or_create(user=user, world=world)
        if wp.certificate_issued:
            return None
        cert, _created = Certificate.objects.get_or_create(user=user, world=world)
        wp.certificate_issued = True
        wp.save(update_fields=['certificate_issued'])
    return cert


@login_required
@require_http_methods(['POST'])
def update_lesson_progress(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress_percentage = int(request.POST.get('progress', 0))

    progress, _ = UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)


    has_quiz = Quiz.objects.filter(lesson=lesson, is_published=True).exists()
    if progress_percentage >= 100 and has_quiz and not progress.quiz_passed:
        progress_percentage = 99

    progress.progress_percentage = progress_percentage
    progress.last_activity = timezone.now()

    if progress_percentage >= 100 and progress.status != 'completed':
        progress.status = 'completed'
        progress.completed_at = timezone.now()
        request.user.add_xp(lesson.xp_reward, 'lesson_completion', f'Completed: {lesson.name}')
        request.user.update_streak()

        daily_goal, _ = DailyGoal.objects.get_or_create(user=request.user, goal_date=timezone.localdate())
        daily_goal.current_lessons += 1
        daily_goal.current_xp += lesson.xp_reward
        daily_goal.save()

    progress.save()

    chapter_progress, _ = UserChapterProgress.objects.get_or_create(user=request.user, chapter=lesson.chapter)
    chapter_progress.update_progress()

    resp = {'success': True, 'status': progress.status}
    cert = _maybe_issue_certificate(request.user, lesson.chapter.world)
    if cert:
        resp['certificate_url'] = reverse('language_academy:certificate_detail', args=[cert.id])
    return JsonResponse(resp)


@login_required
def vocabulary_learning_hub(request):
    total_words = Vocabulary.objects.filter(is_active=True).count()
    learned_words = UserVocabularyProgress.objects.filter(
        user=request.user, mastery_level__gte=2
    ).count()
    mastered_words = UserVocabularyProgress.objects.filter(
        user=request.user, mastery_level__gte=3
    ).count()

    due_reviews = UserVocabularyProgress.objects.filter(
        user=request.user,
        next_review_date__lte=timezone.now()
    ).count()

    recent_words = UserVocabularyProgress.objects.filter(
        user=request.user
    ).select_related('vocabulary').order_by('-updated_at')[:10]

    learning_words = UserVocabularyProgress.objects.filter(
        user=request.user,
        mastery_level__in=[1, 2]
    ).select_related('vocabulary').order_by('?')[:6]

    current_level = request.user.get_level()
    recommended_levels = ['A1', 'A2', 'B1']
    level_index = min(current_level // 5, len(recommended_levels) - 1)
    recommended_level = recommended_levels[level_index]

    new_words = Vocabulary.objects.filter(
        is_active=True,
        difficulty=recommended_level
    ).exclude(
        id__in=UserVocabularyProgress.objects.filter(
            user=request.user
        ).values_list('vocabulary_id', flat=True)
    ).order_by('?')[:10]

    daily_progress = DailyGoal.objects.filter(
        user=request.user,
        goal_date=timezone.localdate()
    ).first()

    context = {
        'total_words': total_words,
        'learned_words': learned_words,
        'mastered_words': mastered_words,
        'due_reviews': due_reviews,
        'recent_words': recent_words,
        'learning_words': learning_words,
        'new_words': new_words,
        'daily_progress': daily_progress,
        'recommended_level': recommended_level,
        'streak': request.user.streak,
        'title': 'Vocabulary Learning Hub'
    }
    return render(request, 'language_academy/vocabulary_hub.html', context)


@login_required
def vocabulary_flashcards(request):
    mode = request.GET.get('mode', 'new')

    if mode == 'new':
        learned_ids = UserVocabularyProgress.objects.filter(
            user=request.user
        ).values_list('vocabulary_id', flat=True)
        words = Vocabulary.objects.filter(
            is_active=True
        ).exclude(id__in=learned_ids).order_by('?')
    elif mode == 'review':
        due_progress = UserVocabularyProgress.objects.filter(
            user=request.user,
            next_review_date__lte=timezone.now()
        ).select_related('vocabulary')
        words = Vocabulary.objects.filter(
            id__in=due_progress.values_list('vocabulary_id', flat=True)
        )
    elif mode == 'mastered':
        mastered_progress = UserVocabularyProgress.objects.filter(
            user=request.user,
            mastery_level__gte=3
        ).select_related('vocabulary')
        words = Vocabulary.objects.filter(
            id__in=mastered_progress.values_list('vocabulary_id', flat=True)
        )
    else:
        words = Vocabulary.objects.filter(is_active=True)

    words = words[:30]

    word_data = []
    for word in words:
        progress = UserVocabularyProgress.objects.filter(
            user=request.user, vocabulary=word
        ).first()
        word_data.append({
            'word': word,
            'progress': progress,
            'mastery_level': progress.mastery_level if progress else 0,
            'mastery_score': progress.mastery_score if progress else 0,
        })

    context = {
        'words': word_data,
        'mode': mode,
        'total': len(word_data),
        'title': 'Flashcards'
    }
    return render(request, 'language_academy/vocabulary_flashcards.html', context)


@login_required
@require_http_methods(['POST'])
def vocabulary_flashcard_action(request):
    data = json.loads(request.body)
    word_id = data.get('word_id')
    action = data.get('action')

    word = get_object_or_404(Vocabulary, id=word_id)

    progress, created = UserVocabularyProgress.objects.get_or_create(
        user=request.user,
        vocabulary=word,
        defaults={
            'mastery_level': 0,
            'mastery_score': 0,
            'next_review_date': timezone.now() + timezone.timedelta(days=1)
        }
    )

    if action == 'know':
        progress.mastery_score = min(100, progress.mastery_score + 15)
        progress.correct_count += 1
        progress.review_count += 1

        if progress.mastery_score >= 80 and progress.mastery_level < 4:
            progress.mastery_level = 4
        elif progress.mastery_score >= 60 and progress.mastery_level < 3:
            progress.mastery_level = 3
        elif progress.mastery_score >= 40 and progress.mastery_level < 2:
            progress.mastery_level = 2
        elif progress.mastery_score >= 20 and progress.mastery_level < 1:
            progress.mastery_level = 1

        request.user.add_xp(10, 'vocabulary_learn', f'Learned: {word.word}')

    elif action == 'dont_know':
        progress.mastery_score = max(0, progress.mastery_score - 10)
        progress.incorrect_count += 1
        progress.review_count += 1

        if progress.mastery_score < 20:
            progress.mastery_level = 0
        elif progress.mastery_score < 40 and progress.mastery_level > 1:
            progress.mastery_level = 1

    elif action == 'hard':
        progress.mastery_score = max(0, progress.mastery_score - 5)
        progress.incorrect_count += 1
        progress.review_count += 1

    elif action == 'easy':
        progress.mastery_score = min(100, progress.mastery_score + 20)
        progress.correct_count += 1
        progress.review_count += 1

        if progress.mastery_score >= 70 and progress.mastery_level < 3:
            progress.mastery_level = 3
        elif progress.mastery_score >= 50 and progress.mastery_level < 2:
            progress.mastery_level = 2
        request.user.add_xp(15, 'vocabulary_master', f'Mastered: {word.word}')

    if action in ['know', 'easy']:
        interval_days = {0: 1, 1: 3, 2: 7, 3: 14, 4: 30}.get(progress.mastery_level, 1)
        progress.next_review_date = timezone.now() + timezone.timedelta(days=interval_days)
    else:
        progress.next_review_date = timezone.now() + timezone.timedelta(hours=12)

    progress.last_reviewed = timezone.now()
    progress.save()

    daily_goal, _ = DailyGoal.objects.get_or_create(
        user=request.user,
        goal_date=timezone.localdate(),
        defaults={'target_xp': 100, 'target_lessons': 2, 'target_vocabulary': 5}
    )
    daily_goal.current_vocabulary += 1
    daily_goal.current_xp += 5
    daily_goal.save()

    return JsonResponse({
        'success': True,
        'mastery_score': progress.mastery_score,
        'mastery_level': progress.mastery_level,
        'next_review': progress.next_review_date.strftime('%Y-%m-%d %H:%M'),
        'xp_earned': 10 if action in ['know', 'easy'] else 0
    })


@login_required
def vocabulary_matching_game(request):
    level = request.GET.get('level', request.user.get_level())
    difficulty_map = {1: 'A1', 2: 'A1', 3: 'A2', 4: 'A2', 5: 'B1', 6: 'B1'}
    diff = difficulty_map.get(level, 'A1')

    words = Vocabulary.objects.filter(
        is_active=True,
        difficulty=diff
    ).order_by('?')[:8]

    if words.count() < 8:
        words = Vocabulary.objects.filter(is_active=True).order_by('?')[:8]

    game_data = []
    for word in words:
        game_data.append({
            'id': word.id,
            'word': word.word,
            'meaning': word.meaning,
            'meaning_fa': word.meaning_fa,
            'difficulty': word.difficulty,
        })

    context = {
        'words': game_data,
        'level': diff,
        'total_words': len(game_data),
        'title': 'Matching Game'
    }
    return render(request, 'language_academy/vocabulary_matching.html', context)


@login_required
@require_http_methods(['POST'])
def vocabulary_matching_result(request):
    data = json.loads(request.body)
    word_id = data.get('word_id')
    is_correct = data.get('is_correct', False)

    word = get_object_or_404(Vocabulary, id=word_id)

    progress, _ = UserVocabularyProgress.objects.get_or_create(
        user=request.user,
        vocabulary=word,
        defaults={
            'mastery_level': 0,
            'mastery_score': 0,
            'next_review_date': timezone.now() + timezone.timedelta(days=1)
        }
    )

    if is_correct:
        progress.mastery_score = min(100, progress.mastery_score + 10)
        progress.correct_count += 1
        request.user.add_xp(5, 'matching_game', f'Matched: {word.word}')
    else:
        progress.mastery_score = max(0, progress.mastery_score - 5)
        progress.incorrect_count += 1

    progress.review_count += 1
    progress.last_reviewed = timezone.now()

    if progress.mastery_score >= 80:
        progress.mastery_level = 4
    elif progress.mastery_score >= 60:
        progress.mastery_level = 3
    elif progress.mastery_score >= 40:
        progress.mastery_level = 2
    elif progress.mastery_score >= 20:
        progress.mastery_level = 1

    progress.save()

    return JsonResponse({
        'success': True,
        'mastery_score': progress.mastery_score,
        'mastery_level': progress.mastery_level,
        'xp_earned': 5 if is_correct else 0
    })


@login_required
def vocabulary_sentence_builder(request):
    words_with_examples = Vocabulary.objects.filter(
        is_active=True,
        examples__isnull=False
    ).distinct().order_by('?')[:10]

    context = {
        'words': words_with_examples,
        'title': 'Sentence Builder'
    }
    return render(request, 'language_academy/vocabulary_sentence_builder.html', context)


@login_required
def vocabulary_spaced_repetition(request):
    due_words = UserVocabularyProgress.objects.filter(
        user=request.user,
        next_review_date__lte=timezone.now()
    ).select_related('vocabulary').order_by('forgetting_risk')[:15]

    new_words = Vocabulary.objects.filter(
        is_active=True
    ).exclude(
        id__in=UserVocabularyProgress.objects.filter(
            user=request.user
        ).values_list('vocabulary_id', flat=True)
    ).order_by('?')[:5]

    context = {
        'due_words': due_words,
        'new_words': new_words,
        'total_due': UserVocabularyProgress.objects.filter(
            user=request.user,
            next_review_date__lte=timezone.now()
        ).count(),
        'title': 'Spaced Repetition'
    }
    return render(request, 'language_academy/vocabulary_spaced_repetition.html', context)


@login_required
@require_http_methods(['POST'])
def vocabulary_spaced_repetition_action(request):
    data = json.loads(request.body)
    word_id = data.get('word_id')
    is_correct = data.get('is_correct', False)
    difficulty = data.get('difficulty', 'medium')

    word = get_object_or_404(Vocabulary, id=word_id)
    progress, _ = UserVocabularyProgress.objects.get_or_create(
        user=request.user,
        vocabulary=word,
        defaults={
            'mastery_level': 0,
            'mastery_score': 0,
            'next_review_date': timezone.now() + timezone.timedelta(days=1)
        }
    )

    difficulty_factor = {'easy': 1.5, 'medium': 1.0, 'hard': 0.5}.get(difficulty, 1.0)

    if is_correct:
        bonus = int(15 * difficulty_factor)
        progress.mastery_score = min(100, progress.mastery_score + bonus)
        progress.correct_count += 1

        xp_reward = int(10 * difficulty_factor)
        request.user.add_xp(xp_reward, 'spaced_repetition', f'Reviewed: {word.word}')
    else:
        penalty = int(10 * (1 / difficulty_factor))
        progress.mastery_score = max(0, progress.mastery_score - penalty)
        progress.incorrect_count += 1

    progress.review_count += 1
    progress.last_reviewed = timezone.now()

    if progress.mastery_score >= 80:
        progress.mastery_level = 4
    elif progress.mastery_score >= 60:
        progress.mastery_level = 3
    elif progress.mastery_score >= 40:
        progress.mastery_level = 2
    elif progress.mastery_score >= 20:
        progress.mastery_level = 1
    else:
        progress.mastery_level = 0

    if is_correct:
        intervals = [1, 3, 7, 14, 30, 60, 90]
        current_level = min(progress.mastery_level, len(intervals) - 1)
        days = int(intervals[current_level] * difficulty_factor)
        progress.next_review_date = timezone.now() + timezone.timedelta(days=days)
    else:
        progress.next_review_date = timezone.now() + timezone.timedelta(hours=6)

    progress.save()

    return JsonResponse({
        'success': True,
        'mastery_score': progress.mastery_score,
        'mastery_level': progress.mastery_level,
        'next_review': progress.next_review_date.strftime('%Y-%m-%d %H:%M'),
        'xp_earned': xp_reward if is_correct else 0
    })


@login_required
def vocabulary_stats(request):
    total_words = Vocabulary.objects.filter(is_active=True).count()
    user_progress = UserVocabularyProgress.objects.filter(user=request.user)

    learned = user_progress.filter(mastery_level__gte=2).count()
    mastered = user_progress.filter(mastery_level__gte=3).count()

    level_distribution = {
        'not_started': total_words - user_progress.count(),
        'level_0': user_progress.filter(mastery_level=0).count(),
        'level_1': user_progress.filter(mastery_level=1).count(),
        'level_2': user_progress.filter(mastery_level=2).count(),
        'level_3': user_progress.filter(mastery_level=3).count(),
        'level_4': user_progress.filter(mastery_level=4).count(),
    }

    from django.db.models import Count, Avg
    from django.db.models.functions import TruncDate

    weekly_stats = UserVocabularyProgress.objects.filter(
        user=request.user,
        last_reviewed__gte=timezone.now() - timezone.timedelta(days=7)
    ).annotate(
        day=TruncDate('last_reviewed')
    ).values('day').annotate(
        count=Count('id'),
        avg_score=Avg('mastery_score')
    ).order_by('day')

    best_words = user_progress.filter(mastery_score__gt=0).order_by('-mastery_score')[:10]
    worst_words = user_progress.filter(mastery_score__lt=50).order_by('mastery_score')[:10]

    context = {
        'total_words': total_words,
        'learned': learned,
        'mastered': mastered,
        'progress_percentage': int((learned / total_words) * 100) if total_words > 0 else 0,
        'level_distribution': level_distribution,
        'weekly_stats': weekly_stats,
        'best_words': best_words,
        'worst_words': worst_words,
        'user_progress': user_progress,
        'title': 'Vocabulary Statistics'
    }
    return render(request, 'language_academy/vocabulary_stats.html', context)


# ═══════════ Idioms Learning + AI Tutor (Questie) ═══════════
from . import ai_tutor as _tutor
from .models import (AIChallenge, AIChatMessage, CEFR_ORDER, Idiom,
                     PlacementAttempt, UserIdiomProgress, UserLanguageEstimate)

PLACE_PASS = 6


def _user_cefr(user):
    est = UserLanguageEstimate.objects.filter(user=user).first()
    return est.cefr_level if est else None


@login_required
def idioms_hub(request):
    if not _user_cefr(request.user):
        return redirect('language_academy:idioms_placement')
    level = _user_cefr(request.user)
    idioms = Idiom.objects.filter(is_active=True, level=level)
    total = idioms.count()
    learned = UserIdiomProgress.objects.filter(user=request.user, mastery_level__gte=2, idiom__level=level).count()
    due = UserIdiomProgress.objects.filter(user=request.user, mastery_level__gte=1,
                                           next_review_date__lte=timezone.now()).count()
    topics = (idioms.values_list('topic', flat=True).distinct())
    topic_cards = []
    for t in sorted(topics):
        qs = idioms.filter(topic=t)
        ids = qs.count()
        done = UserIdiomProgress.objects.filter(user=request.user, mastery_level__gte=2,
                                                idiom__in=qs).count()
        pct = round(done * 100 / ids) if ids else 0
        topic_cards.append({'slug': t, 'total': ids, 'done': done, 'pct': pct,
                            'icon': _TOPIC_ICONS.get(t, '💬')})
    other_levels = []
    for lv in CEFR_ORDER:
        c = Idiom.objects.filter(is_active=True, level=lv).count()
        other_levels.append({'code': lv, 'count': c, 'current': lv == level})
    return render(request, 'language_academy/idioms_hub.html', {
        'level': level, 'total': total, 'learned': learned, 'due': due,
        'topic_cards': topic_cards, 'other_levels': other_levels,
        'ai_available': _tutor.available(),
    })


_TOPIC_ICONS = {'daily': '🏠', 'luck': '🍀', 'health': '🩺', 'travel': '✈️', 'work': '💼',
                'weather': '🌦️', 'money': '💰', 'social': '🗣️', 'time': '⏰', 'study': '📚',
                'emotions': '💜'}


@login_required
def idioms_placement(request):
    if request.method == 'POST':
        force = request.POST.get('force_level', '').upper()
        if force in CEFR_ORDER:
            UserLanguageEstimate.objects.update_or_create(
                user=request.user, defaults={'cefr_level': force, 'source': 'self'})
            messages.success(request, f'Level set to {force} — have fun learning! 💬')
            return redirect('language_academy:idioms_hub')
        chosen = request.POST.get('level', '').upper()
        if chosen not in CEFR_ORDER:
            messages.error(request, 'Pick a level first.')
            return redirect('language_academy:idioms_placement')
        pending = PlacementAttempt.objects.filter(user=request.user, verdict='pending').order_by('-created_at').first()
        if pending:
            pending.delete()
        quiz, used_ai = _tutor.build_placement_quiz(chosen)
        attempt = PlacementAttempt.objects.create(user=request.user, chosen_level=chosen,
                                                  quiz=quiz, used_ai=used_ai)
        return redirect('language_academy:idioms_placement_quiz', attempt_id=attempt.id)
    est = UserLanguageEstimate.objects.filter(user=request.user).first()
    return render(request, 'language_academy/idioms_placement.html', {
        'levels': CEFR_ORDER, 'current': est.cefr_level if est else None,
    })


@login_required
def idioms_placement_quiz(request, attempt_id):
    attempt = get_object_or_404(PlacementAttempt, id=attempt_id, user=request.user, verdict='pending')
    return render(request, 'language_academy/idioms_placement_quiz.html', {'attempt': attempt,
                                                                           'questions': attempt.quiz})


@login_required
@require_http_methods(['POST'])
def idioms_placement_submit(request, attempt_id):
    attempt = get_object_or_404(PlacementAttempt, id=attempt_id, user=request.user, verdict='pending')
    answers = request.POST.getlist('ans[]')
    quiz = attempt.quiz
    if len(answers) != len(quiz):
        messages.error(request, 'Answer every question first.')
        return redirect('language_academy:idioms_placement_quiz', attempt_id=attempt.id)
    try:
        answers = [int(a) for a in answers]
    except ValueError:
        return redirect('language_academy:idioms_placement_quiz', attempt_id=attempt.id)
    score = sum(1 for i, q in enumerate(quiz)
                if answers[i] == q.get('answer') and 0 <= answers[i] <= 3)
    chosen = attempt.chosen_level
    idx = _tutor._cefr_index(chosen)
    with transaction.atomic():
        attempt = PlacementAttempt.objects.select_for_update().get(id=attempt.id)
        if attempt.verdict != 'pending':
            return redirect('language_academy:idioms_hub')
        attempt.answers = answers
        attempt.score = score
        attempt.finished_at = timezone.now()
        if score >= PLACE_PASS:
            attempt.verdict = 'confirmed'
            attempt.recommended_level = chosen
            UserLanguageEstimate.objects.update_or_create(
                user=request.user,
                defaults={'cefr_level': chosen, 'source': 'placement'})
        elif score >= len(quiz) // 2:
            lower = CEFR_ORDER[max(0, idx - 1)]
            attempt.verdict = 'adjust'
            attempt.recommended_level = lower
        else:
            lower = CEFR_ORDER[max(0, idx - 2 if idx >= 2 else 0)]
            attempt.verdict = 'adjust'
            attempt.recommended_level = lower
        attempt.save()
    return redirect('language_academy:idioms_placement_result', attempt_id=attempt.id)


@login_required
def idioms_placement_result(request, attempt_id):
    attempt = get_object_or_404(PlacementAttempt, id=attempt_id, user=request.user)
    return render(request, 'language_academy/idioms_placement_result.html', {'attempt': attempt})


@login_required
def idiom_learn(request):
    if not _user_cefr(request.user):
        return redirect('language_academy:idioms_placement')
    level = _user_cefr(request.user)
    topic = request.GET.get('topic', '')
    qs = Idiom.objects.filter(is_active=True, level=level)
    if topic:
        qs = qs.filter(topic=topic)
    items = []
    prog = {p.idiom_id: p for p in UserIdiomProgress.objects.filter(user=request.user, idiom__in=qs)}
    for i in qs:
        p = prog.get(i.id)
        items.append({'obj': i, 'mastery': p.mastery_level if p else 0})
    raw_topics = sorted(set(Idiom.objects.filter(is_active=True, level=level)
                            .values_list('topic', flat=True)))
    topics = [{'slug': t, 'icon': _TOPIC_ICONS.get(t, '💬')} for t in raw_topics]
    return render(request, 'language_academy/idiom_learn.html', {
        'items': items, 'level': level, 'topic': topic, 'topics': topics,
    })


@login_required
@require_http_methods(['POST'])
def idiom_mark_learned(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        idiom_id = int(data.get('idiom_id'))
        action = str(data.get('action') or 'reviewed')
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'bad_payload'}, status=400)
    idiom = get_object_or_404(Idiom, id=idiom_id, is_active=True)
    xp = 0
    with transaction.atomic():
        prog, created = UserIdiomProgress.objects.select_for_update().get_or_create(
            user=request.user, idiom=idiom)
        if action == 'known':
            first = prog.mastery_level < 2
            prog.mastery_level = min(4, prog.mastery_level + 2)
            prog.mastery_score = min(100.0, prog.mastery_score + 25)
            prog.correct_count += 1
            if first:
                from economy.services import grant_coins, grant_xp
                r = grant_xp(request.user, 8, source='idiom_learn', source_id=idiom.id,
                             idempotency_key=f'idiomlearn:{request.user.id}:{idiom.id}')
                xp = r.get('granted', 0)
                if xp:
                    grant_coins(request.user, 2, source='idiom_learn', source_id=idiom.id,
                                idempotency_key=f'idiomlearn:{request.user.id}:{idiom.id}:c')
        else:
            prog.mastery_level = min(4, prog.mastery_level + 1)
            prog.mastery_score = min(100.0, prog.mastery_score + 10)
            prog.incorrect_count += 1
            created = False
        prog.review_count += 1
        prog.last_reviewed = timezone.now()
        days = [0, 0, 1, 2, 4, 7][min(5, prog.mastery_level + 1)]
        prog.next_review_date = timezone.now() + timezone.timedelta(days=days)
        prog.save()
    return JsonResponse({'ok': True, 'mastery': prog.mastery_level, 'xp': xp})


@login_required
def idiom_flashcards(request):
    if not _user_cefr(request.user):
        return redirect('language_academy:idioms_placement')
    level = _user_cefr(request.user)
    topic = request.GET.get('topic', '')
    qs = Idiom.objects.filter(is_active=True, level=level)
    if topic:
        qs = qs.filter(topic=topic)
    deck = [{'id': i.id, 'ex': i.expression, 'fa': i.translation_fa,
             'def': i.definition_en, 'sen': i.example_en} for i in qs]
    return render(request, 'language_academy/idiom_flashcards.html', {'deck': deck, 'level': level})


@login_required
def idiom_review(request):
    if not _user_cefr(request.user):
        return redirect('language_academy:idioms_placement')
    now = timezone.now()
    due = (UserIdiomProgress.objects.filter(user=request.user, mastery_level__gte=1)
           .filter(Q(next_review_date__lte=now) | Q(next_review_date__isnull=True))
           .select_related('idiom').order_by('next_review_date')[:50])
    deck = [{'id': p.idiom.id, 'ex': p.idiom.expression, 'fa': p.idiom.translation_fa,
             'def': p.idiom.definition_en, 'sen': p.idiom.example_en,
             'mastery': p.mastery_level} for p in due if p.idiom.is_active]
    return render(request, 'language_academy/idiom_flashcards.html', {'deck': deck, 'review': True,
                                                                      'level': _user_cefr(request.user)})


@login_required
@require_http_methods(['POST'])
def ai_chat_send(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        message = str(data.get('message') or '').strip()[:800]
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'bad_payload'}, status=400)
    if not message:
        return JsonResponse({'ok': False, 'error': 'empty'}, status=400)
    ctx = str(data.get('context') or 'general')[:20]
    AIChatMessage.objects.create(user=request.user, role='user', content=message, context_type=ctx)
    history = list(AIChatMessage.objects.filter(user=request.user)
                   .order_by('-created_at')[:11].values('role', 'content'))
    history.reverse()
    reply, used_ai = _tutor.tutor_reply(request.user, message, history)
    AIChatMessage.objects.create(user=request.user, role='assistant', content=reply, context_type=ctx)
    old = AIChatMessage.objects.filter(user=request.user).order_by('-id').values_list('id', flat=True)[60:]
    if old:
        AIChatMessage.objects.filter(id__in=list(old)).delete()
    return JsonResponse({'ok': True, 'reply': reply, 'ai': used_ai})


@login_required
def ai_chat_history(request):
    msgs = list(AIChatMessage.objects.filter(user=request.user)
                .order_by('-created_at')[:30].values('role', 'content'))
    msgs.reverse()
    return JsonResponse({'ok': True, 'messages': msgs})


@login_required
@require_http_methods(['POST'])
def ai_challenge_new(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except ValueError:
        data = {}
    source = str(data.get('source') or 'mixed')
    if source not in ('vocab', 'idiom', 'mixed'):
        source = 'mixed'
    ch, created = _tutor.build_challenge(request.user, source)
    return JsonResponse({'ok': True, 'id': ch.id, 'fresh': created,
                         'question': ch.payload.get('question'),
                         'choices': ch.payload.get('choices'), 'source': ch.source})


@login_required
@require_http_methods(['POST'])
def ai_challenge_answer(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        challenge_id = int(data.get('id'))
        index = int(data.get('index'))
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'bad_payload'}, status=400)
    result = _tutor.grade_challenge(request.user, challenge_id, index)
    if result is None:
        return JsonResponse({'ok': False, 'error': 'already_answered'}, status=409)
    return JsonResponse({'ok': True, **result})
