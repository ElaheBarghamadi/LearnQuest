"""
One-shot cleanup command: mark every published lesson as NOT a free preview
except the very first lesson of the very first chapter of the very first
published world.

Run this once on any environment where an older seed_data.py flagged every
lesson with is_free_preview=True (which effectively disabled the
progression gate).

    python manage.py fix_free_previews
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from language_academy.models import Lesson, World


class Command(BaseCommand):
    help = "Reset is_free_preview so only the true first lesson is free."

    def handle(self, *args, **opts):
        with transaction.atomic():
            total = Lesson.objects.count()
            Lesson.objects.update(is_free_preview=False)

            first_world = (World.objects
                           .filter(is_published=True)
                           .order_by('order').first())
            marked_id = None
            if first_world:
                first_lesson = (Lesson.objects
                                .filter(chapter__world=first_world,
                                        chapter__order=1,
                                        order=1)
                                .first())
                if first_lesson:
                    first_lesson.is_free_preview = True
                    first_lesson.save(update_fields=['is_free_preview'])
                    marked_id = first_lesson.id

        self.stdout.write(self.style.SUCCESS(
            f"✅ Cleared is_free_preview on {total} lesson(s)."
        ))
        if marked_id:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Marked lesson id={marked_id} as the only free preview."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "⚠  Could not find a W1·C1·L1 to mark as free preview."
            ))
