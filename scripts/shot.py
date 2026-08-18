import sys
import time

from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8137'
OUT = '/tmp/shots'


def shots(url, name, sizes, login=True, click=None, hover=None, wait=500, full=False):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': sizes[0][0], 'height': sizes[0][1]})
        if login:
            pg.goto(BASE + '/login/')
            pg.fill('input[name=username]', 'testuser')
            pg.fill('input[name=password]', 'test123456')
            pg.click('button[type=submit]')
            pg.wait_for_url('**/home/**', timeout=8000)
        for i, (w, h) in enumerate(sizes):
            pg.set_viewport_size({'width': w, 'height': h})
            pg.goto(BASE + url)
            pg.wait_for_timeout(wait)
            if hover:
                pg.hover(hover)
                pg.wait_for_timeout(350)
            if click:
                pg.click(click)
                pg.wait_for_timeout(450)
            pg.screenshot(path=f'{OUT}/{name}_{i}_{w}.png', full_page=full)
        b.close()
    print('done', name, [f'{name}_{i}_{w}.png' for i, (w, h) in enumerate(sizes)])


if __name__ == '__main__':
    url = sys.argv[1]
    name = sys.argv[2]
    sizes = [(int(w), int(h)) for w, h in (s.split('x') for s in sys.argv[3].split(','))]
    kw = {}
    if '--click' in sys.argv:
        kw['click'] = sys.argv[sys.argv.index('--click') + 1]
    if '--hover' in sys.argv:
        kw['hover'] = sys.argv[sys.argv.index('--hover') + 1]
    if '--full' in sys.argv:
        kw['full'] = True
    if '--guest' in sys.argv:
        kw['login'] = False
    shots(url, name, sizes, **kw)
