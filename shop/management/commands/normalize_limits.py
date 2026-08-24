"""
Set per_user_limit=1 on every product that is naturally one-per-user:
cosmetics (frames, themes, badges, colors, titles, backgrounds, effects,
accessories, wallpaper packs, pet accessories/skins) and unlock packs
(pets, season pass, exclusive lessons/minigames, vocab/grammar/…-packs).

Consumables (retry ticket, hint ticket, mystery box, lucky spin, hearts,
time cards) and boosters and bundles stay repeatable.

Idempotent — safe to re-run.

    python manage.py normalize_limits
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Product


# effect_types that MUST be one-per-user
ONE_TIME_EFFECTS = {
    # cosmetics
    'frame', 'frame_animated',
    'theme', 'theme_dark_variant',
    'username_color',
    'badge', 'title',
    'profile_background',
    'profile_effect', 'profile_card_animated',
    'pet_skin', 'pet_accessory',
    'wallpaper_pack',
    # unlocks (content or feature)
    'pet',
    'season_pass',
    'exclusive_lesson', 'exclusive_minigame',
    'vocabulary_pack', 'grammar_pack', 'listening_pack', 'speaking_pack',
    'writing_pack', 'pronunciation_pack', 'music_pack',
    'sticker_pack', 'emoji_pack',
    'certificate_special',
}

# effect_types that should stay REPEATABLE (per_user_limit stays 0)
REPEATABLE_EFFECTS = {
    'xp_booster', 'coin_booster', 'gem_booster',
    'retry_ticket', 'hint_ticket', 'time_extension',
    'extra_hearts',
    'mystery_box', 'lucky_spin',
    'bundle',
}


class Command(BaseCommand):
    help = "Set per_user_limit=1 on cosmetic/unlock products; keep consumables repeatable."

    def handle(self, *args, **opts):
        n_locked = 0
        n_kept = 0
        n_skipped = 0

        with transaction.atomic():
            for p in Product.objects.all():
                if p.effect_type in ONE_TIME_EFFECTS:
                    if p.per_user_limit != 1:
                        p.per_user_limit = 1
                        p.save(update_fields=['per_user_limit'])
                        n_locked += 1
                    else:
                        n_kept += 1
                elif p.effect_type in REPEATABLE_EFFECTS:
                    if p.per_user_limit != 0:
                        p.per_user_limit = 0
                        p.save(update_fields=['per_user_limit'])
                        n_locked += 1
                    else:
                        n_kept += 1
                else:
                    n_skipped += 1
                    self.stdout.write(self.style.WARNING(
                        f"  ? Unknown effect_type '{p.effect_type}' on '{p.name}' — left as-is (limit={p.per_user_limit})"
                    ))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"✅ Normalized: {n_locked} product(s) updated, {n_kept} already correct, {n_skipped} unknown."
        ))

        # summary
        one_time = Product.objects.filter(per_user_limit=1).count()
        repeat   = Product.objects.filter(per_user_limit=0).count()
        self.stdout.write(f"   one-per-user: {one_time}")
        self.stdout.write(f"   repeatable:   {repeat}")
