"""Round 3: quiz full flow, exclusive-lesson gate, AI fallback, misc."""
import sys
import re
import requests

BASE = 'http://127.0.0.1:8000'
fails, passes = [], []


def ok(cond, label, extra=''):
    (passes if cond else fails).append(label)
    print(f'  [{"PASS" if cond else "FAIL"}] {label} {"" if cond else extra[:300]}')


def login(s, username, password):
    s.get(BASE + '/login/')
    csrf = s.cookies.get('csrftoken', '')
    r = s.post(BASE + '/login/', data={
        'csrfmiddlewaretoken': csrf, 'username': username, 'password': password,
    }, headers={'Referer': BASE + '/login/'}, allow_redirects=False, timeout=30)
    return r.status_code in (301, 302, 303)


def post_json(s, url, payload):
    return s.post(BASE + url, json=payload,
                  headers={'X-CSRFToken': s.cookies.get('csrftoken', ''),
                           'X-Requested-With': 'XMLHttpRequest',
                           'Referer': BASE + '/'}, timeout=30)


def as_json(r):
    try:
        return r.json()
    except Exception:
        return None


def main():
    s = requests.Session()
    ok(login(s, 'ali', 'Test@12345'), 'login ali')

    print('=== Exclusive lesson gate ===')
    r = s.get(BASE + '/academy/lesson/3/', allow_redirects=False, timeout=30)
    if r.status_code == 200:
        ok(True, 'lesson gate: ticket already owned (from earlier run)')
    else:
        ok(r.status_code in (301, 302) and '/shop/' in r.headers.get('Location', ''),
           'lesson gate redirects to shop without ticket', f'-> {r.status_code} {r.headers.get("Location")}')
        r = post_json(s, '/shop/buy/59/', {})
        ok(as_json(r) and as_json(r).get('ok'), 'buy exclusive ticket', r.text[:200])
        r = s.get(BASE + '/academy/lesson/3/', timeout=30)
        ok(r.status_code == 200, 'lesson accessible after ticket', f'-> {r.status_code}')

    print('=== Quiz full flow ===')
    r = s.get(BASE + '/academy/quiz/1/', timeout=30)
    m = re.search(r'name="session_key" value="([^"]+)"', r.text)
    ok(bool(m), 'quiz session key found in page', r.text[:150])
    skey = m.group(1) if m else None
    if skey:
        r = post_json(s, '/academy/quiz/save-time/', {'session_key': skey, 'seconds': 15})
        ok(r.status_code == 200, 'quiz save-time', r.text[:150])
        # fetch questions for session
        r = s.get(BASE + '/academy/quiz/1/', timeout=30)
        qids = re.findall(r'data-question-id="(\d+)"', r.text)
        if not qids:
            qids = re.findall(r'question[_-]id[^0-9]*["\']?[:=]\s*["\']?(\d+)', r.text)
        ok(len(qids) > 0, f'quiz question ids found ({len(qids)})', str(qids[:5]))
        # find correct choice ids from the page (data-correct or is_correct attrs)
        corrects = re.findall(r'data-correct="true"[^>]*data-choice-id="(\d+)"', r.text)
        if not corrects:
            corrects = re.findall(r'data-choice-id="(\d+)"[^>]*data-correct="true"', r.text)
        answers = {q: (corrects[i] if i < len(corrects) else '1') for i, q in enumerate(qids)}
        r = post_json(s, '/academy/quiz/save-answer/', {
            'session_key': skey, 'question_id': qids[0], 'choice_id': answers.get(qids[0], '1')})
        ok(r.status_code == 200, 'quiz save-answer', r.text[:150])
        r = s.post(BASE + '/academy/quiz/submit/1/', data={
            'csrfmiddlewaretoken': s.cookies.get('csrftoken', ''), 'session_key': skey},
            headers={'Referer': BASE + '/academy/quiz/1/'}, allow_redirects=False, timeout=30)
        loc = r.headers.get('Location', '')
        ok(r.status_code == 302 and '/result/' in loc, 'quiz submit (form)',
           f'-> {r.status_code} {loc}')
        j = as_json(r)
        if j and j.get('attempt_id'):
            rr = s.get(BASE + f'/academy/quiz/result/{j["attempt_id"]}/', timeout=30)
            ok(rr.status_code == 200, 'quiz result page')

    print('=== AI fallback (no API key) ===')
    r = post_json(s, '/academy/ai/chat/', {'message': 'سلام! چطور شروع کنم؟'})
    j = as_json(r)
    ok(bool(j) and j.get('ok') and j.get('reply'), 'ai chat reply fallback', r.text[:250])
    r = post_json(s, '/academy/ai/challenge/new/', {})
    ok(r.status_code == 200, 'ai challenge new', r.text[:200])
    j = as_json(r)
    if j and j.get('ok') and j.get('challenge_id'):
        r2 = post_json(s, '/academy/ai/challenge/answer/', {'challenge_id': j['challenge_id'], 'answer': 'test'})
        ok(r2.status_code == 200, 'ai challenge answer', r2.text[:200])

    print('=== Writing evaluate with proper fields ===')
    r = post_json(s, '/academy/writing/evaluate/', {
        'prompt': 'Write about your daily routine', 'submission': 'I wake up at 7 am and go to school.'})
    ok(r.status_code == 200, 'writing evaluate ok', r.text[:200])

    print('=== Program app correct URLs ===')
    for u in ['/app/', '/app/calculate/', '/app/calculate-w/', '/app/converter/', '/app/discount/',
              '/app/factorial/', '/app/gcd-lcm-page/', '/app/pythagorean/', '/app/linear-equation/',
              '/app/stats/']:
        rr = s.get(BASE + u, timeout=30)
        ok(rr.status_code == 200, f'programapp {u}', f'-> {rr.status_code}')

    print('=== Misc pages ===')
    for u in ['/blog/?q=airport', '/blog/?cat=test', '/blog/?page=2',
              '/academy/?edit=1', '/academy/world/2/', '/academy/vocabulary/?difficulty=A1',
              '/shop/?sort=cheap', '/shop/?sort=bogus', '/shop/?type=cosmetic',
              '/economy/leaderboard/?type=season', '/games/sudoku/']:
        rr = s.get(BASE + u, timeout=30)
        ok(rr.status_code == 200, f'misc {u}', f'-> {rr.status_code}')

    print()
    print(f'RESULT: {len(passes)} passed, {len(fails)} failed')
    if fails:
        print('FAILED:', fails)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
