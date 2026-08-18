import json
import random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from Game.services import record_game

from .models import Word

# Used only when the words table has (almost) no rows, so a game never breaks.
FALLBACK_WORDS = [
    {'id': -1, 'english_word': 'apple', 'persian_meaning': 'سیب'},
    {'id': -2, 'english_word': 'book', 'persian_meaning': 'کتاب'},
    {'id': -3, 'english_word': 'car', 'persian_meaning': 'ماشین'},
    {'id': -4, 'english_word': 'dog', 'persian_meaning': 'سگ'},
    {'id': -5, 'english_word': 'cat', 'persian_meaning': 'گربه'},
    {'id': -6, 'english_word': 'house', 'persian_meaning': 'خانه'},
    {'id': -7, 'english_word': 'happy', 'persian_meaning': 'خوشحال'},
    {'id': -8, 'english_word': 'sad', 'persian_meaning': 'ناراحت'},
    {'id': -9, 'english_word': 'big', 'persian_meaning': 'بزرگ'},
    {'id': -10, 'english_word': 'small', 'persian_meaning': 'کوچک'},
]

DIFF_LENGTHS = {'easy': (2, 5), 'medium': (6, 8), 'hard': (9, 99)}
DIFF_MULTIPLIER = {'easy': 1, 'medium': 2, 'hard': 3}
DICTATION_ROUNDS = 12
SPRINT_ITEMS = 40


def _word_dict(word):
    return {'id': word.id, 'english_word': word.english_word, 'persian_meaning': word.persian_meaning}


def _sample_words(count, min_len=2, max_len=99):
    """Random unique words optionally filtered by word-length; never empty."""
    sampled = [
        word for word in Word.objects.order_by('?')[:600]
        if min_len <= len(word.english_word) <= max_len
    ]
    random.shuffle(sampled)
    result = [_word_dict(word) for word in sampled[:count]]

    seen = {item['english_word'] for item in result}
    for fallback in FALLBACK_WORDS:
        if len(result) >= count:
            break
        if fallback['english_word'] in seen:
            continue
        if min_len <= len(fallback['english_word']) <= max_len:
            result.append(dict(fallback))
    return result


def _clamp_int(value, low, high, default):
    try:
        value = int(value)
    except (ValueError, TypeError):
        return default
    return max(low, min(high, value))


def _language_response(res, points_gained):
    """Response shape shared by every language-game save endpoint."""
    return JsonResponse({
        'status': 'success',
        'success': True,
        'xp_gained': res.xp_gained,
        'xp_capped': res.xp_capped,
        'total_xp': res.user.xp,
        'level': res.user.level,
        'points_gained': points_gained,
        'total_points': res.user.points,
    })


def language_home(request):
    total_words = Word.objects.count()
    recent_words = Word.objects.order_by('-id')[:6]
    return render(request, 'languagehome.html', {
        'total_words': total_words,
        'recent_words': recent_words,
    })


# ---------------------------------------------------------------- وصل کن (drag & drop)


def drag_drop_game(request):
    words = _sample_words(5)
    meanings = [{'id': w['id'], 'meaning': w['persian_meaning'], 'correct_word': w['english_word']}
                for w in words]
    random.shuffle(meanings)

    return render(request, 'drag_drop_game.html', {
        'words': words,
        'persian_meanings': meanings,
        'total_words': len(words),
    })


@require_http_methods(["POST"])
def check_match(request):
    try:
        data = json.loads(request.body)
        word_id = data.get('word_id')
        meaning_id = data.get('meaning_id')
        word = Word.objects.get(id=word_id)
        meaning_word = Word.objects.get(id=meaning_id)
        return JsonResponse({'correct': word.english_word == meaning_word.english_word})
    except Exception as e:
        return JsonResponse({'correct': False, 'error': str(e)})


def get_new_words(request):
    words = _sample_words(5)
    meanings = [{'id': w['id'], 'meaning': w['persian_meaning'], 'correct_word': w['english_word']}
                for w in words]
    random.shuffle(meanings)

    return JsonResponse({
        'words': [{'id': w['id'], 'english': w['english_word'], 'persian': w['persian_meaning']}
                  for w in words],
        'meanings': meanings,
        'total': len(words),
    })


@require_http_methods(["POST"])
@login_required
def save_game_score(request):
    try:
        data = json.loads(request.body)
        matched_count = max(0, int(data.get('matched_count', 0) or 0))
        total_words = max(1, int(data.get('total_words', 5) or 5))
        mistakes = max(0, int(data.get('mistakes', 0) or 0))
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    completed = matched_count == total_words
    xp = max(0, matched_count * 10 + (20 if completed else 0) - mistakes * 2)
    points = matched_count * 5

    res = record_game(
        request.user, game_name='language', xp_wanted=xp, completed=completed,
        best_score=int((matched_count / total_words) * 100) if completed else None,
        activity_title='انجام بازی وصل کن',
        activity_desc=f'بازی وصل کن را با {matched_count} اتصال صحیح از {total_words} کلمه کامل کردید',
        activity_icon='language', points_gained=points,
    )
    return _language_response(res, points)


# ---------------------------------------------------------------- حدس کلمه


def word_guessing_game(request):
    words = _sample_words(10)
    return render(request, 'word_guessing.html', {
        'words': words,
        'total_words': len(words),
    })


@require_http_methods(["POST"])
@login_required
def save_guessing_score(request):
    try:
        data = json.loads(request.body)
        score = max(0, int(data.get('score', 0) or 0))
        total_questions = max(1, int(data.get('total_questions', 10) or 10))
        hints_used = max(0, int(data.get('hints_used', 0) or 0))
        time_seconds = max(0, int(data.get('time_seconds', 0) or 0))
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    completed = score == total_questions
    xp = score * 3 + (30 if completed else 0)
    if completed and time_seconds < 60:
        xp += 20
    xp = max(0, xp - hints_used * 2)
    points = score * 4

    res = record_game(
        request.user, game_name='guessing', xp_wanted=xp, completed=completed,
        best_score=int((score / total_questions) * 100) if completed else None,
        activity_title='انجام بازی حدس کلمه',
        activity_desc=f'بازی حدس کلمه را با {score} پاسخ صحیح از {total_questions} سوال کامل کردید',
        activity_icon='guess', points_gained=points,
    )
    return _language_response(res, points)


# ---------------------------------------------------------------- جورچین کلمات


def word_scramble_game(request):
    words = _sample_words(8)
    return render(request, 'word_scramble.html', {
        'words': words,
        'total_words': len(words),
    })


@require_http_methods(["POST"])
@login_required
def save_scramble_score(request):
    try:
        data = json.loads(request.body)
        score = max(0, int(data.get('score', 0) or 0))
        total_questions = max(1, int(data.get('total_questions', 8) or 8))
        time_seconds = max(0, int(data.get('time_seconds', 0) or 0))
        level = data.get('level', 'medium')
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    multiplier = DIFF_MULTIPLIER.get(level, 2)
    completed = score == total_questions
    xp = score * 5 * multiplier + (40 if completed else 0)
    if completed and time_seconds < 90:
        xp += 30
    points = score * 6 * multiplier

    res = record_game(
        request.user, game_name='scramble', xp_wanted=xp, completed=completed,
        best_score=int((score / total_questions) * 100) if completed else None,
        activity_title='انجام بازی جورچین',
        activity_desc=f'بازی جورچین کلمات را با {score} پاسخ صحیح از {total_questions} سوال کامل کردید',
        activity_icon='scramble', points_gained=points,
    )
    return _language_response(res, points)


# ---------------------------------------------------------------- دیکته صوتی (new)


def _dictation_deck(diff):
    min_len, max_len = DIFF_LENGTHS.get(diff, DIFF_LENGTHS['medium'])
    return [{
        'word': w['english_word'],
        'meaning': w['persian_meaning'],
        'letters': len(w['english_word']),
    } for w in _sample_words(DICTATION_ROUNDS, min_len, max_len)]


@login_required
def dictation_game(request):
    diff = request.GET.get('diff', 'medium')
    if diff not in DIFF_LENGTHS:
        diff = 'medium'
    if request.GET.get('deck') == 'json':
        return JsonResponse({'diff': diff, 'rounds': DICTATION_ROUNDS, 'words': _dictation_deck(diff)})
    return render(request, 'word_dictation.html', {'diff': diff})


@require_http_methods(["POST"])
@login_required
def save_dictation_score(request):
    try:
        data = json.loads(request.body)
        diff = data.get('diff', 'medium')
        total = _clamp_int(data.get('total', DICTATION_ROUNDS), 1, 50, DICTATION_ROUNDS)
        score = _clamp_int(data.get('score', 0), 0, total, 0)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    multiplier = DIFF_MULTIPLIER.get(diff, 2)
    xp = score * 6 * multiplier + (25 if score == total else 0)
    points = score * 5 * multiplier

    res = record_game(
        request.user, game_name='dictation', xp_wanted=xp, completed=True,
        best_score=score,
        activity_title='انجام دیکته صوتی',
        activity_desc=f'در دیکته صوتی {score} کلمه از {total} کلمه را درست نوشتید',
        activity_icon='headphones', points_gained=points,
    )
    return _language_response(res, points)


# ---------------------------------------------------------------- دوئل کلمات (new)


def _sprint_deck():
    words = _sample_words(SPRINT_ITEMS)
    deck = []
    other_meanings = [w['persian_meaning'] for w in words]
    for index, word in enumerate(words):
        is_true = index % 2 == 0
        meaning = word['persian_meaning']
        if not is_true:
            candidates = [m for m in other_meanings if m != word['persian_meaning']]
            if candidates:
                meaning = random.choice(candidates)
            else:
                is_true = True
        deck.append({'word': word['english_word'], 'meaning': meaning, 'isTrue': is_true})
    random.shuffle(deck)
    return deck


@login_required
def word_sprint_game(request):
    if request.GET.get('deck') == 'json':
        return JsonResponse({'seconds': 30, 'items': _sprint_deck()})
    return render(request, 'word_sprint.html')


@require_http_methods(["POST"])
@login_required
def save_sprint_score(request):
    try:
        data = json.loads(request.body)
        score = _clamp_int(data.get('score', 0), 0, 500, 0)
        answered = _clamp_int(data.get('answered', 0), 0, 500, 0)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    xp = min(score, 40) * 2 + (15 if score >= 25 else 0)
    points = score

    res = record_game(
        request.user, game_name='sprint', xp_wanted=xp, completed=True,
        best_score=score,
        activity_title='دوئل کلمات',
        activity_desc=f'در دوئل کلمات {score} پاسخ درست از {answered} پرسش دادید',
        activity_icon='swords', points_gained=points,
    )
    return _language_response(res, points)
