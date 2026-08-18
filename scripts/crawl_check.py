"""Smoke-test every URL of the project against the running dev server."""
import sys
import re
import requests

BASE = 'http://127.0.0.1:8000'

ANON_URLS = [
    '/', '/blog/', '/blog/article/1/', '/language/', '/academy/', '/academy/world/1/',
    '/academy/chapter/1/', '/academy/vocabulary/', '/academy/idioms/',
    '/academy/vocabulary/flashcards/', '/academy/vocabulary/matching/',
    '/academy/certificate/verify/', '/contact_us/', '/games/sudoku/',
    '/games/memory/', '/games/number-puzzle/', '/games/iq-test/', '/games/snake/',
    '/games/2048/', '/games/reaction/', '/games/simon/', '/games/whack/',
    '/games/tictactoe/', '/games/minesweeper/', '/games/breakout/',
    '/language/drag-drop/', '/language/word-guessing/', '/language/word-scramble/',
    '/language/dictation/', '/language/word-sprint/',
    '/register/', '/login/', '/password-reset/', '/admin/login/',
    '/home/', '/home/games/', '/home/guide/', '/home/profile/', '/home/edit-profile/',
    '/economy/wallet/', '/economy/leaderboard/', '/economy/season/', '/economy/pet/',
    '/shop/', '/messenger/', '/panel/', '/academy/manage/', '/academy/dashboard/',
]

AUTH_URLS = [
    '/home/', '/home/games/', '/home/profile/', '/home/edit-profile/',
    '/economy/wallet/', '/economy/leaderboard/', '/economy/season/', '/economy/pet/',
    '/shop/', '/shop/product/frame-gold/', '/shop/inventory/', '/shop/history/',
    '/shop/wishlist/', '/messenger/', '/messenger/conversations/',
    '/messenger/blocked/', '/messenger/search/?q=ad',
    '/academy/dashboard/', '/academy/chapter/1/', '/academy/lesson/1/',
    '/academy/quiz/1/', '/academy/exam/1/', '/academy/writing/',
    '/academy/vocabulary/hub/', '/academy/vocabulary/flashcards/',
    '/academy/vocabulary/stats/', '/academy/vocabulary/review/',
    '/academy/vocabulary/spaced-repetition/', '/academy/vocabulary/sentence-builder/',
    '/academy/idioms/', '/academy/idioms/learn/', '/academy/idioms/flashcards/',
    '/academy/certificates/', '/academy/dialogue/1/',
    '/panel/', '/panel/users/', '/panel/users/2/',
    '/academy/manage/', '/academy/manage/worlds/', '/academy/manage/worlds/1/edit/',
    '/academy/manage/vocabulary/', '/academy/manage/quizzes/', '/academy/manage/exams/',
    '/academy/manage/users/', '/academy/manage/analytics/', '/academy/manage/settings/',
    '/academy/manage/shop/products/', '/academy/manage/blog/articles/',
    '/academy/manage/certificates/', '/academy/manage/badges/',
]

REDIRECT_OK = {301, 302, 303, 307, 308}


def check(url, session, label):
    try:
        r = session.get(BASE + url, allow_redirects=False, timeout=30)
    except Exception as e:
        print(f'  [ERR] {label} {url} -> {e}')
        return False
    ok = r.status_code == 200 or r.status_code in REDIRECT_OK
    status = 'OK' if ok else f'FAIL({r.status_code})'
    print(f'  [{status:11}] {label} {url}')
    return ok


def main():
    fails = 0

    s_anon = requests.Session()
    print(f'=== Anonymous ({len(ANON_URLS)} URLs) ===')
    for u in ANON_URLS:
        if not check(u, s_anon, 'anon'):
            fails += 1

    # login as normal user
    s = requests.Session()
    s.get(BASE + '/login/')
    csrf = s.cookies.get('csrftoken', '')
    r = s.post(BASE + '/login/', data={
        'csrfmiddlewaretoken': csrf,
        'username': 'ali', 'password': 'Test@12345',
    }, headers={'Referer': BASE + '/login/'}, allow_redirects=False, timeout=30)
    if r.status_code not in REDIRECT_OK:
        print(f'  [FAIL] login -> {r.status_code}')
        fails += 1
    else:
        print('  [OK] login as ali')

    print(f'=== Authenticated ({len(AUTH_URLS)} URLs) ===')
    for u in AUTH_URLS:
        if not check(u, s, 'auth'):
            fails += 1

    # admin panel pages (ali is not staff, so these should redirect — just check no 500)
    print('=== Panel access as non-staff (expect redirects, no 500) ===')
    for u in ['/panel/', '/panel/users/', '/panel/users/2/',
              '/academy/manage/', '/academy/manage/worlds/', '/academy/manage/analytics/']:
        if not check(u, s, 'nonstaff'):
            fails += 1

    # staff user
    s_staff = requests.Session()
    s_staff.get(BASE + '/login/')
    csrf = s_staff.cookies.get('csrftoken', '')
    s_staff.post(BASE + '/login/', data={
        'csrfmiddlewaretoken': csrf,
        'username': 'admin', 'password': 'Admin@12345',
    }, headers={'Referer': BASE + '/login/'}, allow_redirects=False, timeout=30)
    print('=== Staff pages ===')
    for u in ['/panel/', '/panel/users/', '/panel/users/1/', '/panel/users/2/',
              '/academy/manage/', '/academy/manage/worlds/', '/academy/manage/worlds/1/edit/',
              '/academy/manage/chapters/1/edit/', '/academy/manage/lessons/1/edit/',
              '/academy/manage/vocabulary/', '/academy/manage/vocabulary/categories/',
              '/academy/manage/quizzes/', '/academy/manage/quizzes/1/questions/',
              '/academy/manage/exams/', '/academy/manage/exams/1/questions/',
              '/academy/manage/users/', '/academy/manage/users/2/progress/',
              '/academy/manage/analytics/', '/academy/manage/settings/',
              '/academy/manage/shop/products/', '/academy/manage/blog/articles/',
              '/academy/manage/certificates/', '/academy/manage/badges/',
              '/admin/', '/admin/user/customuser/']:
        if not check(u, s_staff, 'staff'):
            fails += 1

    print()
    print(f'RESULT: {"ALL OK ✔" if fails == 0 else f"{fails} FAILURES ✘"}')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
