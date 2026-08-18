from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from ..models import (
    World, Chapter, Lesson, Vocabulary, Quiz, QuizAttempt,
    Exam, ExamAttempt, UserLessonProgress, UserVocabularyProgress
)
from ..serializers import (
    WorldSerializer, ChapterSerializer, LessonSerializer,
    VocabularySerializer, QuizSerializer, QuizAttemptSerializer,
    ExamSerializer, ExamAttemptSerializer, ProgressSerializer
)
from ..services.progress_service import ProgressService, SpacedRepetitionService
from ..services.ai_service import AIService


class WorldViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WorldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return World.objects.filter(is_published=True)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        world = self.get_object_or_404()
        progress = UserWorldProgress.objects.filter(
            user=request.user, world=world
        ).first()

        return Response({
            'world': world.name,
            'is_completed': progress.is_completed if progress else False,
            'completion_percentage': world.get_completion_percentage(request.user),
            'chapters_completed': progress.chapters_completed if progress else 0,
            'total_chapters': world.get_chapter_count()
        })


class ChapterViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chapter.objects.filter(is_published=True)

    @action(detail=True, methods=['get'])
    def unlock_status(self, request, pk=None):
        chapter = self.get_object()
        is_unlocked = chapter.is_unlocked_for_user(request.user)

        return Response({
            'chapter_id': chapter.id,
            'is_unlocked': is_unlocked,
            'required_chapter': chapter.required_chapter.name if chapter.required_chapter else None,
            'required_score': chapter.unlock_score
        })


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.filter(is_published=True)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        lesson = self.get_object()
        progress = ProgressService.update_lesson_progress(request.user, lesson)

        return Response({
            'status': 'completed',
            'xp_earned': lesson.xp_reward,
            'coin_earned': lesson.coin_reward
        })

    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        lesson = self.get_object()
        content = lesson.content

        return Response({
            'introduction': content.introduction if content else '',
            'learning_objectives': content.learning_objectives if content else [],
            'grammar_notes': content.grammar_notes if content else '',
            'example_sentences': content.example_sentences if content else [],
            'summary': content.summary if content else ''
        })


class VocabularyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VocabularySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vocabulary.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def due_for_review(self, request):
        due_words = SpacedRepetitionService.get_due_vocabulary(request.user)
        serializer = self.get_serializer([dw.vocabulary for dw in due_words], many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        vocabulary = self.get_object()
        is_correct = request.data.get('is_correct', False)

        progress = SpacedRepetitionService.update_mastery(
            request.user, vocabulary, is_correct
        )

        return Response({
            'mastery_score': progress.mastery_score,
            'mastery_level': progress.mastery_level,
            'next_review_date': progress.next_review_date
        })


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(is_published=True)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        answers = request.data.get('answers', {})


        total_points = 0
        earned_points = 0

        for question in quiz.questions.all():
            total_points += question.points
            user_answer = answers.get(str(question.id))

            if question.question_type == 'mcq':
                correct_choice = question.choices.filter(is_correct=True).first()
                if correct_choice and user_answer == correct_choice.id:
                    earned_points += question.points
            elif question.question_type == 'fill_blank':
                if user_answer and user_answer.lower().strip() == question.blank_answer.lower().strip():
                    earned_points += question.points

        score = int((earned_points / total_points) * 100) if total_points > 0 else 0
        passed = score >= quiz.passing_score


        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed,
            answers=answers,
            completed_at=timezone.now()
        )


        if passed:
            ProgressService.update_lesson_progress(request.user, quiz.lesson)

        return Response({
            'score': score,
            'passed': passed,
            'xp_earned': quiz.xp_reward if passed else 0,
            'attempt_id': attempt.id
        })


class ExamViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Exam.objects.filter(is_published=True)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        exam = self.get_object()
        answers = request.data.get('answers', {})


        total_points = sum(q.points for q in exam.get_questions())
        earned_points = 0

        for exam_question in exam.get_questions():
            user_answer = answers.get(str(exam_question.id))
            if user_answer and user_answer == exam_question.correct_answer:
                earned_points += exam_question.points

        score = int((earned_points / total_points) * 100) if total_points > 0 else 0
        passed = score >= exam.passing_score

        attempt = ExamAttempt.objects.create(
            user=request.user,
            exam=exam,
            score=score,
            passed=passed,
            answers=answers,
            completed_at=timezone.now()
        )


        if exam.chapter and passed:
            chapter_progress = UserChapterProgress.objects.filter(
                user=request.user, chapter=exam.chapter
            ).first()
            if chapter_progress:
                chapter_progress.exam_score = score
                chapter_progress.exam_passed = passed
                chapter_progress.save()


                ProgressService.update_chapter_progress(request.user, exam.chapter)

        return Response({
            'score': score,
            'passed': passed,
            'xp_earned': exam.xp_reward if passed else 0,
            'attempt_id': attempt.id
        })


class AIViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def evaluate_speaking(self, request):
        prompt = request.data.get('prompt', '')
        transcript = request.data.get('transcript', '')
        audio_file = request.FILES.get('audio')


        submission = SpeakingSubmission.objects.create(
            user=request.user,
            prompt=prompt,
            transcript=transcript,
            audio_file=audio_file
        )


        evaluation = AIService.evaluate_speaking(prompt, transcript)


        submission.ai_feedback = evaluation
        submission.pronunciation_score = evaluation.get('pronunciation_score')
        submission.fluency_score = evaluation.get('fluency_score')
        submission.grammar_score = evaluation.get('grammar_score')
        submission.vocabulary_score = evaluation.get('vocabulary_score')
        submission.overall_score = evaluation.get('overall_score')
        submission.evaluated_at = timezone.now()
        submission.save()

        return Response(evaluation)

    @action(detail=False, methods=['post'])
    def evaluate_writing(self, request):
        prompt = request.data.get('prompt', '')
        submission_text = request.data.get('submission', '')


        submission = WritingSubmission.objects.create(
            user=request.user,
            prompt=prompt,
            submission=submission_text
        )


        evaluation = AIService.evaluate_writing(prompt, submission_text)


        submission.ai_feedback = evaluation
        submission.grammar_score = evaluation.get('grammar_score')
        submission.vocabulary_score = evaluation.get('vocabulary_score')
        submission.coherence_score = evaluation.get('coherence_score')
        submission.overall_score = evaluation.get('overall_score')
        submission.evaluated_at = timezone.now()
        submission.save()

        return Response(evaluation)

    @action(detail=False, methods=['post'])
    def correct_grammar(self, request):
        text = request.data.get('text', '')
        result = AIService.correct_grammar(text)
        return Response(result)


class ProgressViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):

        worlds = World.objects.filter(is_published=True)
        world_progress = []

        for world in worlds:
            progress = UserWorldProgress.objects.filter(
                user=request.user, world=world
            ).first()
            world_progress.append({
                'id': world.id,
                'name': world.name,
                'order': world.order,
                'is_completed': progress.is_completed if progress else False,
                'completion_percentage': world.get_completion_percentage(request.user),
                'chapters_completed': progress.chapters_completed if progress else 0,
                'total_chapters': world.get_chapter_count(),
                'is_locked': world.order > 1 and not World.objects.filter(
                    order=world.order - 1, user_progress__user=request.user,
                    user_progress__is_completed=True
                ).exists()
            })


        streak = request.user.streak if hasattr(request.user, 'streak') else None


        daily_goal = request.user.daily_goal if hasattr(request.user, 'daily_goal') else None

        return Response({
            'total_xp': getattr(request.user.profile, 'total_xp', 0),
            'total_coins': getattr(request.user.profile, 'total_coins', 0),
            'current_streak': streak.current_streak if streak else 0,
            'longest_streak': streak.longest_streak if streak else 0,
            'daily_goal': {
                'current_xp': daily_goal.current_xp if daily_goal else 0,
                'target_xp': daily_goal.target_xp if daily_goal else 100,
                'is_completed': daily_goal.is_completed() if daily_goal else False
            } if daily_goal else None,
            'worlds': world_progress,
            'recent_achievements': [],
            'vocabulary_stats': {
                'total_learned': UserVocabularyProgress.objects.filter(
                    user=request.user, mastery_level__gte=2
                ).count(),
                'due_for_review': UserVocabularyProgress.objects.filter(
                    user=request.user, next_review_date__lte=timezone.now()
                ).count()
            }
        })
