import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services import (
    check_and_create_achievement,
    grant_game_xp as _grant_game_xp,
    level_up_activity as _level_up_activity,
    record_game,
)

LEGACY_OK = {'status': 'success', 'success': True}


def _bad_payload():
    return JsonResponse({'status': 'error', 'success': False, 'message': 'داده نامعتبر است'}, status=400)


def _json_body(request):
    """Parse the request body; returns None when it is not valid JSON."""
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def _legacy_response(res):
    """Response shape used by the four original board games."""
    return JsonResponse({
        **LEGACY_OK,
        'xp_gained': res.xp_gained,
        'xp_capped': res.xp_capped,
        'total_xp': res.user.xp,
        'new_level': res.user.level,
        'achievements_earned': res.achievements,
        'games_completed': res.stats.games_completed,
    })


def _record_score(user, game_name, score, completed, activity_title, activity_desc,
                  xp_base=20, max_xp_bonus=40, lower_is_better=False):
    """Shared handler for the canvas/arcade family (higher/lower-is-better score)."""
    score = max(0, int(score or 0))
    xp_wanted = 0
    if completed:
        bonus = 10 if lower_is_better else score // 50
        xp_wanted = min(xp_base + max(0, bonus), xp_base + max_xp_bonus)

    res = record_game(
        user, game_name=game_name, xp_wanted=xp_wanted, completed=completed,
        best_score=score, lower_is_better=lower_is_better,
        activity_title=activity_title, activity_desc=activity_desc,
    )
    return JsonResponse({
        'status': 'success',
        'best_score': res.stats.best_score,
        'new_best': res.new_best,
        'xp_gained': res.xp_gained,
        'xp_capped': res.xp_capped,
        'total_xp': res.user.xp,
        'level': res.user.level,
        'games_played': res.stats.games_played,
        'achievements': res.achievements,
    })


# ---------------------------------------------------------------- memory


@login_required
def memory_game(request):
    return render(request, 'memory.html')


@login_required
@require_http_methods(["POST"])
def save_memory_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        moves = max(0, int(data.get('moves', 0) or 0))
        time_seconds = max(0, int(data.get('time', 0) or 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    xp = 30
    if moves < 20:
        xp += (20 - moves) // 2
    if time_seconds < 60:
        xp += (60 - time_seconds) // 5

    res = record_game(
        request.user, game_name='memory', xp_wanted=xp, completed=completed,
        best_score=max(0, 1000 - moves - time_seconds // 2),
        activity_title='انجام بازی حافظه',
        activity_desc=f'بازی حافظه را با {moves} حرکت و {time_seconds} ثانیه کامل کردید',
        activity_icon='memory',
    )
    return _legacy_response(res)


# ---------------------------------------------------------------- number puzzle


@login_required
def number_puzzle(request):
    return render(request, 'number_puzzle.html')


@login_required
@require_http_methods(["POST"])
def save_puzzle_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        moves = max(0, int(data.get('moves', 0) or 0))
        time_seconds = max(0, int(data.get('time', 0) or 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    xp = 40
    if moves < 100:
        xp += (100 - moves) // 5
    if time_seconds < 120:
        xp += (120 - time_seconds) // 10

    res = record_game(
        request.user, game_name='puzzle', xp_wanted=xp, completed=completed,
        best_score=max(0, 1000 - moves - time_seconds // 3),
        activity_title='انجام بازی پازل عددی',
        activity_desc=f'پازل عددی را با {moves} حرکت و {time_seconds} ثانیه کامل کردید',
        activity_icon='puzzle',
    )
    return _legacy_response(res)


# ---------------------------------------------------------------- sudoku


@login_required
def sudoku_view(request):
    return render(request, 'sudoku.html')


@login_required
@require_http_methods(["POST"])
def save_sudoku_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        time_seconds = max(0, int(data.get('time', 0) or 0))
        hints_used = max(0, int(data.get('hints_used', 0) or 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    xp = 35
    if time_seconds < 300:
        xp += 25
    elif time_seconds < 600:
        xp += 15
    xp = max(10, xp - hints_used * 2)

    res = record_game(
        request.user, game_name='sudoku', xp_wanted=xp, completed=completed,
        best_score=max(0, 1000 - time_seconds // 2 - hints_used * 50),
        activity_title='انجام بازی سودوکو',
        activity_desc=f'سودوکو را در {time_seconds} ثانیه با {hints_used} راهنما کامل کردید',
        activity_icon='sudoku',
    )
    return _legacy_response(res)


# ---------------------------------------------------------------- iq test


@login_required
def iq_test(request):
    return render(request, 'iq_test.html')


@login_required
@require_http_methods(["POST"])
def save_iq_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        score = max(0, int(data.get('score', 0) or 0))
        total = max(1, int(data.get('total', 10) or 10))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    percent = (score / total) * 100
    xp = 30
    if percent >= 80:
        xp += 30
    elif percent >= 60:
        xp += 20
    elif percent >= 40:
        xp += 10

    res = record_game(
        request.user, game_name='iq_test', xp_wanted=xp, completed=completed,
        best_score=int(percent),
        activity_title='انجام تست هوش',
        activity_desc=f'تست هوش را با {score} پاسخ صحیح از {total} سوال کامل کردید',
        activity_icon='brain',
    )
    return _legacy_response(res)


# ---------------------------------------------------------------- snake


@login_required
def snake_game(request):
    return render(request, 'snake.html')


@login_required
@require_http_methods(["POST"])
def save_snake_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        score = int(data.get('score', 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    return _record_score(
        request.user, 'snake', score, completed,
        activity_title='انجام بازی مار',
        activity_desc=f'مار را با امتیاز {score} بازی کردید',
        xp_base=20, max_xp_bonus=40,
    )


# ---------------------------------------------------------------- 2048


@login_required
def game_2048(request):
    return render(request, 'game_2048.html')


@login_required
@require_http_methods(["POST"])
def save_2048_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        score = int(data.get('score', 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    return _record_score(
        request.user, '2048', score, completed,
        activity_title='انجام بازی ۲۰۴۸',
        activity_desc=f'بازی ۲۰۴۸ را با امتیاز {score} بازی کردید',
        xp_base=25, max_xp_bonus=60,
    )


# ---------------------------------------------------------------- reaction


@login_required
def reaction_game(request):
    return render(request, 'reaction.html')


@login_required
@require_http_methods(["POST"])
def save_reaction_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        best_ms = int(data.get('best_ms', 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    if best_ms <= 0:
        return JsonResponse({'status': 'error', 'message': 'زمان نامعتبر است'}, status=400)

    return _record_score(
        request.user, 'reaction', best_ms, completed,
        activity_title='تست سرعت واکنش',
        activity_desc=f'بهترین واکنش شما {best_ms} میلی‌ثانیه بود',
        xp_base=15, max_xp_bonus=25, lower_is_better=True,
    )


# ---------------------------------------------------------------- simon


@login_required
def simon_game(request):
    return render(request, 'simon.html')


@login_required
@require_http_methods(["POST"])
def save_simon_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        score = int(data.get('score', 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    return _record_score(
        request.user, 'simon', score, completed,
        activity_title='انجام حافظه رنگی',
        activity_desc=f'تا مرحله {score} در بازی حافظه رنگی پیش رفتید',
        xp_base=20, max_xp_bonus=50,
    )


# ---------------------------------------------------------------- whack-a-mole


@login_required
def whack_game(request):
    return render(request, 'whack.html')


@login_required
@require_http_methods(["POST"])
def save_whack_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        score = int(data.get('score', 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    return _record_score(
        request.user, 'whack', score, completed,
        activity_title='انجام بازی ضربه به موش',
        activity_desc=f'توانستید {score} ضربه موفق در بازی موش بزنید',
        xp_base=15, max_xp_bonus=40,
    )


# ---------------------------------------------------------------- tic-tac-toe


@login_required
def tictactoe_game(request):
    return render(request, 'tictactoe.html')


@login_required
@require_http_methods(["POST"])
def save_tictactoe_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        streak = int(data.get('score', 0))
        completed = bool(data.get('completed', True))
    except (ValueError, TypeError):
        return _bad_payload()

    return _record_score(
        request.user, 'tictactoe', streak, completed,
        activity_title='انجام دوز باهوش',
        activity_desc=f'{streak} برد پیاپی در دوز مقابل هوش مصنوعی',
        xp_base=10, max_xp_bonus=30,
    )


# ---------------------------------------------------------------- minesweeper (new)


@login_required
def minesweeper_game(request):
    return render(request, 'minesweeper.html')


@login_required
@require_http_methods(["POST"])
def save_minesweeper_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        time_seconds = max(0, int(data.get('time', 0) or 0))
    except (ValueError, TypeError):
        return _bad_payload()
    won = bool(data.get('won', False))

    xp = 0
    if won:
        xp = min(60, 30 + max(0, (180 - time_seconds) // 6))

    res = record_game(
        request.user, game_name='minesweeper', xp_wanted=xp, completed=won,
        best_score=time_seconds if won else None, lower_is_better=True,
        activity_title='پاک‌سازی میدان مین',
        activity_desc=f'میدان مین را در {time_seconds} ثانیه پاک کردید' if won else None,
        activity_icon='bomb',
    )
    return JsonResponse({
        'status': 'success',
        'best_score': res.stats.best_score,
        'new_best': res.new_best,
        'xp_gained': res.xp_gained,
        'xp_capped': res.xp_capped,
        'total_xp': res.user.xp,
        'level': res.user.level,
        'games_played': res.stats.games_played,
        'games_completed': res.stats.games_completed,
        'achievements': res.achievements,
    })


# ---------------------------------------------------------------- breakout (new)


@login_required
def breakout_game(request):
    return render(request, 'breakout.html')


@login_required
@require_http_methods(["POST"])
def save_breakout_score(request):
    data = _json_body(request)
    if data is None:
        return _bad_payload()
    try:
        score = max(0, int(data.get('score', 0) or 0))
    except (ValueError, TypeError):
        return _bad_payload()
    completed = bool(data.get('completed', True))

    return _record_score(
        request.user, 'breakout', score, completed,
        activity_title='انجام بازی آجرشکن',
        activity_desc=f'در آجرشکن {score} امتیاز گرفتید',
        xp_base=15, max_xp_bonus=60,
    )
