"""
Shared reward/stats engine for every game (Game + language apps).

All save-score endpoints funnel through `record_game` so that:
  * stats increments, best-score, XP grant and points are atomic
    (select_for_update on the user row -> no lost updates),
  * the 10x achievements are defined in ONE map,
  * response shaping stays with the thin views.
"""
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.db import transaction

from economy.services import grant_xp as _eco_grant_xp
from user.models import UserActivity

from .models import UserAchievement, UserGameStats


def grant_game_xp(user, xp_amount, game_name, source_id=None):
    """Route game XP through the economy ledger (daily cap aware)."""
    if xp_amount <= 0:
        return 0, False
    result = _eco_grant_xp(
        user, xp_amount,
        source=f'game:{game_name}', source_id=source_id, rule_code='game_play',
    )
    return result.get('granted', 0), bool(result.get('capped'))


def level_up_activity(user, old_level):
    if old_level != user.level:
        UserActivity.objects.create(
            user=user,
            title=f'رسیدن به سطح {user.level}',
            description=f'شما به سطح {user.level} در بازی رسیدید',
            icon='level-up',
        )


ACHIEVEMENT_10 = {
    'memory':      ('memory_10', 'استاد حافظه', '۱۰ بازی حافظه را با موفقیت کامل کردی!', 'brain'),
    'puzzle':      ('puzzle_10', 'استاد پازل', '۱۰ بازی پازل عددی را کامل کردی!', 'puzzle-piece'),
    'sudoku':      ('sudoku_10', 'استاد سودوکو', '۱۰ بازی سودوکو را کامل کردی!', 'th'),
    'iq_test':     ('iq_10', 'نابغه هوش', '۱۰ تست هوش را کامل کردی!', 'brain'),
    'language':    ('language_10', 'استاد زبان', '۱۰ بازی وصل کن را با موفقیت کامل کردی!', 'star'),
    'guessing':    ('guessing_10', 'نابغه کلمات', '۱۰ بازی حدس کلمه را با موفقیت کامل کردی!', 'star'),
    'scramble':    ('scramble_10', 'استاد جورچین', '۱۰ بازی جورچین کلمات را با موفقیت کامل کردی!', 'star'),
    'dictation':   ('dictation_10', 'گوش طلایی', '۱۰ بازی دیکته صوتی را کامل کردی!', 'star'),
    'sprint':      ('sprint_10', 'برق کلمات', 'در ۱۰ دوئل کلمات شرکت کردی!', 'star'),
    'minesweeper': ('minesweeper_10', 'مین‌روب حرفه‌ای', '۱۰ میدان مین را با موفقیت پاک کردی!', 'star'),
    'breakout':    ('breakout_10', 'شکنندهٔ آجرها', '۱۰ بازی آجرشکن را کامل کردی!', 'star'),
}


def check_and_create_achievement(user, game_name, completed_count):
    """Award the '<game>_10' achievement once the player finishes 10 runs."""
    earned = []
    if completed_count >= 10 and game_name in ACHIEVEMENT_10:
        ach_type, name, desc, icon = ACHIEVEMENT_10[game_name]
        _, created = UserAchievement.objects.get_or_create(
            user=user, achievement_type=ach_type,
            defaults={'name': name, 'description': desc, 'icon': icon},
        )
        if created:
            earned.append(name)
            UserActivity.objects.create(
                user=user,
                title=f'دریافت دستاورد: {name}',
                description=desc,
                icon='trophy',
            )
    return earned


def record_game(user, *, game_name, xp_wanted=0, completed=True, best_score=None,
                lower_is_better=False, activity_title=None, activity_desc=None,
                activity_icon='gamepad', points_gained=0):
    """
    One atomic unit of "a game finished":
      1. lock the user row,
      2. bump stats / best score,
      3. log the activity,
      4. grant XP via the economy ledger,
      5. add legacy points (language games),
      6. check the 10x achievement.
    Returns a namespace with everything the views need for their JSON payloads.
    """
    with transaction.atomic():
        user = get_user_model().objects.select_for_update().get(pk=user.pk)

        stats, _ = UserGameStats.objects.get_or_create(user=user, game_name=game_name)
        stats.games_played += 1
        new_best = False
        if completed:
            stats.games_completed += 1
            if best_score is not None:
                score_value = int(best_score)
                if lower_is_better:
                    if score_value > 0 and (stats.best_score == 0 or score_value < stats.best_score):
                        stats.best_score = score_value
                        new_best = True
                elif score_value > stats.best_score:
                    stats.best_score = score_value
                    new_best = True
            if activity_title:
                UserActivity.objects.create(
                    user=user,
                    title=activity_title,
                    description=activity_desc or '',
                    icon=activity_icon,
                )
        stats.save(update_fields=['games_played', 'games_completed', 'best_score', 'updated_at'])

        old_level = user.level
        xp_gained, xp_capped = grant_game_xp(user, int(max(0, xp_wanted)), game_name)
        user.refresh_from_db(fields=['xp', 'level', 'points'])
        level_up_activity(user, old_level)

        if points_gained > 0:
            user.points = (user.points or 0) + int(points_gained)
            user.save(update_fields=['points'])

        achievements = check_and_create_achievement(user, game_name, stats.games_completed)

    return SimpleNamespace(
        user=user, stats=stats,
        xp_gained=xp_gained, xp_capped=xp_capped,
        new_best=new_best, achievements=achievements,
    )
