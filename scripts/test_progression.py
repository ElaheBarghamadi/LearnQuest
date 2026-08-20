"""تست کامل زنجیرهٔ پیشروی آکادمی (اجرا: python scripts/test_progression.py)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from language_academy.models import (
    World, Chapter, Lesson, UserLessonProgress, UserChapterProgress,
    UserWorldProgress, Quiz, QuizAttempt, Exam, ExamAttempt,
)

PASSED, FAILED = [], []


def T(name, cond, extra=''):
    (PASSED if cond else FAILED).append(name)
    print(('  ✅' if cond else '  ❌'), name, '' if cond else extra)


def main():
    U = get_user_model()
    u, _ = U.objects.get_or_create(username='progflow', defaults={
        'email': 'progflow@t.com', 'password': 'pbkdf2_sha256$dummy'})
    u.set_password('Passw0rd!')
    u.save()

    # پاک کردن پیشرفت قبلی کاربر
    UserLessonProgress.objects.filter(user=u).delete()
    UserChapterProgress.objects.filter(user=u).delete()
    UserWorldProgress.objects.filter(user=u).delete()

    c = Client()
    c.login(username='progflow', password='Passw0rd!')

    worlds = list(World.objects.filter(is_published=True).order_by('order'))
    w1, w2, w3 = worlds
    chs1 = list(w1.chapters.filter(is_published=True).order_by('order'))
    ch1 = chs1[0]
    ch2 = chs1[1] if len(chs1) > 1 else None
    lessons = list(ch1.lessons.filter(is_published=True).order_by('order'))

    print('=== ۱) پیش‌نیاز: جهان ۲ قفل است ===')
    r = c.get(f'/academy/world/{w2.id}/')
    T('جهان ۲ قفل → ریدایرکت', r.status_code in (301, 302))

    print('=== ۲) تکمیل همهٔ درس‌های فصل ۱ (شبیه‌سازی pass کوئیز) ===')
    for l in lessons:
        p, _ = UserLessonProgress.objects.get_or_create(user=u, lesson=l)
        p.status = 'completed'
        p.progress_percentage = 100
        p.quiz_passed = True
        p.completed_at = timezone.now()
        p.save()

    print('=== ۳) امتحان فصل ۱: اول باید رد شود (همه درس‌ها مانده → حالا OK) ===')
    r = c.get(f'/academy/exam/{ch1.exams.first().id}/')
    T('امتحان فصل ۱ بعد از تکمیل درس‌ها باز است', r.status_code == 200, f'{r.status_code}')

    # ثبت امتحان پاس‌شده مستقیم (شبیه‌سازی submit)
    exam = ch1.exams.first()
    ExamAttempt.objects.create(user=u, exam=exam, score=90, passed=True,
                               answers={}, completed_at=timezone.now())
    cp, _ = UserChapterProgress.objects.get_or_create(user=u, chapter=ch1)
    cp.exam_score = 90
    cp.exam_passed = True
    cp.is_completed = True
    cp.completed_at = timezone.now()
    cp.save()

    print('=== ۴) فصل بعدی حالا باز است ===')
    if ch2:
        r = c.get(f'/academy/chapter/{ch2.id}/')
        T('فصل بعدی باز شد', r.status_code == 200, f'{r.status_code}')
    else:
        T('فصل بعدی (ندارد — رد شد)', True)

    print('=== ۵) جهان ۱ هنوز کامل نشده → جهان ۲ قفل ===')
    r = c.get(f'/academy/world/{w2.id}/')
    T('جهان ۲ همچنان قفل (جهان ۱ ناقص)', r.status_code in (301, 302))

    print('=== ۶) تکمیل بقیهٔ فصل‌های جهان ۱ ===')
    for ch in w1.chapters.filter(is_published=True).exclude(pk=ch1.pk):
        for l in ch.lessons.filter(is_published=True):
            p, _ = UserLessonProgress.objects.get_or_create(user=u, lesson=l)
            p.status = 'completed'
            p.progress_percentage = 100
            p.quiz_passed = True
            p.completed_at = timezone.now()
            p.save()
        e = ch.exams.first()
        if e:
            ExamAttempt.objects.create(user=u, exam=e, score=90, passed=True,
                                       answers={}, completed_at=timezone.now())
        cpc, _ = UserChapterProgress.objects.get_or_create(user=u, chapter=ch)
        cpc.exam_score = 90
        cpc.exam_passed = True
        cpc.is_completed = True
        cpc.completed_at = timezone.now()
        cpc.save()

    print('=== ۷) امتحان نهایی جهان ۱ + تکمیل جهان ===')
    we = w1.exams.first()
    r = c.get(f'/academy/exam/{we.id}/')
    T('امتحان نهایی جهان ۱ باز است', r.status_code == 200, f'{r.status_code}')
    ExamAttempt.objects.create(user=u, exam=we, score=90, passed=True,
                               answers={}, completed_at=timezone.now())
    wp, _ = UserWorldProgress.objects.get_or_create(user=u, world=w1)
    wp.exam_score = 90
    wp.exam_passed = True
    wp.save(update_fields=['exam_score', 'exam_passed'])
    wp.update_progress()
    T('جهان ۱ کامل شد', wp.is_completed)

    print('=== ۸) جهان ۲ حالا باز است ===')
    r = c.get(f'/academy/world/{w2.id}/')
    T('جهان ۲ باز شد', r.status_code == 200, f'{r.status_code}')

    print('=== ۹) جهان ۳ هنوز قفل ===')
    r = c.get(f'/academy/world/{w3.id}/')
    T('جهان ۳ قفل', r.status_code in (301, 302))

    print()
    print(f'RESULT: {len(PASSED)} passed, {len(FAILED)} failed')
    if FAILED:
        print('FAILED:', FAILED)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
