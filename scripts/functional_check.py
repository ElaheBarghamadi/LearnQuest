"""Functional smoke tests: exercise POST endpoints and dynamic flows against the live server."""
import sys
import json
import requests

BASE = 'http://127.0.0.1:8000'
fails = []
passes = []


def ok(cond, label, extra=''):
    if cond:
        passes.append(label)
        print(f'  [PASS] {label}')
    else:
        fails.append(label)
        print(f'  [FAIL] {label} {extra}')


def new_session():
    s = requests.Session()
    s.headers.update({'X-Requested-With': 'XMLHttpRequest'})
    return s


def login(s, username, password):
    s.get(BASE + '/login/')
    csrf = s.cookies.get('csrftoken', '')
    r = s.post(BASE + '/login/', data={
        'csrfmiddlewaretoken': csrf, 'username': username, 'password': password,
    }, headers={'Referer': BASE + '/login/'}, allow_redirects=False, timeout=30)
    return r.status_code in (301, 302, 303)


def csrf_of(s):
    return s.cookies.get('csrftoken', '')


def post_json(s, url, payload):
    return s.post(BASE + url, json=payload,
                  headers={'X-CSRFToken': csrf_of(s), 'Referer': BASE + '/'}, timeout=30)


def main():
    print('=== Register + auth flow ===')
    s0 = new_session()
    s0.get(BASE + '/register/')
    r = s0.post(BASE + '/register/', data={
        'csrfmiddlewaretoken': csrf_of(s0),
        'username': 'newwave', 'email': 'newwave@test.com',
        'password1': 'Passw0rd!', 'password2': 'Passw0rd!',
    }, headers={'Referer': BASE + '/register/'}, allow_redirects=False, timeout=30)
    ok(r.status_code in (200, 302), 'register new user', f'-> {r.status_code}')

    # login
    s = new_session()
    ok(login(s, 'ali', 'Test@12345'), 'login ali')

    print('=== Blog ===')
    r = s.post(BASE + '/blog/add-comment/', data={
        'csrfmiddlewaretoken': csrf_of(s), 'content': 'عالی بود این مقاله!', 'article_id': '1',
    }, headers={'Referer': BASE + '/blog/article/1/', 'X-CSRFToken': csrf_of(s)}, timeout=30)
    ok(r.status_code == 200 and r.json().get('success'), 'blog add comment', r.text[:100])
    r = s.post(BASE + '/blog/like/1/', data={'csrfmiddlewaretoken': csrf_of(s)},
               headers={'Referer': BASE + '/blog/article/1/', 'X-CSRFToken': csrf_of(s)}, timeout=30)
    ok(r.status_code == 200 and r.json().get('liked') is True, 'blog like article', r.text[:100])
    r = s.post(BASE + '/blog/like/1/', data={'csrfmiddlewaretoken': csrf_of(s)},
               headers={'Referer': BASE + '/blog/article/1/', 'X-CSRFToken': csrf_of(s)}, timeout=30)
    ok(r.status_code == 200 and r.json().get('liked') is False, 'blog unlike article', r.text[:100])

    print('=== Shop ===')
    st_adm = new_session()
    login(st_adm, 'admin', 'Admin@12345')
    post_json(st_adm, '/panel/users/2/grant/', {'target': 'coins', 'amount': 10000, 'note': 'تاپ آپ'})
    r = s.get(BASE + '/shop/', timeout=30)
    ok(r.status_code == 200, 'shop list')
    # buy once + idempotent replay (rate limit is 12/min — keep under it)
    r = post_json(s, '/shop/buy/1/', {})
    ok(r.status_code == 200 and r.json().get('ok'), 'buy product #1', r.text[:200])
    r = post_json(s, '/shop/buy/1/', {'idem': 'same-idem-test-1'})
    ok(r.status_code == 200 and r.json().get('ok'), 'buy with fixed idem', r.text[:200])
    r = post_json(s, '/shop/buy/1/', {'idem': 'same-idem-test-1'})
    ok(r.status_code == 200 and r.json().get('duplicate'), 'same idem replay -> duplicate (no double charge)', r.text[:200])
    # invalid product (not a real purchase, but hits rate limit counter)
    r = post_json(s, '/shop/buy/999999/', {})
    ok(r.status_code in (400, 402, 404), 'buy invalid product handled', r.text[:200])
    r = s.get(BASE + '/shop/inventory/', timeout=30)
    ok(r.status_code == 200, 'inventory page')
    r = s.get(BASE + '/shop/history/', timeout=30)
    ok(r.status_code == 200, 'history page')
    r = post_json(s, '/shop/wishlist/toggle/1/', {})
    ok(r.status_code == 200, 'wishlist toggle', r.text[:200])

    print('=== Games (score saves) ===')
    def game_ok(r):
        j = None
        try:
            j = r.json()
        except Exception:
            pass
        return r.status_code == 200 and j and (j.get('success') or j.get('status') == 'success')

    for url, payload in [
        ('/games/save-sudoku-score/', {'score': 120, 'completed': True, 'time': 180}),
        ('/games/save-memory-score/', {'moves': 18, 'time': 40, 'completed': True}),
        ('/games/save-puzzle-score/', {'moves': 25, 'time': 90, 'completed': True}),
        ('/games/save-iq-score/', {'score': 80, 'correct': 8, 'total': 10}),
        ('/games/save-snake-score/', {'score': 50, 'completed': True}),
        ('/games/save-2048-score/', {'score': 1024, 'completed': True}),
        ('/games/save-reaction-score/', {'best_ms': 320, 'completed': True}),
        ('/games/save-simon-score/', {'score': 6, 'completed': True}),
        ('/games/save-whack-score/', {'score': 30, 'completed': True}),
        ('/games/save-tictactoe-score/', {'score': 1, 'result': 'win'}),
        ('/games/save-minesweeper-score/', {'score': 100, 'completed': True, 'time': 120}),
        ('/games/save-breakout-score/', {'score': 500, 'completed': True}),
    ]:
        r = post_json(s, url, payload)
        ok(game_ok(r), f'game {url}', r.text[:150])

    print('=== Language games ===')
    for url, payload in [
        ('/language/save-game-score/', {'matched_count': 5, 'total_words': 5, 'mistakes': 1}),
        ('/language/save-guessing-score/', {'score': 9, 'total_questions': 10, 'hints_used': 1, 'time_seconds': 50}),
        ('/language/save-scramble-score/', {'score': 8, 'total_questions': 8, 'time_seconds': 70, 'level': 'hard'}),
        ('/language/save-dictation-score/', {'diff': 'medium', 'total': 12, 'score': 9}),
        ('/language/save-sprint-score/', {'score': 22, 'answered': 30}),
    ]:
        r = post_json(s, url, payload)
        ok(r.status_code == 200 and r.json().get('success'), f'lang {url}', r.text[:150])
    r = s.get(BASE + '/language/word-sprint/?deck=json', timeout=30)
    ok(r.status_code == 200, 'sprint deck json')
    r = s.get(BASE + '/language/dictation/?deck=json&diff=hard', timeout=30)
    ok(r.status_code == 200, 'dictation deck json')

    print('=== Academy: quiz flow ===')
    r = s.get(BASE + '/academy/quiz/51/', timeout=30)
    ok(r.status_code == 200, 'quiz page', str(r.status_code))
    r = s.get(BASE + '/academy/lesson/51/', timeout=30)
    ok(r.status_code == 200, 'lesson page')
    r = post_json(s, '/academy/api/update-progress/51/', {'progress': 50})
    ok(r.status_code in (200, 400), 'update progress', r.text[:150])

    print('=== Academy: vocabulary actions ===')
    r = post_json(s, '/academy/vocabulary/mark-learned/487/', {})
    ok(r.status_code == 200, 'vocab mark learned', r.text[:150])
    r = post_json(s, '/academy/vocabulary/flashcard-action/', {'word_id': 487, 'action': 'known'})
    ok(r.status_code == 200, 'flashcard action', r.text[:150])
    r = post_json(s, '/academy/vocabulary/spaced-repetition-action/', {'word_id': 487, 'quality': 4})
    ok(r.status_code == 200, 'spaced repetition action', r.text[:150])
    r = post_json(s, '/academy/vocabulary/matching-result/', {'word_id': 487, 'is_correct': True})
    ok(r.status_code == 200, 'matching result', r.text[:150])
    r = post_json(s, '/academy/vocabulary/add-to-practice/487/', {})
    ok(r.status_code == 200, 'add to practice', r.text[:150])

    print('=== Idioms ===')
    r = s.get(BASE + '/academy/idioms/placement/', timeout=30)
    ok(r.status_code == 200, 'idioms placement page')
    r = post_json(s, '/academy/idioms/mark/', {'idiom_id': 1})
    ok(r.status_code == 200, 'idiom mark learned', r.text[:150])

    print('=== Messenger ===')
    r = s.get(BASE + '/messenger/conversation/1/', timeout=30)
    ok(r.status_code == 200 and r.json().get('success'), 'open DM with admin', r.text[:150])
    r = post_json(s, '/messenger/send/', {'conversation_id': r.json()['conversation']['id'], 'content': 'سلام!'})
    ok(r.status_code == 201 and r.json().get('success'), 'send DM', r.text[:200])
    conv_id = r.json()['message']['id'] if r.status_code == 201 else None
    r = post_json(s, '/messenger/create-group/', {'name': 'گروه تست', 'participant_ids': [1]})
    ok(r.status_code == 201 and r.json().get('success'), 'create group', r.text[:200])
    group_id = r.json()['conversation']['id'] if r.status_code == 201 else None
    r = post_json(s, '/messenger/send/', {'conversation_id': group_id, 'content': 'پیام گروهی'})
    ok(r.status_code == 201, 'send group msg', r.text[:200])
    r = post_json(s, '/messenger/block/1/', {})
    ok(r.status_code == 200, 'block admin', r.text[:150])
    r = post_json(s, '/messenger/unblock/1/', {})
    ok(r.status_code == 200, 'unblock admin', r.text[:150])

    print('=== Economy ===')
    r = post_json(s, '/economy/use-hint/', {'session_key': 'nonexistent-session-123'})
    ok(r.status_code in (404, 400, 402), 'use hint (missing session -> handled)', f'-> {r.status_code}')
    r = post_json(s, '/economy/use-time-card/', {'session_key': 'nonexistent-session-123'})
    ok(r.status_code in (404, 400, 402), 'use time card (missing session -> handled)', f'-> {r.status_code}')
    r = s.get(BASE + '/economy/retry-status/1/', timeout=30)
    ok(r.status_code == 200, 'retry status')
    r = s.get(BASE + '/economy/leaderboard/?type=weekly', timeout=30)
    ok(r.status_code == 200, 'leaderboard weekly')
    r = s.get(BASE + '/economy/leaderboard/?type=bogus', timeout=30)
    ok(r.status_code == 200, 'leaderboard bogus type fallback')

    print('=== Public profile + API ===')
    r = s.get(BASE + '/u/admin/', timeout=30)
    ok(r.status_code == 200, 'public profile admin')
    r = s.get(BASE + '/api/profile/admin/', timeout=30)
    ok(r.status_code == 200 and r.json().get('success'), 'profile card api', r.text[:200])

    print('=== Contact form ===')
    sc = new_session()
    sc.get(BASE + '/contact_us/')
    r = sc.post(BASE + '/contact_us/', data={
        'csrfmiddlewaretoken': csrf_of(sc), 'name': 'کاربر تست', 'email': 't@t.com',
        'phone_number': '09120000000', 'message': 'سلام، پیام تستی',
    }, headers={'Referer': BASE + '/contact_us/'}, allow_redirects=False, timeout=30)
    ok(r.status_code in (200, 302), 'contact form submit', f'-> {r.status_code}')

    print('=== Staff panel actions ===')
    st = new_session()
    ok(login(st, 'admin', 'Admin@12345'), 'login admin')
    r = post_json(st, '/panel/users/2/grant/', {'target': 'coins', 'amount': 100, 'note': 'تست'})
    ok(r.status_code == 200 and r.json().get('ok'), 'panel grant coins', r.text[:200])
    r0 = post_json(st, '/panel/users/2/grant/', {'target': 'coins', 'amount': 100, 'note': 'تست', 'idem': 'same-key-1'})
    ok(r0.status_code == 200 and r0.json().get('ok'), 'panel grant with idem', r0.text[:200])
    r = post_json(st, '/panel/users/2/grant/', {'target': 'coins', 'amount': 100, 'note': 'تست', 'idem': 'same-key-1'})
    ok(r.status_code == 200 and r.json().get('duplicate'), 'panel grant idempotent', r.text[:200])
    r = post_json(st, '/panel/users/2/toggle-active/', {})
    ok(r.status_code == 200, 'panel toggle active', r.text[:200])
    r = post_json(st, '/panel/users/2/toggle-active/', {})
    ok(r.status_code == 200, 'panel toggle active back', r.text[:200])
    r = post_json(st, '/panel/users/2/item/', {'product_id': 2})
    ok(r.status_code == 200 and r.json().get('ok'), 'panel grant item', r.text[:200])

    print('=== Academy CMS (staff) ===')
    r = post_json(st, '/academy/manage/worlds/7/toggle-publish/', {})
    ok(r.status_code == 200, 'cms toggle world publish', r.text[:200])
    r = post_json(st, '/academy/manage/worlds/7/toggle-publish/', {})
    ok(r.status_code == 200, 'cms toggle world publish back', r.text[:200])
    r = post_json(st, '/academy/manage/worlds/7/move/down/', {})
    ok(r.status_code in (200, 400), 'cms move world', r.text[:200])
    r = post_json(st, '/academy/manage/shop/products/1/toggle/', {})
    ok(r.status_code == 200, 'cms toggle product', r.text[:200])
    r = post_json(st, '/academy/manage/shop/products/1/toggle/', {})
    ok(r.status_code == 200, 'cms toggle product back', r.text[:200])
    r = post_json(st, '/academy/manage/blog/categories/quick-create/', {'name': 'دسته تست', 'slug': 'test-cat-1'})
    ok(r.status_code == 200, 'cms quick create category', r.text[:200])

    print('=== Admin site ===')
    r = st.get(BASE + '/admin/', timeout=30)
    ok(r.status_code == 200, 'admin index')

    print()
    print(f'RESULT: {len(passes)} passed, {len(fails)} failed')
    if fails:
        print('FAILED:', fails)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
