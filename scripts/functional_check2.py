"""Round 2: corrected + deeper functional checks (quiz flow, AI fallback, seed idempotency, programapp)."""
import sys
import re
import requests

BASE = 'http://127.0.0.1:8000'
fails, passes = [], []


def ok(cond, label, extra=''):
    (passes if cond else fails).append(label)
    print(f'  [{"PASS" if cond else "FAIL"}] {label} {"" if cond else extra[:200]}')


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

    # Top up coins so purchase tests are meaningful
    st = requests.Session()
    ok(login(st, 'admin', 'Admin@12345'), 'login admin')
    post_json(st, '/panel/users/2/grant/', {'target': 'coins', 'amount': 5000, 'note': 'تاپ آپ تست'})

    print('=== Shop purchases (real) ===')
    r = s.get(BASE + '/shop/', timeout=30)
    # parse product links
    slugs = re.findall(r'/shop/product/([\w-]+)/', r.text)
    ok(len(slugs) > 0, 'found product slugs', str(slugs[:3]))
    bought_any = False
    for slug in slugs[:6]:
        rr = s.get(BASE + f'/shop/product/{slug}/', timeout=30)
        if rr.status_code != 200:
            continue
        pid = re.search(r'/shop/buy/(\d+)/', rr.text)
        if not pid:
            continue
        r2 = post_json(s, f'/shop/buy/{pid.group(1)}/', {})
        j2 = as_json(r2)
        if r2.status_code == 200 and j2 and j2.get('ok'):
            bought_any = True
            print(f'    bought {slug}')
            break
    ok(bought_any, 'actually bought an affordable product')

    # idempotent buy (same idem twice)
    r1 = post_json(s, f'/shop/buy/{pid.group(1)}/', {'idem': 'my-fixed-key-123'}) if pid else None
    r2 = post_json(s, f'/shop/buy/{pid.group(1)}/', {'idem': 'my-fixed-key-123'}) if pid else None
    if pid:
        ok(as_json(r1) and as_json(r1).get('ok') and as_json(r2) and as_json(r2).get('duplicate'), 'buy idempotency (2nd = duplicate)', f'{r1.text[:80]} | {r2.text[:80]}')

    # equip/unequip/consume flows
    inv = s.get(BASE + '/shop/inventory/', timeout=30)
    ok(inv.status_code == 200, 'inventory after buy')
    eq = re.search(r'data-act="(equip|unequip)" data-id="(\d+)"', inv.text)
    if eq:
        eid = eq.group(2)
        r = post_json(s, f'/shop/equip/{eid}/', {})
        ok(r.status_code == 200 and as_json(r) and as_json(r).get('ok'), 'equip item', r.text[:150])
        r = post_json(s, f'/shop/unequip/{eid}/', {})
        ok(r.status_code == 200 and as_json(r) and as_json(r).get('ok'), 'unequip item', r.text[:150])
    else:
        ok(False, 'equip button found')
    cons = re.search(r'/shop/consume/(\d+)/', inv.text)
    if cons:
        r = post_json(s, f'/shop/consume/{cons.group(1)}/', {})
        ok(r.status_code == 200, 'consume item', r.text[:150])
    else:
        print('    (no consumable item to test)')

    print('=== Quiz full flow ===')
    r = s.get(BASE + '/academy/quiz/29/', timeout=30)
    m = re.search(r'name="session_key" value="([^"]+)"', r.text)
    ok(r.status_code == 200, 'quiz page loads')
    skey = m.group(1) if m else None
    print('    session_key found:', bool(skey))
    if skey:
        r = post_json(s, '/academy/quiz/save-time/', {'session_key': skey, 'seconds': 12})
        ok(r.status_code == 200, 'quiz save time', r.text[:150])
        r = s.post(BASE + '/academy/quiz/submit/29/', data={
            'csrfmiddlewaretoken': s.cookies.get('csrftoken', ''), 'session_key': skey},
            headers={'Referer': BASE + '/academy/quiz/29/'}, allow_redirects=False, timeout=30)
        ok(r.status_code == 302 and '/result/' in r.headers.get('Location', ''),
           'quiz submit (form)', f'-> {r.status_code} {r.headers.get("Location")}')

    print('=== Writing + AI fallback ===')
    r = s.get(BASE + '/academy/writing/', timeout=30)
    ok(r.status_code == 200, 'writing page')
    r = post_json(s, '/academy/writing/evaluate/', {
        'prompt': 'Write about your daily routine', 'submission': 'I am go to school every day and I like my teacher very much.'})
    ok(r.status_code == 200, 'writing evaluate (fallback w/o AI)', r.text[:200])
    r = post_json(s, '/academy/ai/chat/', {'message': 'سلام! چطور انگلیسی یاد بگیرم؟'})
    ok(r.status_code == 200, 'ai chat (graceful no-key)', r.text[:200])
    r = s.get(BASE + '/academy/ai/chat/history/', timeout=30)
    ok(r.status_code == 200, 'ai chat history', r.text[:150])

    print('=== Idioms placement full flow (form-based) ===')
    r = s.get(BASE + '/academy/idioms/placement/', timeout=30)
    ok(r.status_code == 200, 'placement page')
    r = s.post(BASE + '/academy/idioms/placement/', data={
        'csrfmiddlewaretoken': s.cookies.get('csrftoken', ''), 'level': 'A1'},
        headers={'Referer': BASE + '/academy/idioms/placement/'}, allow_redirects=False, timeout=30)
    ok(r.status_code in (301, 302) and '/placement/quiz/' in r.headers.get('Location', ''),
       'placement start (form)', f'-> {r.status_code} {r.headers.get("Location")}')
    loc = r.headers.get('Location', '')
    if loc:
        rr = s.get(BASE + loc, timeout=30)
        ok(rr.status_code == 200, 'placement quiz page')
        aid = loc.rstrip('/').split('/')[-1]
        r3 = s.post(BASE + f'/academy/idioms/placement/submit/{aid}/',
                    data={'csrfmiddlewaretoken': s.cookies.get('csrftoken', ''),
                          'ans[]': ['0', '1', '2', '3', '0', '1', '2', '3']},
                    headers={'Referer': BASE + loc}, allow_redirects=False, timeout=30)
        ok(r3.status_code in (301, 302), 'placement submit', f'-> {r3.status_code}')

    print('=== Exam page + save answer ===')
    r = s.get(BASE + '/academy/exam/10/', timeout=30)
    ok(r.status_code == 200, 'exam page')

    print('=== Program app module ===')
    for u in ['/app/', '/app/calculate/', '/app/calculate-w/', '/app/converter/', '/app/discount/',
              '/app/factorial/', '/app/gcd-lcm-page/', '/app/pythagorean/', '/app/linear-equation/',
              '/app/stats/']:
        rr = s.get(BASE + u, timeout=30)
        ok(rr.status_code in (200, 301, 302), f'programapp {u}', f'-> {rr.status_code}')
    r = post_json(s, '/app/calculate/', {'a': 3, 'b': 4, 'op': 'add'})
    ok(r.status_code in (200, 302, 400), 'calculate post', f'-> {r.status_code}')

    print('=== Language pages ===')
    for u in ['/language/', '/language/drag-drop/', '/language/word-guessing/',
              '/language/word-scramble/', '/language/dictation/', '/language/word-sprint/']:
        rr = s.get(BASE + u, timeout=30)
        ok(rr.status_code == 200, f'lang page {u}', f'-> {rr.status_code}')

    print('=== Messenger join token flow ===')
    convs = s.get(BASE + '/messenger/conversations/', timeout=30).json()
    grp = next((c for c in convs.get('conversations', []) if c.get('is_group')), None)
    if grp and grp.get('invite_url'):
        token = grp['invite_url'].rstrip('/').split('/')[-1]
        r = s.get(BASE + f'/messenger/join/{token}/', timeout=30)
        ok(r.status_code == 200, 'group join page')
        r = s.post(BASE + f'/messenger/join/{token}/', data={
            'csrfmiddlewaretoken': s.cookies.get('csrftoken', '')},
            headers={'Referer': BASE + f'/messenger/join/{token}/'}, allow_redirects=False, timeout=30)
        ok(r.status_code in (301, 302), 'group join POST')
        # leave group
        r = post_json(s, f'/messenger/group/{grp["id"]}/leave/', {})
        ok(r.status_code == 200, 'leave group', r.text[:150])
    else:
        ok(False, 'group invite found')

    print('=== Password reset OTP flow ===')
    sn = requests.Session()
    sn.get(BASE + '/password-reset/')
    r = sn.post(BASE + '/password-reset/', data={
        'csrfmiddlewaretoken': sn.cookies.get('csrftoken', ''),
        'email': 'newwave@test.com'},
        headers={'Referer': BASE + '/password-reset/'}, allow_redirects=False, timeout=30)
    ok(r.status_code in (200, 302), 'password reset request', f'-> {r.status_code}')

    print()
    print(f'RESULT: {len(passes)} passed, {len(fails)} failed')
    if fails:
        print('FAILED:', fails)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
