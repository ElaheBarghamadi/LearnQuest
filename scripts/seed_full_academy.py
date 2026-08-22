# -*- coding: utf-8 -*-
"""
اسکریپت کامل پر کردن آکادمی — ۳ جهان + گرامرها + درس‌های ویژه (پولی)

اجرا:  python scripts/seed_full_academy.py
این اسکریپت idempotent است (اجرای دوباره، رکورد تکراری نمی‌سازد).

تولید می‌کند:
- ۳ جهان کامل (Airport Adventures، Restaurant & Food، Everyday Life & City)
- فصل‌ها و درس‌ها با محتوای کامل (مقدمه، اهداف، خلاصه، نکات، متن خواندن + ترجمه)
- نکات گرامری (GrammarPoint) برای هر درس — الهام‌گرفته از Grammar in Use
- واژگان هر درس + دسته‌بندی
- کوئیز هر درس + امتحان هر جهان
- دیالوگ برای درس‌ها
- درس‌های ویژه (exclusive) + محصول بلیط در فروشگاه
- تصاویر گرادیانی برای جهان/فصل/درس/واژگان (با PIL)
"""
import os
import sys
import hashlib
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')

import django
django.setup()

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from language_academy.models import (
    World, Chapter, Lesson, LessonContent, GrammarPoint,
    Vocabulary, VocabularyCategory, VocabularyExample,
    Quiz, Question, QuestionChoice, Exam, ExamQuestion,
    Dialogue, DialogueScene, DialogueChoice,
)
from shop.models import Product, Category

from scripts.content_worlds import WORLDS, WORLD_EXAMS, EXCLUSIVE_LESSONS
from scripts.content_grammar import GRAMMAR_BANK

# ---------------------------------------------------------------
# تولید تصویر گرادیانی با PIL (بدون نیاز به فایل خارجی)
# ---------------------------------------------------------------
def _color_for(text, palette_idx=0):
    palettes = [
        ((108, 99, 255), (54, 209, 220)),
        ((30, 168, 154), (232, 163, 61)),
        ((236, 72, 153), (99, 102, 241)),
        ((59, 130, 246), (30, 64, 175)),
        ((16, 185, 129), (5, 150, 105)),
        ((245, 158, 11), (217, 119, 6)),
        ((139, 92, 246), (76, 29, 149)),
        ((14, 165, 233), (2, 132, 199)),
    ]
    h = int(hashlib.md5(str(text).encode('utf-8')).hexdigest(), 16)
    c1, c2 = palettes[(h + palette_idx) % len(palettes)]
    return c1, c2


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_gradient_image(text, filename, size=(640, 360), emoji=None):
    """ساخت تصویر گرادیانی با متن فارسی/انگلیسی وسط."""
    from PIL import Image, ImageDraw, ImageFilter

    c1, c2 = _color_for(text)
    img = Image.new('RGB', size)
    px = img.load()
    for y in range(size[1]):
        t = y / size[1]
        col = _lerp(c1, c2, t)
        for x in range(size[0]):
            px[x, y] = col

    # هاله‌های نوری
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([-80, -80, 260, 260], fill=(255, 255, 255, 36))
    od.ellipse([size[0] - 200, size[1] - 200, size[0] + 120, size[1] + 120], fill=(255, 255, 255, 26))
    overlay = overlay.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img.convert('RGBA'), overlay)

    d = ImageDraw.Draw(img)
    # ایموجی بزرگ (فونت سیستمی)
    if emoji:
        try:
            from PIL import ImageFont
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 110)
            d.text((size[0] // 2, size[1] // 2 - 30), emoji, font=font, anchor='mm', fill=(255, 255, 255, 235))
        except Exception:
            pass
    # متن
    try:
        from PIL import ImageFont
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 26)
        d.text((size[0] // 2, size[1] - 50), text[:38], font=font, anchor='mm', fill=(255, 255, 255, 220))
    except Exception:
        pass

    out = os.path.join(settings.MEDIA_ROOT, filename)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert('RGB').save(out, quality=88)
    return filename


# ---------------------------------------------------------------
# ساخت درس
# ---------------------------------------------------------------
def build_lesson(chapter, data, order, is_exclusive=False):
    lesson, created = Lesson.objects.update_or_create(
        chapter=chapter, order=order,
        defaults={
            'name': data['name'],
            'name_fa': data['name_fa'],
            'lesson_type': data['type'],
            'xp_reward': 60,
            'coin_reward': 15,
            'estimated_time_minutes': 20,
            'is_published': True,
            'is_free_preview': not is_exclusive,
            'is_exclusive': is_exclusive,
        },
    )

    content_data = data['content']
    content, _ = LessonContent.objects.update_or_create(
        lesson=lesson,
        defaults={
            'introduction': content_data['introduction'],
            'learning_objectives': content_data['objectives'],
            'summary': content_data['summary'],
            'key_takeaways': content_data['takeaways'],
            'is_interactive': True,
            'allow_skip': False,
            'display_options': {'image_align': 'center', 'image_width': 80},
        },
    )

    # گرامر داخل درس
    grammar_html = []
    for gk in data.get('grammar_keys', []):
        g = GRAMMAR_BANK.get(gk)
        if g:
            grammar_html.append(
                f"<h4>📘 {g['title']}</h4><p><code dir='ltr'>{g['structure']}</code></p>"
                f"<div>{g['explanation']}</div>"
                f"<ul>{''.join('<li><b>' + ex['en'] + '</b> — ' + ex['fa'] + '</li>' for ex in g['examples'][:3])}</ul>"
            )
            _create_grammar_point(lesson, g, gk, data['grammar_keys'].index(gk))
    content.grammar_notes = '\n'.join(grammar_html) if grammar_html else content.grammar_notes
    content.grammar_examples = [
        ex['en'] for gk in data.get('grammar_keys', [])
        for ex in GRAMMAR_BANK.get(gk, {}).get('examples', [])
    ]

    # مثال‌ها و متن خواندن
    content.example_sentences = [
        ex['en'] for gk in data.get('grammar_keys', [])
        for ex in GRAMMAR_BANK.get(gk, {}).get('examples', [])[:3]
    ]
    if data.get('reading'):
        r = data['reading']
        content.reading_text = r['en']
        content.reading_translation = r['fa']
        content.reading_notes = r['notes']

    # تصویر درس
    img_name = make_gradient_image(lesson.name, f"lesson_images/lesson_{lesson.id}.jpg", emoji=_type_emoji(lesson.lesson_type))
    content.featured_image = img_name
    content.save()

    _build_vocab(lesson, data.get('vocab', []))
    _build_quiz(lesson, data['quiz'])
    if data.get('dialogue'):
        _build_dialogue(lesson, data['dialogue'])
    return lesson, created


def _type_emoji(t):
    return {'vocabulary': '📚', 'grammar': '📝', 'dialogue': '💬', 'reading': '📖',
            'listening': '🎧', 'writing': '✍️', 'speaking': '🗣️', 'mixed': '⭐'}.get(t, '⭐')


def _create_grammar_point(lesson, g, key, order):
    GrammarPoint.objects.update_or_create(
        lesson=lesson, order=order,
        defaults={
            'title': g['title'],
            'title_fa': g.get('title_fa', ''),
            'level': g['level'],
            'structure': g['structure'],
            'explanation': g['explanation'],
            'examples': g['examples'],
            'common_mistakes': g.get('common_mistakes', ''),
            'usage_tips': g.get('usage_tips', ''),
        },
    )


# ---------------------------------------------------------------
# واژگان
# ---------------------------------------------------------------
def _build_vocab(lesson, vocab_list):
    cat, _ = VocabularyCategory.objects.get_or_create(
        name=lesson.name[:50],
        defaults={
            'name_fa': lesson.name_fa or lesson.name,
            'description': f'Vocabulary for {lesson.name}',
            'icon': 'book',
            'order': lesson.chapter.world.order * 100 + lesson.order,
        },
    )
    for word, meaning_fa, level in vocab_list:
        v, _ = Vocabulary.objects.update_or_create(
            word=word, defaults={
                'meaning': meaning_fa,
                'meaning_fa': meaning_fa,
                'difficulty': level,
                'is_active': True,
            },
        )
        v.categories.add(cat)
        if not v.examples.exists():
            VocabularyExample.objects.create(
                vocabulary=v,
                sentence=f'Example sentence with "{word}".',
                sentence_fa=f'Example sentence with "{word}".',
            )


# ---------------------------------------------------------------
# کوئیز
# ---------------------------------------------------------------
def _build_quiz(lesson, quiz_data):
    quiz, _ = Quiz.objects.update_or_create(
        lesson=lesson,
        defaults={
            'title': f'Quiz: {lesson.name}',
            'description': f'Test your knowledge of {lesson.name}!',
            'passing_score': 70,
            'time_limit_minutes': 10,
            'max_attempts': 3,
            'shuffle_questions': True,
            'xp_reward': 40,
            'coin_reward': 15,
            'is_published': True,
        },
    )
    # بازسازی کامل سوالات (جلوگیری از رکوردهای تکراری اجراهای قبلی)
    Question.objects.filter(quiz=quiz).delete()
    for i, qd in enumerate(quiz_data):
        q, _ = Question.objects.update_or_create(
            quiz=quiz, order=i,
            defaults={
                'question_type': qd['type'],
                'question_text': qd['q'],
                'points': 10,
                'hint': qd.get('hint', ''),
                'explanation': qd.get('explain', ''),
            },
        )
        for j, ch in enumerate(qd['choices']):
            QuestionChoice.objects.update_or_create(
                question=q, order=j,
                defaults={'choice_text': ch, 'is_correct': (j == qd['correct'])},
            )


# ---------------------------------------------------------------
# دیالوگ
# ---------------------------------------------------------------
def _build_dialogue(lesson, dlg):
    dialogue, _ = Dialogue.objects.update_or_create(
        lesson=lesson, order=1,
        defaults={
            'title': dlg['title'],
            'title_fa': dlg['title_fa'],
            'description': f'Practice a real conversation about {lesson.name}.',
            'difficulty': lesson.chapter.world.difficulty_level,
            'is_active': True,
        },
    )
    for i, (char, en, fa, is_user) in enumerate(dlg['scenes']):
        scene, _ = DialogueScene.objects.update_or_create(
            dialogue=dialogue, order=i + 1,
            defaults={
                'character': char,
                'message': en,
                'message_fa': fa,
                'is_user_turn': is_user,
            },
        )
        if not scene.choices.exists():
            DialogueChoice.objects.get_or_create(
                scene=scene,
                defaults={
                    'choice_text': 'Continue the conversation',
                    'choice_text_fa': 'ادامهٔ گفتگو',
                    'is_correct': True,
                    'feedback': 'Good job! Keep going.',
                    'feedback_fa': 'آفرین! ادامه بده.',
                    'xp_reward': 5,
                },
            )


# ---------------------------------------------------------------
# امتحان فصل — از سوالات کوئیز درس‌های همان فصل
# ---------------------------------------------------------------
def _build_chapter_exam(chapter):
    from language_academy.models import Question, QuestionChoice as QC
    exam, _ = Exam.objects.update_or_create(
        exam_type='chapter', chapter=chapter,
        defaults={
            'title': f'{chapter.name} — Chapter Exam',
            'description': f'Pass this exam to complete «{chapter.name}» and unlock the next chapter!',
            'passing_score': 70,
            'time_limit_minutes': 12,
            'max_attempts': 3,
            'questions_count': 5,
            'randomize_questions': True,
            'xp_reward': 120,
            'coin_reward': 30,
            'is_published': True,
        },
    )
    # جمع‌آوری سوالات از کوئیز درس‌های فصل (حداکثر ۵)
    qs = list(Question.objects.filter(quiz__lesson__chapter=chapter).order_by('order'))
    picked = qs[:5]
    ExamQuestion.objects.filter(exam=exam).delete()
    for i, q in enumerate(picked):
        choices = list(q.choices.order_by('order'))
        correct = next((ch for ch in choices if ch.is_correct), choices[0] if choices else None)
        ExamQuestion.objects.create(
            exam=exam, order=i,
            question=q.question_text,
            question_type='mcq',
            correct_answer=correct.choice_text if correct else '',
            options=[ch.choice_text for ch in choices],
            points=10,
        )
    return exam


# ---------------------------------------------------------------
# امتحان جهان
# ---------------------------------------------------------------
def _build_world_exam(world, exam_data):
    exam, _ = Exam.objects.update_or_create(
        exam_type='world', world=world,
        defaults={
            'title': exam_data['title'],
            'description': exam_data['description'],
            'passing_score': exam_data['passing_score'],
            'time_limit_minutes': exam_data['time_limit'],
            'max_attempts': 3,
            'questions_count': len(exam_data['questions']),
            'randomize_questions': True,
            'xp_reward': 300,
            'coin_reward': 80,
            'is_published': True,
        },
    )
    for i, qd in enumerate(exam_data['questions']):
        ExamQuestion.objects.update_or_create(
            exam=exam, order=i,
            defaults={
                'question': qd['q'],
                'question_type': qd['type'],
                'correct_answer': qd['options'][qd['answer']],
                'options': qd['options'],
                'points': 10,
            },
        )


# ---------------------------------------------------------------
# محصول بلیط درس ویژه
# ---------------------------------------------------------------
def _build_ticket_product(world, lesson, price=400):
    cat, _ = Category.objects.get_or_create(
        slug='unlocks',
        defaults={'name': 'بازکننده محتوا', 'emoji': '🔓', 'order': 15, 'is_active': True},
    )
    slug = f'ticket-{world.order}-{lesson.id}'
    product, created = Product.objects.update_or_create(
        slug=slug,
        defaults={
            'name': f'🎫 بلیط درس ویژه: {lesson.name}',
            'category': cat,
            'product_type': 'unlock',
            'effect_type': 'exclusive_lesson',
            'effect_payload': {'lesson_id': lesson.id},
            'description': f'دسترسی دائمی به درس ویژه «{lesson.name}» در جهان «{world.name}».',
            'price_coins': price,
            'is_active': True,
            'is_featured': True,
        },
    )
    return product, created


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
def _check_migrations():
    """اگر مهاجرت‌های pending وجود داشت، پیام واضح بده و خارج شو."""
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(connections['default'])
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    if plan:
        print('⚠️  ابتدا مهاجرت‌ها را اعمال کنید:')
        print('    uv run python manage.py migrate')
        print('    (یا: python manage.py migrate)')
        print('سپس دوباره این اسکریپت را اجرا کنید.')
        for migration, _backwards in plan[:8]:
            print(f'    - {migration.app_label}.{migration.name}')
        raise SystemExit(1)


def main():
    _check_migrations()
    print('🚀 شروع پر کردن کامل آکادمی…')
    print('=' * 60)

    total_lessons = 0
    total_grammar = 0
    total_vocab = 0
    total_quiz_q = 0

    for wdata in WORLDS:
        # جهان
        world, _ = World.objects.update_or_create(
            order=wdata['order'],
            defaults={
                'name': wdata['name'],
                'name_fa': wdata['name_fa'],
                'description': wdata['description'],
                'difficulty_level': wdata['difficulty'],
                'xp_reward': 800,
                'coin_reward': 200,
                'is_published': True,
            },
        )
        # ترتیب قطعی بر اساس نام (جلوگیری از به‌هم‌ریختگی بعد از اجراهای قبلی)
        fixed_order = {'Airport Adventures': 1, 'Restaurant & Food': 2, 'Everyday Life & City': 3}
        world.order = fixed_order.get(wdata['name'], world.order)
        img_name = make_gradient_image(world.name, f"worlds/world_{world.id}.jpg",
                                       emoji={1: '✈️', 2: '🍽️', 3: '🏙️'}.get(world.order, '🌍'))
        world.image = img_name
        world.save()

        # فصل‌ها
        for cdata in wdata['chapters']:
            chapter, _ = Chapter.objects.update_or_create(
                world=world, order=cdata['order'],
                defaults={
                    'name': cdata['name'],
                    'name_fa': cdata['name_fa'],
                    'description': f"Master {cdata['name']} and unlock the next step.",
                    'passing_score': cdata['passing_score'],
                    'estimated_time_minutes': 60,
                    'xp_reward': 150,
                    'coin_reward': 40,
                    'is_published': True,
                },
            )

            # درس‌ها
            for lorder, ldata in enumerate(cdata['lessons'], start=1):
                lesson, created = build_lesson(chapter, ldata, lorder)
                total_lessons += 1
                total_grammar += GrammarPoint.objects.filter(lesson=lesson).count()
                total_vocab += Vocabulary.objects.filter(categories__name=lesson.name[:50]).count()
                total_quiz_q += Question.objects.filter(quiz__lesson=lesson).count()
                print(f'  {"✅" if created else "↻"} درس: {lesson.name}')

            # امتحان فصل (برای تکمیل فصل و باز شدن فصل بعد)
            _build_chapter_exam(chapter)
            print(f'  🎓 امتحان فصل: {chapter.name}')

        # مرتب‌سازی نهایی فصل‌ها و درس‌های این جهان بر اساس ترتیب ثبت
        for i, ch in enumerate(world.chapters.order_by('id'), start=1):
            if ch.order != i:
                ch.order = i; ch.save(update_fields=['order'])
            for j, l in enumerate(ch.lessons.order_by('id'), start=1):
                if l.order != j:
                    l.order = j; l.save(update_fields=['order'])

        # امتحان جهان
        if wdata['name'] in WORLD_EXAMS:
            _build_world_exam(world, WORLD_EXAMS[wdata['name']])
            print(f'  🎓 امتحان جهان: {world.name}')

        # درس ویژه (پولی)
        if wdata['name'] in EXCLUSIVE_LESSONS:
            edata = EXCLUSIVE_LESSONS[wdata['name']]
            chapter = world.chapters.order_by('order').first()
            # درس ویژه را با نام پیدا کن (idempotent) — اگر بود به‌روزرسانی، وگرنه بساز
            existing = Lesson.objects.filter(chapter=chapter, name=edata['name']).first()
            if existing:
                build_lesson(chapter, edata, existing.order, is_exclusive=True)
                lesson = existing
                created = False
            else:
                last_order = chapter.lessons.count() + 1
                lesson, created = build_lesson(chapter, edata, last_order, is_exclusive=True)
            product, pcreated = _build_ticket_product(world, lesson)
            print(f'  👑 درس ویژه (پولی): {lesson.name} — بلیط: {product.slug} ({"جدید" if created else "موجود"})')

    print()
    print('=' * 60)
    print(f'✅ آکادمی کامل شد!')
    print(f'   🌍 جهان‌ها: {World.objects.count()}')
    print(f'   📚 فصل‌ها: {Chapter.objects.count()}')
    print(f'   📖 درس‌ها: {Lesson.objects.count()}')
    print(f'   📘 نکات گرامری: {GrammarPoint.objects.count()}')
    print(f'   📕 واژگان: {Vocabulary.objects.count()}')
    print(f'   ❓ سوالات کوئیز: {Question.objects.count()}')
    print(f'   🎓 امتحان‌ها: {Exam.objects.count()}')
    print(f'   💬 دیالوگ‌ها: {Dialogue.objects.count()}')
    print(f'   👑 درس‌های ویژه: {Lesson.objects.filter(is_exclusive=True).count()}')
    print('=' * 60)


if __name__ == '__main__':
    main()
