"""
Seed GrammarPoint objects from scripts/content_grammar.py into published lessons.

Idempotent: safe to run multiple times. Maps grammar packs to lessons based on
the world/chapter/lesson order coming from seed_data.py.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from language_academy.models import GrammarPoint, Lesson


# ------------------------------------------------------------------
# نگاشت درس‌ها به کلید(های) گرامر — با ترتیب world/chapter/lesson
# ------------------------------------------------------------------
# هر آیتم: ((world_order, chapter_order, lesson_order), [grammar_keys...])
LESSON_GRAMMAR_MAP = [
    # ---------- World 1 : Airport Adventures ----------
    ((1, 1, 1), ["present_simple_to_be"]),
    ((1, 1, 2), ["present_simple_actions", "there_is_are"]),
    ((1, 1, 3), ["imperatives", "modals_can_must"]),

    ((1, 2, 1), ["past_simple"]),
    ((1, 2, 2), ["present_continuous", "adverbs_frequency"]),
    ((1, 2, 3), ["future_will_going"]),

    ((1, 3, 1), ["past_continuous"]),
    ((1, 3, 2), ["prepositions_place", "prepositions_time"]),
    ((1, 3, 3), ["present_perfect"]),

    # ---------- World 2 : Restaurant & Food ----------
    ((2, 1, 1), ["some_any", "countable_uncountable"]),
    ((2, 1, 2), ["would_like"]),
    ((2, 1, 3), ["comparatives"]),

    ((2, 2, 1), ["gerunds_infinitives"]),
    ((2, 2, 2), ["passive"]),
    ((2, 2, 3), ["present_perfect_2"]),

    ((2, 3, 1), ["zero_first_conditional"]),
    ((2, 3, 2), ["second_conditional", "relative_clauses"]),
    ((2, 3, 3), ["reported_speech", "question_tags"]),
]


class Command(BaseCommand):
    help = "Seed GrammarPoint objects from scripts/content_grammar.py (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete existing GrammarPoint objects before seeding.",
        )

    def handle(self, *args, **opts):
        # بارگذاری بانک محتوا از scripts/
        import sys
        from pathlib import Path
        base = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(base / "scripts"))
        try:
            from content_grammar import GRAMMAR_BANK
        except ImportError as e:
            self.stderr.write(self.style.ERROR(
                f"❌ Cannot import scripts/content_grammar.py: {e}"
            ))
            return

        if opts.get("wipe"):
            n = GrammarPoint.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"🗑  Deleted {n} old GrammarPoint(s)."))

        created = 0
        updated = 0
        skipped_lessons = 0
        skipped_keys = 0

        with transaction.atomic():
            for (w_ord, ch_ord, l_ord), keys in LESSON_GRAMMAR_MAP:
                lesson = (Lesson.objects
                          .filter(chapter__world__order=w_ord,
                                  chapter__order=ch_ord,
                                  order=l_ord)
                          .select_related('chapter', 'chapter__world')
                          .first())
                if not lesson:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  Lesson W{w_ord}·C{ch_ord}·L{l_ord} not found — skipping."
                    ))
                    skipped_lessons += 1
                    continue

                for i, key in enumerate(keys, start=1):
                    pack = GRAMMAR_BANK.get(key)
                    if not pack:
                        self.stderr.write(self.style.ERROR(
                            f"   ❌ Grammar key '{key}' not in bank — skipping."
                        ))
                        skipped_keys += 1
                        continue

                    defaults = {
                        "title_fa": pack.get("title_fa", ""),
                        "level": pack.get("level", "A1"),
                        "structure": pack.get("structure", ""),
                        "explanation": pack.get("explanation", ""),
                        "examples": pack.get("examples", []),
                        "common_mistakes": pack.get("common_mistakes", ""),
                        "usage_tips": pack.get("usage_tips", ""),
                        "order": i,
                    }
                    obj, was_created = GrammarPoint.objects.update_or_create(
                        lesson=lesson,
                        title=pack["title"],
                        defaults=defaults,
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

        total = GrammarPoint.objects.count()
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"✅ Grammar seed done: {created} created, {updated} updated, {skipped_lessons} lessons missing, {skipped_keys} bank keys missing."
        ))
        self.stdout.write(self.style.SUCCESS(f"📚 Total GrammarPoint in DB: {total}"))
