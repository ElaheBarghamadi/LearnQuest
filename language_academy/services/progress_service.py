from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from ..models import (
    UserLessonProgress, UserChapterProgress, UserWorldProgress,
    UserVocabularyProgress, XPTransaction, CoinTransaction,
    UserStreak, DailyGoal, Lesson, Chapter, World
)


class ProgressService:

    @staticmethod
    def update_lesson_progress(user, lesson, status='completed'):
        with transaction.atomic():
            progress, created = UserLessonProgress.objects.get_or_create(
                user=user, lesson=lesson
            )

            if progress.status == 'completed':
                return progress

            progress.status = status
            if status == 'completed':
                progress.progress_percentage = 100
                progress.completed_at = timezone.now()


                XPTransaction.objects.create(
                    user=user,
                    amount=lesson.xp_reward,
                    transaction_type='lesson',
                    source_id=lesson.id,
                    source_model='Lesson'
                )

                CoinTransaction.objects.create(
                    user=user,
                    amount=lesson.coin_reward,
                    transaction_type='earn',
                    source='lesson_completion',
                    source_id=lesson.id
                )


                user.profile.total_xp += lesson.xp_reward
                user.profile.save()


                ProgressService.update_streak(user)


                ProgressService.update_daily_goal(user, xp=lesson.xp_reward, lesson_count=1)

            progress.save()


            ProgressService.update_chapter_progress(user, lesson.chapter)

            return progress

    @staticmethod
    def update_chapter_progress(user, chapter):
        with transaction.atomic():
            progress, created = UserChapterProgress.objects.get_or_create(
                user=user, chapter=chapter
            )

            completed_lessons = UserLessonProgress.objects.filter(
                user=user,
                lesson__chapter=chapter,
                status='completed'
            ).count()

            total_lessons = chapter.lessons.filter(is_published=True).count()

            progress.lessons_completed = completed_lessons
            progress.total_lessons = total_lessons

            if completed_lessons >= total_lessons:

                progress.is_completed = True
                progress.completed_at = timezone.now()

            progress.save()


            ProgressService.update_world_progress(user, chapter.world)

            return progress

    @staticmethod
    def update_world_progress(user, world):
        with transaction.atomic():
            progress, created = UserWorldProgress.objects.get_or_create(
                user=user, world=world
            )

            completed_chapters = UserChapterProgress.objects.filter(
                user=user,
                chapter__world=world,
                is_completed=True
            ).count()

            total_chapters = world.chapters.filter(is_published=True).count()

            progress.chapters_completed = completed_chapters
            progress.total_chapters = total_chapters

            if completed_chapters >= total_chapters:
                progress.is_completed = True
                progress.completed_at = timezone.now()

            progress.save()

            return progress

    @staticmethod
    def update_streak(user):
        streak, created = UserStreak.objects.get_or_create(user=user)
        streak.update_streak()
        return streak

    @staticmethod
    def update_daily_goal(user, xp=0, lesson_count=0, vocabulary_count=0):
        goal, _created = DailyGoal.objects.get_or_create(user=user, goal_date=timezone.localdate())

        goal.current_xp += xp
        goal.current_lessons += lesson_count
        goal.current_vocabulary += vocabulary_count
        goal.save()


        if goal.is_completed() and not getattr(goal, 'bonus_awarded', False):
            XPTransaction.objects.create(
                user=user,
                amount=50,
                transaction_type='daily_goal',
                source_id=goal.id,
                source_model='DailyGoal'
            )
            goal.bonus_awarded = True
            goal.save()

        return goal


class SpacedRepetitionService:

    @staticmethod
    def update_mastery(user, vocabulary, is_correct):
        progress, created = UserVocabularyProgress.objects.get_or_create(
            user=user, vocabulary=vocabulary
        )

        progress.review_count += 1

        if is_correct:
            progress.correct_count += 1
            progress.mastery_score = min(100, progress.mastery_score + 10)


            if progress.mastery_score >= 80 and progress.mastery_level < 4:
                progress.mastery_level = 4
            elif progress.mastery_score >= 60 and progress.mastery_level < 3:
                progress.mastery_level = 3
            elif progress.mastery_score >= 40 and progress.mastery_level < 2:
                progress.mastery_level = 2
            elif progress.mastery_score >= 20 and progress.mastery_level < 1:
                progress.mastery_level = 1
        else:
            progress.incorrect_count += 1
            progress.mastery_score = max(0, progress.mastery_score - 5)
            progress.mastery_level = max(0, progress.mastery_level - 1)

        progress.last_accuracy = (progress.correct_count / progress.review_count) * 100
        progress.last_reviewed = timezone.now()


        days_since_review = (timezone.now() - progress.last_reviewed).days if progress.last_reviewed else 30
        progress.forgetting_risk = min(100, max(0,
                                                (1 - (progress.mastery_score / 100)) * 50 +
                                                (days_since_review / 30) * 50
                                                ))

        progress.calculate_next_review()
        progress.save()

        return progress

    @staticmethod
    def get_due_vocabulary(user, limit=10):
        return UserVocabularyProgress.objects.filter(
            user=user,
            next_review_date__lte=timezone.now(),
            vocabulary__is_active=True
        ).select_related('vocabulary').order_by('forgetting_risk')[:limit]
