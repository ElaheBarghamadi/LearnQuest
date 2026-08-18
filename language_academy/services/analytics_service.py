from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from ..models import (
    UserLessonProgress, UserVocabularyProgress, LearningAnalytics,
    QuizAttempt, ExamAttempt, Vocabulary, Lesson
)


class AnalyticsService:

    @staticmethod
    def update_user_analytics(user):
        analytics, created = LearningAnalytics.objects.get_or_create(user=user)


        analytics.total_lessons_completed = UserLessonProgress.objects.filter(
            user=user, status='completed'
        ).count()

        analytics.total_quizzes_passed = QuizAttempt.objects.filter(
            user=user, passed=True
        ).count()

        analytics.total_exams_passed = ExamAttempt.objects.filter(
            user=user, passed=True
        ).count()

        analytics.vocabulary_learned = UserVocabularyProgress.objects.filter(
            user=user, mastery_level__gte=2
        ).count()


        vocab_progress = UserVocabularyProgress.objects.filter(user=user)
        if vocab_progress.exists():
            analytics.overall_vocabulary_mastery = vocab_progress.aggregate(
                avg=Avg('mastery_score')
            )['avg'] or 0


        weak_grammar = AnalyticsService._identify_weak_grammar_areas(user)
        analytics.weak_grammar_areas = weak_grammar


        weak_vocab = AnalyticsService._identify_weak_vocabulary_categories(user)
        analytics.weak_vocabulary_categories = weak_vocab


        analytics.recommended_lessons = AnalyticsService._generate_recommendations(user)


        analytics.predicted_exam_readiness = AnalyticsService._predict_exam_readiness(user)

        analytics.updated_at = timezone.now()
        analytics.save()

        return analytics

    @staticmethod
    def _identify_weak_grammar_areas(user):


        return [
            {"area": "present_perfect", "accuracy": 45, "priority": "high"},
            {"area": "prepositions", "accuracy": 55, "priority": "medium"},
        ]

    @staticmethod
    def _identify_weak_vocabulary_categories(user):
        weak_categories = []
        vocab_progress = UserVocabularyProgress.objects.filter(
            user=user, mastery_score__lt=50
        ).select_related('vocabulary')

        category_stats = {}
        for progress in vocab_progress:
            for category in progress.vocabulary.categories.all():
                if category.name not in category_stats:
                    category_stats[category.name] = {'count': 0, 'total_score': 0}
                category_stats[category.name]['count'] += 1
                category_stats[category.name]['total_score'] += progress.mastery_score

        for category, stats in category_stats.items():
            if stats['count'] >= 3:
                avg_score = stats['total_score'] / stats['count']
                if avg_score < 50:
                    weak_categories.append({
                        "category": category,
                        "average_mastery": round(avg_score, 1),
                        "words_count": stats['count']
                    })

        return weak_categories

    @staticmethod
    def _generate_recommendations(user):
        recommendations = []


        weak_categories_data = AnalyticsService._identify_weak_vocabulary_categories(user)

        for weak in weak_categories_data:
            category_name = weak['category']


            lessons = Lesson.objects.filter(
                chapter__world__is_published=True,
                is_published=True
            ).exclude(
                user_progress__user=user, user_progress__status='completed'
            )[:3]

            for lesson in lessons:
                recommendations.append({
                    "lesson_id": lesson.id,
                    "lesson_name": lesson.name,
                    "reason": f"Improve {category_name} vocabulary",
                    "priority": weak.get('priority', 'medium')
                })

        return recommendations[:5]

    @staticmethod
    def _predict_exam_readiness(user):

        recent_quizzes = QuizAttempt.objects.filter(
            user=user,
            completed_at__gte=timezone.now() - timedelta(days=30)
        )

        if recent_quizzes.exists():
            avg_score = recent_quizzes.aggregate(avg=Avg('score'))['avg'] or 0
        else:
            avg_score = 0


        return {
            "chapter_exam_ready": avg_score >= 65,
            "world_exam_ready": avg_score >= 70,
            "final_exam_ready": avg_score >= 75,
            "confidence_percentage": min(100, avg_score),
            "recommended_study_days": max(0, 7 - int(avg_score / 15))
        }
