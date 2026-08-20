# -*- coding: utf-8 -*-
"""استخراج کلاس‌های lq-* از shop.css قدیمی به فایل economy.css"""
import re

old = open('/tmp/old_shop.css', encoding='utf-8').read()

blocks = []
lines = old.split('\n')
i = 0
while i < len(lines):
    line = lines[i]
    m = re.match(r'^([^{}]+)\{', line)
    if m:
        selector = m.group(1)
        if 'lq-' in selector or selector.strip() == ':root':
            block = line
            depth = line.count('{') - line.count('}')
            i += 1
            while i < len(lines) and depth > 0:
                block += '\n' + lines[i]
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1
            blocks.append(block)
            continue
    i += 1

css = '\n\n'.join(blocks)
header = """/* ============================================================
   LearnQuest — Economy pages (wallet / leaderboard / season / pet)
   lq-* component styles (restored after the shop redesign)
   ============================================================ */

"""
with open('static/css/economy.css', 'w', encoding='utf-8') as f:
    f.write(header + css)
print('blocks extracted:', len(blocks))
print('size:', len(css))
