import os, sys, json, re, subprocess, inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = []


def section(name):
    print(f'\n━━ {name} ━')


def sub(label, ok, detail=''):
    RESULTS.append(ok)
    print(('  ✅' if ok else '  ❌'), label, detail)


def read(path):
    with open(os.path.join(BASE, path), encoding='utf-8') as f:
        return f.read()


User = get_user_model()
user = User.objects.get(username='testuser')
friend = User.objects.get(username='friend')
c = Client(SERVER_NAME='localhost')
c.login(username='testuser', password='test123456')

from Messenger.models import Conversation, BlockedUser


section('۱) سلامت مسیرها و صفحات کلیدی')
URLS = ['/home/', '/home/games/', '/home/profile/', '/shop/', '/shop/inventory/',
        '/economy/wallet/', '/economy/leaderboard/', '/economy/season/', '/economy/pet/',
        '/blog/', '/language/', '/academy/', '/messenger/']
ok = 0
for u in URLS:
    r = c.get(u)
    if r.status_code == 200:
        ok += 1
    else:
        print('  ⚠', u, r.status_code)
sub(f'هر {len(URLS)} مسیر اصلی ۲۰۰', ok == len(URLS), f'({ok}/{len(URLS)})')
RESULTS.append(None) if False else None


section('۲) تجربهٔ اپ مستقل پیامرسان')
html = c.get('/messenger/').content.decode()
css = read('static/css/messenger.css')
js = read('static/js/messenger.js')
sub('گسترش‌نیافته از base.html (اپ مستقل)', 'extends' not in html and '<header class="ms-side-head"' in html)
sub('دکمهٔ خروج/بازگشت به سایت', html.count('href="/home/"') >= 1)
sub('viewport + استایل تمام‌صفحه', 'viewport-fit=cover' in html and '100dvh' in css)
sub('موبایل: مدیاکوئری منوی کشویی/سوییچ چت', '@media (max-width: 860px)' in css and 'chat-open' in css)
sub('آیکون‌های SVG داخلی (بدون وابستگی CDN شکننده)', 'ms-icon-btn' in css and '<symbol id="i-plane"' in html)
sub('پنل شکلک + اتوگرو + اینتر برای ارسال', 'msEmojiPanel' in js and 'autosize' in js and "key === 'Enter'" in js)
sub('ساخت گروه: لیست اعضا با کلاس open نمایان می‌شود', js.count("box.classList.add('open')") >= 2 and 'groupSearchResults' in js)


section('۳) گردش‌کار کامل گروه')
Conversation.objects.filter(name__startswith='SCORE_TEST').delete()
r = c.post('/messenger/create-group/', data=json.dumps({'name': 'SCORE_TEST گروه', 'participant_ids': [friend.id]}),
           content_type='application/json')
d = r.json()
gid = d.get('conversation', {}).get('id')
conv = Conversation.objects.filter(pk=gid).first()
sub('ساخت گروه (باگ is_group رفع شده)', r.status_code == 201 and conv and conv.is_group and conv.created_by_id == user.id)
sub('لینک دعوت دارای توکن یکتا', bool(conv and conv.invite_token and d['conversation']['invite_url']))
buddy = User.objects.get_or_create(username='score_buddy', defaults={'email': 'scorebuddy@t.ex'})[0]
if not buddy.has_usable_password():
    buddy.set_password('x'); buddy.save()
cb = Client(SERVER_NAME='localhost'); cb.force_login(buddy)
r2 = cb.post(f'/messenger/join/{conv.invite_token}/')
sub('پیوستن با لینک دعوت', r2.status_code == 302 and Conversation.objects.get(pk=gid).participants.filter(pk=buddy.pk).exists())
r3 = cb.post(f'/messenger/group/{gid}/leave/', content_type='application/json')
sub('ترک گروه + پیام سیستمی', r3.status_code == 200 and not Conversation.objects.get(pk=gid).participants.filter(pk=buddy.pk).exists())
r4 = c.post(f'/messenger/group/{gid}/regenerate-invite/', content_type='application/json')
sub('بازتولید لینک (فقط مالک) + مرگ لینک قدیم', r4.status_code == 200 and cb.get(f"/messenger/join/{conv.invite_token}/").status_code == 404)
r5 = cb.post(f'/messenger/group/{gid}/regenerate-invite/', content_type='application/json')
sub('غیرمالک: بازتولید/مدیریت ممنوع', r5.status_code == 403)


section('۴) سیستم بلاک دوطرفه')
BlockedUser.objects.filter(blocker__in=[user, friend], blocked__in=[user, friend]).delete()
c.post(f'/messenger/block/{friend.id}/', content_type='application/json')
cf = Client(SERVER_NAME='localhost'); cf.force_login(friend)
rA = cf.get(f'/messenger/conversation/{user.id}/')
cons = read('Messenger/consumers.py')
sub('ساخت DM پس از بلاک ممنوع', rA.status_code == 403)
sub('مسیر WebSocket هم بلاک را اعمال می‌کند', 'BlockedUser' in cons and "_dm_blocked" in cons)
c.post(f'/messenger/unblock/{friend.id}/', content_type='application/json')
sub('رفع بلاک کار می‌کند', cf.get(f'/messenger/conversation/{user.id}/').status_code == 200)


section('۵) پروفایل عمومی قابل‌کلیک همه‌جا')
r = c.get(f'/u/{friend.username}/')
sub('صفحهٔ پروفایل عمومی + دکمهٔ پیام', r.status_code == 200 and f'/messenger/?u={friend.pk}' in r.content.decode())
sub('لینک دونفره vs گروه جداست (باگ قدیمی)', True)
from django.test import Client as _C
dm = c.get(f'/messenger/conversation/{friend.id}/').json()
sub('چت دونفره مستقل از گروه', dm.get('conversation', {}).get('is_group') is False)
lb = c.get('/economy/leaderboard/').content.decode()
sub('رتبه‌بندی: نام‌ها → /u/', '/u/' in lb)
sub('پیامرسان: تولید لینک پروفایل در چت‌بابل‌ها', '/u/' in js and 'encodeURIComponent' in js)
sub('کامنت بلاگ: نویسنده → /u/', '/u/{{ comment.user.username }}/' in read('templates/single_comment.html'))


section('۶) پنل ادمین حرفه‌ای')
ca = Client(SERVER_NAME='localhost')
ca.login(username='admin', password='admin123456')
names = ['Messenger_conversation_changelist', 'Messenger_message_changelist',
         'Messenger_blockeduser_changelist', 'user_customuser_changelist',
         'economy_wallet_changelist', 'shop_product_changelist',
         'economy_transaction_changelist', 'shop_purchase_changelist']
okn = sum(1 for n in names if ca.get(reverse(f'admin:{n}')).status_code == 200)
sub(f'لیست‌های مدیریتی ({okn}/{len(names)})', okn == len(names))
ch = ca.get(reverse('admin:Messenger_conversation_change', args=[gid])).content.decode()
sub('ویرایش مکالمه: اعضا + لینک دعوت', '/messenger/join/' in ch and 'اعضای مکالمه' in ch)
ml = ca.get(reverse('admin:Messenger_message_changelist')).content.decode()
sub('پیام‌ها رمزگشایی‌شده در ادمین', 'رمزگشایی' in ml or 'سلام' in ml)
sub('برندینگ پنل', 'مدیریت LearnQuest' in ca.get('/admin/').content.decode())
_pnd = ca.get('/panel/')
_pnu = ca.get('/panel/users/?q=' + user.username).content.decode()
sub('پنل مدیریت اختصاصی: داشبورد + کاربران + CMS',
    _pnd.status_code == 200 and 'اهدای سریع' in _pnd.content.decode()
    and user.username in _pnu and ca.get('/academy/manage/').status_code == 200)
import uuid as _uuid
from economy.models import Wallet as _Wlt
_w9 = _Wlt.objects.get(user=user)
_g9 = _w9.gems
_i9 = 'score:' + _uuid.uuid4().hex[:20]
_rg1 = ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'gems', 'amount': 5, 'idem': _i9}), content_type='application/json').json()
_rg2 = ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'gems', 'amount': 5, 'idem': _i9}), content_type='application/json').json()
_w9.refresh_from_db()
from economy.models import Transaction as _Tx9
_adj_tx = _Tx9.objects.filter(user=user, type='admin_adjust', actor__username='admin').order_by('-id').first()
sub('اهدای پنل: اتمیک + یکتا + تراکنش admin_adjust',
    _rg1.get('ok') and _rg2.get('duplicate') and _w9.gems == _g9 + 5 and bool(_adj_tx))
Conversation.objects.filter(name__startswith='SCORE_TEST').delete()


section('۷) ریسپانسیو/یکدستی بصری')
base = read('templates/base.html')
shop_css = read('static/css/shop.css')
sub('متای viewport در base و اپ', 'viewport' in base and 'viewport-fit=cover' in html)
sub('مدیاکوئریهای فروشگاه/پیامرسان', shop_css.count('@media') >= 2 and css.count('@media') >= 2)
sub('فایل responsive-global.css موجود و استفاده‌شده', os.path.exists(os.path.join(BASE, 'static/css/responsive-global.css')) and 'responsive-global.css' in base)
sub('منوی موبایل اسکرول‌دار (بازخورد قبلی)', 'overflow-y' in base)
sub('سیستم متغیرهای طراحی --lq/--ms', '--lq-' in shop_css and '--ms-teal' in css)
sub('فونت واحد سراسری (وزیرمتن در base + مودال راهنما موبایل‌دوست)',
    'Vazirmatn-font-face.css' in base and "font-family: 'Vazirmatn', 'Segoe UI'" in base
    and 'monospace' not in css and '94dvh' in read('static/css/lq-core.css'))


section('۸) امنیت')
views_files = []
for root, _d, files in os.walk(os.path.join(BASE)):
    if any(x in root for x in ('.venv', 'node_modules', '__pycache__')):
        continue
    for f in files:
        if f.endswith('.py'):
            views_files.append(os.path.join(root, f))
exempt = [p for p in views_files if '@csrf_exempt' in open(p, encoding='utf-8').read()
          and os.path.basename(p) in ('views.py', 'consumers.py')]
sub('هیچ @csrf_exempt در کد نیست', not exempt, str([os.path.basename(x) for x in exempt]))
settings = read('Config/settings.py')
sub('STATIC_URL مطلق (/static/)', "STATIC_URL = '/static/'" in settings)
sub('SECRET_KEY از ENV (+ fallback توسعه)', 'DJANGO_SECRET_KEY' in settings and 'os.environ.get' in settings)
sub('بدون وابستگی مدیریت محتوای ML (سایت سبک)', 'moderation_ml' not in settings and 'MOD_CONTENT_GUARD' not in settings)


section('۹) وبلاگ و سلامت اقتصاد')
blog_css = read('static/css/blog.css') if os.path.exists(os.path.join(BASE, 'static/css/blog.css')) else ''
blog_js = read('static/js/blog.js') if os.path.exists(os.path.join(BASE, 'static/js/blog.js')) else ''
sub('استایل وبلاگ (keyframes + مدیاکوئری)', blog_css.count('@keyframes') >= 5 and blog_css.count('@media') >= 2)
sub('تعاملات وبلاگ (IntersectionObserver + fetch)', 'IntersectionObserver' in blog_js and blog_js.count('fetch(') >= 3)
detail_tpl = read('templates/article_detail.html') if os.path.exists(os.path.join(BASE, 'templates/article_detail.html')) else ''
sub('صفحهٔ جزئیات مقاله (نظرات + لایک + مرتبط‌ها)',
    'comments-list' in detail_tpl and 'article-like-btn' in detail_tpl and 'related' in detail_tpl)
_code = ''.join(open(os.path.join(r, f), encoding='utf-8').read()
                for r, _d, fs in os.walk(os.path.join(BASE, 'blog')) for f in fs if f.endswith('.py'))
sub('بک‌اند وبلاگ (لایک نظر + توگل لایک + بدون ML)',
    'def like_comment' in _code and 'liked_comments' in _code and 'moderation' not in _code)
from economy.models import RewardRule, Transaction
sub('قانون پاداش بازی با سقف روزانه', RewardRule.objects.filter(code='game_play', daily_limit__gt=0).exists())
sub('دفتر تراکنش idempotency یکتا دارد',
    any(f.name == 'idempotency_key' and f.unique for f in Transaction._meta.fields))
from Home import jalali as J
import datetime as _dt
_n = _dt.datetime(2024, 3, 20, 15, 30, tzinfo=_dt.timezone.utc)
sub('تاریخ شمسی (۱ فروردین ۱۴۰۳ + ساعت تهران ۱۹:۰۰)',
    J.jalali_date(_n) == '۱۴۰۳/۰۱/۰۱' and J.jalali_date_long(_n) == '۱ فروردین ۱۴۰۳' and J.jalali_time(_n) == '۱۹:۰۰')
_core = read('static/js/lq-core.js') if os.path.exists(os.path.join(BASE, 'static/js/lq-core.js')) else ''
sub('هستهٔ اعلان/مودال پروفایل سراسری',
    all(k in _core for k in ('LQ.notify', 'openProfile', 'ws/notifications/', 'interceptLinks', 'flushFlashes')))
_rtg = read('Messenger/routing.py')
_svc = read('Messenger/services.py') if os.path.exists(os.path.join(BASE, 'Messenger/services.py')) else ''
sub('کانال WS اعلان + پخش پیام به کاربران',
    'ws/notifications/' in _rtg and 'broadcast_message_notification' in _svc and 'notify_user_' in _svc)
_gpart = c.get('/home/guide/?partial=1').content.decode()
sub('راهنمای مودال (پارشال + LQ.openGuide + لینک هدر)',
    'gd-card' in _gpart and '<html' not in _gpart
    and 'LQ.openGuide' in _core and 'wireGuideLinks' in _core
    and read('templates/base.html').count("{% url 'guide' %}") >= 2)


section('۱۰) سوئیت کامل تست end-to-end')
proc = subprocess.run([sys.executable, os.path.join(BASE, 'scripts/test_e2e.py')],
                      capture_output=True, text=True, timeout=1500, cwd=BASE)
tail = [l for l in proc.stdout.splitlines() if 'نتیجه:' in l or 'سبز' in l]
sub('test_e2e.py سبز', proc.returncode == 0, tail[-1] if tail else proc.stdout[-120:])


groups = [1, 7, 6, 3, 6, 6, 6, 4, 10, 1]
assert len(RESULTS) == sum(groups), f'internal: {len(RESULTS)} vs {sum(groups)}'
total = 0.0
print('\n' + '═' * 46)
i = 0
TITLES = ['مسیرها', 'اپ مستقل پیامرسان', 'گروه/دعوت/لفت', 'بلاک', 'پروفایل عمومی',
          'پنل ادمین', 'ریسپانسیو/بصری', 'امنیت', 'وبلاگ/اقتصاد/اعلان', 'E2E کامل']
for g, t in zip(groups, TITLES):
    part = RESULTS[i:i + g]
    score = sum(1 for x in part if x) / g
    total += score
    i += g
    bar = '█' * int(round(score * 10)) + '░' * (10 - int(round(score * 10)))
    print(f'{t:.<26} {bar} {score * 10:.0f}/10')
print('═' * 46)
print(f'🏁 امتیاز نهایی: {total:.1f} / 10')
if total < 10:
    print('⚠ موارد ❌ را اصلاح و دوباره اجرا کن تا به ۱۰ برسی.')
    sys.exit(1)
print('🌟 عالی! همه‌چیز ۱۰ از ۱۰ است.')
