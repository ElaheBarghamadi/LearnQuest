# -*- coding: utf-8 -*-
"""پیدا کردن متن فارسی در تمپلیت‌های آکادمی (فقط UI نه ترجمه)."""
import os
import re

base = 'language_academy/templates/language_academy'
for fn in sorted(os.listdir(base)):
    if not fn.endswith('.html'):
        continue
    path = os.path.join(base, fn)
    content = open(path, encoding='utf-8').read()
    persian_texts = re.findall(r'>([^<>]*[\u0600-\u06FF][^<>]*)<', content)
    persian_texts = [t.strip() for t in persian_texts
                     if t.strip() and not t.strip().startswith('/*')]
    if persian_texts:
        print(f'=== {fn} ({len(persian_texts)}) ===')
        for t in persian_texts[:10]:
            print('   ', repr(t[:95]))
