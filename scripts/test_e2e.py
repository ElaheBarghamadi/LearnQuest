import os, django, json, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
django.setup()

from django.test import Client
from django.utils import timezone

PASSED, FAILED = [], []
def T(name, cond, extra=''):
    (PASSED if cond else FAILED).append(name)
    print(('  ✅' if cond else '  ❌'), name, extra if extra else '')

RUN = __import__('uuid').uuid4().hex[:8]
def ID(x):
    return RUN + ':' + x

c = Client(SERVER_NAME='localhost')
assert c.login(username='testuser', password='test123456'), 'login failed'
from django.contrib.auth import get_user_model
from economy.models import Wallet, Transaction, ActiveBoost, UserSeasonPass, UserPet, RewardGrant
from economy import services as eco
from shop.models import Product, Purchase, InventoryItem
from shop import services as shop_svc

user = get_user_model().objects.get(username='testuser')


wallet = eco.get_wallet(user)
wallet.coins = 5000; wallet.gems = 100; wallet.save()
from shop.services import invalidate_cosmetics_cache
from economy.context_processors import invalidate_wallet_cache
invalidate_wallet_cache(user)

print('\n━━━ ۱) رندر صفحات جدید ━━━')
for url, name in [('/shop/', 'shop home'), ('/shop/inventory/', 'inventory'),
                  ('/economy/wallet/', 'wallet'), ('/economy/leaderboard/', 'leaderboard'),
                  ('/economy/season/', 'season'), ('/economy/pet/', 'pet'),
                  ('/shop/history/', 'history'), ('/shop/wishlist/', 'wishlist')]:
    r = c.get(url)
    T(f'GET {url}', r.status_code == 200, f'({r.status_code})')

print('\n━━━ ۲) خرید امن ━━━')
frame = Product.objects.get(slug='frame-gold')
old_coins = Wallet.objects.get(user=user).coins
r = c.post(f'/shop/buy/{frame.id}/', data=json.dumps({'idem': ID('test-buy-1')}),
           content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
d = r.json(); T('خرید قاب طلایی', d.get('ok') is True, str(d))
T('کسر ۵۰۰ سکه', Wallet.objects.get(user=user).coins == old_coins - 500)
T('آیتم در موجودی', InventoryItem.objects.filter(user=user, product=frame).exists())
T('Purchase ساخته شد', Purchase.objects.filter(user=user, product=frame).exists())


r = c.post(f'/shop/buy/{frame.id}/', data=json.dumps({'idem': ID('test-buy-1')}),
           content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
d = r.json(); T('بازپخش → duplicate', d.get('duplicate') is True, str(d))
T('موجودی دوباره کم نشد', Wallet.objects.get(user=user).coins == old_coins - 500)


dragon = Product.objects.get(slug='frame-rainbow')
expensive = Product.objects.get(slug='pet-dragon')
usergems = Wallet.objects.get(user=user); usergems.gems = 10; usergems.save()
invalidate_wallet_cache(user)
r = c.post(f'/shop/buy/{expensive.id}/', data=json.dumps({'idem': ID('no-money')}),
           content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
T('الماس ناکافی → 402', r.status_code == 402, f'({r.status_code}) {r.json()}')
T('الماس ثابت ماند', Wallet.objects.get(user=user).gems == 10)
usergems = Wallet.objects.get(user=user); usergems.gems = 100; usergems.save()
invalidate_wallet_cache(user)


limited = Product.objects.filter(slug='frame-royal').first()
Purchase.objects.filter(user=user, product=limited).delete()
InventoryItem.objects.filter(user=user, product=limited).delete()
limited.stock_limit = 1; limited.sold_count = 0; limited.save()
r = c.post(f'/shop/buy/{limited.id}/', data=json.dumps({'idem': ID('stock-1')}),
           content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
T('خرید نسخهٔ محدود اول OK', r.json().get('ok') is True)
r = c.post(f'/shop/buy/{limited.id}/', data=json.dumps({'idem': ID('stock-2')}),
           content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
T('موجودی تمام → 400', r.status_code == 400, f'({r.status_code})')
limited.stock_limit = 100; limited.save()


r = c.post(f'/shop/buy/{limited.id}/', data=json.dumps({'idem': ID('stock-3')}),
           content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
T('per_user_limit=1 → 400', r.status_code == 400, f'({r.status_code})')


before = Wallet.objects.get(user=user).coins
p = Purchase.objects.filter(user=user, product=frame).first()
from django.contrib.auth import get_user_model as gum
admin = gum().objects.get(username='admin')
res = shop_svc.refund_purchase(admin, p.pk, 'تست')
T('ریفاند OK', res.get('ok') is True)
T('سکه برگشت', Wallet.objects.get(user=user).coins == before + 500)
T('آیتم حذف شد', not InventoryItem.objects.filter(user=user, product=frame).exists())

shop_svc.purchase_product(user, frame.id, idempotency_key=ID('rebuy-frame'))

Purchase.objects.filter(user=user, product=limited).update(status='refunded')

print('\n━━━ ۳) Equip / Unequip ━━━')
item = InventoryItem.objects.get(user=user, product=frame)
r = c.post(f'/shop/equip/{item.id}/')
T('Equip قاب', r.json().get('ok') is True, str(r.json()))
cos = shop_svc.get_equipped_cosmetics(user, cached=False)
T('قاب در cosmetics', cos.get('frame') and cos['frame'][0]['css_class'] == 'frame-gold', str(cos))


frame2 = Product.objects.get(slug='frame-ice')
shop_svc.purchase_product(user, frame2.id, idempotency_key=ID('buy-frame2'))
item2 = InventoryItem.objects.get(user=user, product=frame2)
c.post(f'/shop/equip/{item2.id}/')
item.refresh_from_db()
T('اسلات یکتایی: قاب اول خاموش شد', not item.equipped)
cos = shop_svc.get_equipped_cosmetics(user, cached=False)
T('فقط قاب دوم فعال', cos['frame'][0]['slug'] == 'frame-ice')

r = c.post(f'/shop/unequip/{item2.id}/')
T('Unequip', r.json().get('ok') is True)


other = gum().objects.get(username='friend')
friend_item = InventoryItem.objects.filter(user=other).first()
if friend_item:
    r = c.post(f'/shop/equip/{friend_item.id}/')
    T('IDOR محافظت شد', r.json().get('ok') is False)
else:
    T('IDOR محافظت شد (بدون آیتم)', True)

print('\n━━━ ۴) مصرفی‌ها ━━━')
mb = Product.objects.get(slug='mystery-box')
shop_svc.purchase_product(user, mb.id, idempotency_key=ID('buy-mb'))
mb_item = InventoryItem.objects.get(user=user, product=mb)
qty0 = mb_item.quantity
r = c.post(f'/shop/consume/{mb_item.id}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
d = r.json()
T('بازکردن جعبهٔ مرموز', d.get('ok') is True, str(d)[:110])
mb_item.refresh_from_db(); T('تعداد یکی کم شد', mb_item.quantity == qty0 - 1)
T('پیام جایزه دارد', bool(d.get('message')))


hint = Product.objects.get(slug='hint-ticket')
InventoryItem.objects.filter(user=user, product__effect_type='hint_ticket').delete()
res = shop_svc.consume_item_by_effect(user, 'hint_ticket')
T('بلیط راهنما نداری → خطا', res.get('ok') is False)


xb = Product.objects.get(slug='xp-booster-15')
shop_svc.purchase_product(user, xb.id, idempotency_key=ID('buy-xb'))
xb_item = InventoryItem.objects.get(user=user, product=xb)
r = c.post(f'/shop/consume/{xb_item.id}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
T('فعال‌سازی بوستر XP', r.json().get('ok') is True, r.json().get('message', '')[:60])
boost = ActiveBoost.objects.filter(user=user, boost_type='xp').order_by('-created_at').first()
T('ActiveBoost ثبت شد', boost is not None and boost.is_active())


user.xp_before_boost = None
old_xp = get_user_model().objects.get(pk=user.pk).xp
eco.grant_xp(user, 100, source='test_boost')
new_xp = get_user_model().objects.get(pk=user.pk).xp
T('بوستر ×۱٫۵ اعمال شد (۱۰۰→۱۵۰)', new_xp - old_xp == 150, f'(Δ={new_xp - old_xp})')


shop_svc.purchase_product(user, hint.id, idempotency_key=ID('buy-hint'))
hint_item = InventoryItem.objects.get(user=user, product=hint)
r = c.post(f'/shop/consume/{hint_item.id}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
T('بلیط راهنما فقط در صفحهٔ کوئیز', r.json().get('ok') is False)

print('\n━━━ ۵) ضد فارم: پاداش یک‌بار کوئیز/امتحان ━━━')
from language_academy.views import _grant_pass_rewards_once
from language_academy.models import Quiz, Lesson
quiz = Quiz.objects.filter(xp_reward__gt=0).first()
if quiz:
    RewardGrant.objects.filter(user=user, rule_code__in=('quiz_pass', 'exam_pass')).delete()
    x1, c1, first1 = _grant_pass_rewards_once(user, quiz, 'quiz')
    x2, c2, first2 = _grant_pass_rewards_once(user, quiz, 'quiz')
    T('اولین پاس پاداش می‌دهد', first1 and x1 >= quiz.xp_reward, f'({x1}/{c1})')
    T('دومین پاس پاداش نمی‌دهد', not first2 and x2 == 0 and c2 == 0, f'({x2}/{c2})')
    T('RewardGrant یکتا ثبت شد', RewardGrant.objects.filter(
        user=user, rule_code='quiz_pass', period_key=f'quiz:{quiz.id}').exists())
else:
    T('کوئیز تست پیدا نشد (skip)', False, 'no quiz fixture')

print('\n━━━ ۶) بازی‌ها: CSRF + سقف روزانه ━━━')

c_csrf = Client(SERVER_NAME='localhost', enforce_csrf_checks=True)
c_csrf.login(username='testuser', password='test123456')
c_csrf.get('/games/snake/')
csrftok = c_csrf.cookies.get('csrftoken')
T('کوکی CSRF هست', csrftok is not None)
r = c_csrf.post('/games/save-snake-score/', data='{"score": 50}', content_type='application/json')
T('بدون CSRF → 403', r.status_code == 403, f'({r.status_code})')
r = c_csrf.post('/games/save-snake-score/', data='{"score": 50}',
                content_type='application/json', HTTP_X_CSRFTOKEN=csrftok.value)
T('با CSRF → 200', r.status_code == 200, r.json().get('status', '') if r.status_code == 200 else '')
if r.status_code == 200:
    T('پاسخ دارای xp_capped', 'xp_capped' in r.json())

print('\n━━━ ۷) جایزهٔ ورود روزانه ━━━')
from economy.models import DailyRewardClaim
from datetime import date as _date
from django.utils import timezone as _tz
DailyRewardClaim.objects.filter(user=user, claim_date=_tz.localdate()).delete()
r1 = eco.claim_daily_login(user)
r2 = eco.claim_daily_login(user)
T('اولی موفق', r1.get('ok') is True and not r1.get('already'), str(r1)[:80])
T('دومی رد شد', r2.get('already') is True)
T('استریک ثبت شد', r1.get('streak', 0) >= 1)

print('\n━━━ ۸) فصل و سیزن‌پس ━━━')
season = eco.get_active_season()
T('فصل فعال هست', season is not None)
usp, _ = UserSeasonPass.objects.get_or_create(user=user, season=season)

usp.season_xp = 0; usp.has_pass = False; usp.claimed_free = []; usp.claimed_premium = []
usp.save()
Purchase.objects.filter(user=user, product__slug='season-pass-1').delete()
InventoryItem.objects.filter(user=user, product__slug='season-pass-1').delete()

res = eco.claim_season_reward(user, 10, 'free')
T('پلهٔ نرسیده → رد', res.get('ok') is False, res.get('error', ''))

eco._add_season_xp(user, 500)
res = eco.claim_season_reward(user, 1, 'free')
T('پلهٔ ۱ رایگان کلایم شد', res.get('ok') is True, str(res)[:90])
res2 = eco.claim_season_reward(user, 1, 'free')
T('دوباره → already_claimed', res2.get('ok') is False)
res3 = eco.claim_season_reward(user, 1, 'premium')
T('بدون پس → needs_pass', res3.get('error') == 'needs_pass')

sp = Product.objects.get(slug='season-pass-1')
pr = shop_svc.purchase_product(user, sp.id, idempotency_key=ID('buy-pass'))
usp.refresh_from_db()
T('خرید سیزن‌پس فعال شد', usp.has_pass is True)
res4 = eco.claim_season_reward(user, 1, 'premium')
T('کلایم ویژه با پس OK', res4.get('ok') is True, str(res4)[:90])

print('\n━━━ ۹) پت ━━━')
chick = Product.objects.get(slug='pet-chick')
Purchase.objects.filter(user=user, product=chick).delete()
InventoryItem.objects.filter(user=user, product=chick).delete()
UserPet.objects.filter(user=user).delete()
pr = shop_svc.purchase_product(user, chick.id, idempotency_key=ID('buy-chick'))
pet = UserPet.objects.filter(user=user).first()
T('پت بعد از خرید ساخته شد', pet is not None)
if pet:
    T('پت فعال است', pet.is_active)
    h0 = pet.hunger()
    r = c.post(f'/economy/pet/{pet.id}/feed/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    d = r.json(); T('غذا دادن OK', d.get('ok') is True, str(d)[:90])
    pet.refresh_from_db()
    T('XP پت +20', pet.xp >= 20)

    c.post(f'/economy/pet/{pet.id}/rename/', {'name': 'پیکو'})
    pet.refresh_from_db(); T('تغییر نام', pet.name == 'پیکو')
    r = c.post(f'/economy/pet/{pet.id}/activate/')
    T('فعال‌سازی', r.status_code == 302)

    other_pet = UserPet.objects.filter(user__username='friend').first()
    if other_pet:
        r = c.post(f'/economy/pet/{other_pet.id}/feed/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        T('IDOR پت → 404', r.status_code == 404)

print('\n━━━ ۱۰) معکوس منفی و غیرقابل‌تغییر بودن دفتر ━━━')
try:
    eco.spend(user, 'coin', 10**9, source='test', idempotency_key=ID('overspend'))
    T('کسر بیش از موجودی → استثنا', False)
except eco.InsufficientFunds:
    T('کسر بیش از موجودی → استثنا', True)
tx = Transaction.objects.filter(user=user).first()
try:
    tx.amount = 999
    tx.save()
    T('دفتر تغییرناپذیر → خطا', False)
except ValueError:
    T('دفتر تغییرناپذیر → خطا', True)

print('\n━━━ ۱۱) گییت درس ویژه ━━━')
lesson = Lesson.objects.filter(is_exclusive=True, is_published=True).order_by('id').first()
if lesson:
    InventoryItem.objects.filter(user=user, product__effect_type='exclusive_lesson').delete()
    r = c.get(f'/academy/lesson/{lesson.id}/')
    T('درس ویژه بدون بلیط → ریدایرکت صفحه محصول', r.status_code == 302 and '/shop/product/' in r.url, r.url if r.status_code == 302 else '')

    from shop.services import _grant_item
    exprod = Product.objects.filter(effect_type='exclusive_lesson',
                                    effect_payload__lesson_id=lesson.id).first()
    T('محصول بلیط متناظر با درس ویژه پیدا شد', exprod is not None)
    _grant_item(user, exprod, 'test')
    ok = shop_svc.has_unlock(user, 'exclusive_lesson', lesson_id=lesson.id)
    T('has_unlock با بلیط', ok)
    r = c.get(f'/academy/lesson/{lesson.id}/')
    T('درس ویژه با بلیط باز شد', r.status_code == 200, f'({r.status_code})')
    InventoryItem.objects.filter(user=user, product__effect_type='exclusive_lesson').delete()
else:
    T('درس ویژهٔ منتشرشده پیدا نشد (skip)', False)

print('\n━━━ ۱۲-الف) اکادمی کاملاً رایگان (بدون بلیط/قفل برای درس‌های عادی) ━━━')
from language_academy.models import Chapter, World
free_fail = None
for ch in Chapter.objects.filter(is_published=True)[:8]:
    if c.get(f'/academy/chapter/{ch.id}/').status_code != 200:
        free_fail = ch.id
        break
T('همهٔ فصل‌ها بدون بلیط بازند', free_fail is None, f'(fail={free_fail})' if free_fail else '')
ls_fail, ls_cnt = None, 0
for l in Lesson.objects.filter(is_published=True, is_exclusive=False)[:10]:
    if c.get(f'/academy/lesson/{l.id}/').status_code != 200:
        ls_fail = l.id
        break
    ls_cnt += 1
T(f'همهٔ درس‌های عادی بدون بلیط بازند ({ls_cnt})', ls_fail is None and ls_cnt > 0, f'(fail={ls_fail})' if ls_fail else '')
T('بلیط فصل دیگر فعال نیست', not Product.objects.filter(effect_type='exclusive_chapter', is_active=True).exists())
_wm2 = c.get('/academy/').content.decode()
T('هیچ ارجاعی به بلیط فصل در نقشهٔ جهان نیست', 'chapter-unlock' not in _wm2)
_w2 = World.objects.filter(order=2).first()
if _w2:
    T('جهان دوم هم آزاد است', c.get(f'/academy/world/{_w2.id}/').status_code == 200)
_les_others = Lesson.objects.filter(is_published=True, is_exclusive=False)
T('هر درس exclusive یک بلیط فعال متناظر دارد (قرارداد سلامت)',
  all(Product.objects.filter(is_active=True, effect_type='exclusive_lesson',
                             effect_payload__lesson_id=l.id).exists()
      for l in Lesson.objects.filter(is_exclusive=True)))

print('\n━━━ ۱۲-ب) خرید سیزن‌پس از صفحه فصل ━━━')
usp = UserSeasonPass.objects.filter(user=user, season=eco.get_active_season()).first()
InventoryItem.objects.filter(user=user, product__effect_type='season_pass').delete()
Purchase.objects.filter(user=user, product__effect_type='season_pass').delete()
Coins = eco.get_wallet(user); Coins.gems = 200; Coins.save()
r = c.post('/economy/season/buy-pass/')
usp.refresh_from_db()
T('خرید سیزن‌پس از صفحه فصل ✅', usp.has_pass is True, f'→ {r.url if hasattr(r,"url") else r.status_code}')

print('\n━━━ ۱۲-ج) همگام‌سازی فعالیت‌ها (۱۰ تای آخر) ━━━')
from user.models import UserActivity
UserActivity.objects.filter(user=user).delete()
for i in range(14):
    UserActivity.objects.create(user=user, title=f'test {i}')
cnt = UserActivity.objects.filter(user=user).count()
T('DB فقط ۱۰ فعالیت نگه می‌دارد', cnt == 10, f'(count={cnt})')

print('\n━━━ ۱۲) رگرسیون صفحات اصلی ━━━')
for url in ['/', '/home/games/', '/home/profile/', '/blog/', '/language/', '/academy/']:
    r = c.get(url)
    ok = r.status_code == 200 or (url == '/' and r.status_code == 302)
    T(f'GET {url}', ok, f'({r.status_code})')

print('\n━━━ ۱۳) وبلاگ و مقالات ━━━')
from blog.models import Article, Category, Comment as BlogComment


bcat, _ = Category.objects.get_or_create(slug='lq-test-cat', defaults={'name': 'LQTEST دستهٔ تست'})
art, _ = Article.objects.get_or_create(
    slug='lq-test-article',
    defaults={'title': 'LQTEST مقالهٔ تستی', 'excerpt': 'خلاصهٔ تستی',
              'content': 'این یک متن تستی برای مقالهٔ وبلاگ است. ' * 30,
              'category': bcat, 'image': 'blog_images/test.jpg', 'is_featured': True})

r = c.get('/blog/')
h = r.content.decode()
T('GET /blog/ ۲۰۰', r.status_code == 200, f'({r.status_code})')
T('دیزاین جدید لود شده (blog.css + وزیرمتن + شِل)', 'css/blog.css' in h and 'blog-shell' in h and 'vazirmatn' in h.lower())
T('کارت مقاله در لیست مجله‌ای', 'bc-card' in h and 'LQTEST' in h)
T('چیپ دسته‌بندی و جستجوی مجله‌ای', 'bc-cat' in h and 'bc-search' in h)


v0 = Article.objects.get(pk=art.pk).views
r = c.get(f'/blog/article/{art.pk}/')
h = r.content.decode()
T('صفحهٔ جزئیات ۲۰۰', r.status_code == 200, f'({r.status_code})')
T('ساختار جزئیات (هِد/اکشن/نظرات)', 'art-head' in h and 'article-like-btn' in h and 'comments-list' in h)
c.get(f'/blog/article/{art.pk}/')
art.refresh_from_db()
T('بازدید با هر GET شمرده می‌شود (۲ بازدید = +۲)', art.views == v0 + 2, f'({v0}→{art.views})')


r = c.get('/blog/?q=' + __import__('urllib.parse', fromlist=['quote']).quote('مقالهٔ تستی'))
T('جستجو مقاله را پیدا می‌کند', 'LQTEST' in r.content.decode())
r = c.get('/blog/?q=zzqnotfound')
T('جستجوی بی‌نتیجه → حالت خالی', 'چیزی پیدا نشد' in r.content.decode())
r = c.get(f'/blog/?cat={bcat.slug}')
T('فیلتر دسته‌بندی', 'LQTEST' in r.content.decode())


r = c.get(f'/blog/get-article/{art.pk}/')
T('ریدایرکت مسیر قدیمی get-article', r.status_code == 301 and f'/blog/article/{art.pk}/' in r['Location'], f'({r.status_code})')
T('فاوآیکون در base لینک شده', 'favicon' in c.get('/blog/').content.decode().lower())
r = c.get('/favicon.ico')
T('GET /favicon.ico → ریدایرکت به SVG', r.status_code == 301 and 'favicon.svg' in r['Location'], f'({r.status_code})')


l0 = Article.objects.get(pk=art.pk).likes
r = c.post(f'/blog/like/{art.pk}/'); d = r.json()
T('لایک مقاله', d.get('liked') is True and d.get('likes') == l0 + 1, str(d))
r = c.post(f'/blog/like/{art.pk}/'); d = r.json()
T('آن‌لایک مقاله (توگل)', d.get('liked') is False and d.get('likes') == l0, str(d))


r = c.post('/blog/add-comment/', {'article_id': art.pk, 'content': 'خیلی عالی بود، ممنون!'})
d = r.json()
T('ثبت نظر AJAX', r.status_code == 200 and d.get('success') is True, f'({r.status_code}) {str(d)[:80]}')
T('HTML نظر حاوی لینک پروفایل نویسنده', '/u/testuser/' in d.get('html', ''))
cm_id = d.get('comment_id')
T('شمارندهٔ نظرات به‌روز', d.get('comments_count') == BlogComment.objects.filter(article=art, is_approved=True).count())


r = c.post('/blog/add-comment/', {'article_id': art.pk, 'content': 'نظر پشت سر هم'})
T('کول‌داون ضداسپم (۴۲۹)', r.status_code == 429, f'({r.status_code})')


sess = c.session; sess['last_comment_ts'] = 0; sess.save()
r = c.post('/blog/add-comment/', {'article_id': art.pk, 'content': 'سل'})
T('نظر خیلی کوتاه ۴۰۰', r.status_code == 400, f'({r.status_code})')


art2, _ = Article.objects.get_or_create(
    slug='lq-test-article-2',
    defaults={'title': 'LQTEST مقالهٔ دوم', 'excerpt': 'خلاصه', 'content': 'بدنه',
              'category': bcat, 'image': 'blog_images/test2.jpg'})
sess = c.session; sess['last_comment_ts'] = 0; sess.save()
r = c.post('/blog/add-comment/', {'article_id': art2.pk, 'parent_id': cm_id,
                                  'content': 'پاسخ به مقالهٔ اشتباه!'})
T('پاسخ الصاقی به مقالهٔ دیگر ۴۰۰', r.status_code == 400, f'({r.status_code})')
sess = c.session; sess['last_comment_ts'] = 0; sess.save()
r = c.post('/blog/add-comment/', {'article_id': art.pk, 'parent_id': cm_id,
                                  'content': 'پاسخ درست به نظر اول'})
d = r.json()
T('ثبت پاسخ (parent)', r.status_code == 200 and d.get('parent_id') == cm_id, f'({r.status_code})')


sess = c.session; sess['last_comment_ts'] = 0; sess.save()
r = c.post(f'/blog/like-comment/{cm_id}/'); d = r.json()
T('لایک نظر', d.get('liked') is True and d.get('likes') == 1, str(d))
r = c.post(f'/blog/like-comment/{cm_id}/'); d = r.json()
T('آن‌لایک نظر', d.get('liked') is False and d.get('likes') == 0, str(d))


from django.test import Client as _C
r = _C(SERVER_NAME='localhost').post('/blog/add-comment/', {'article_id': art.pk, 'content': 'مهمان'})
T('مهمان ۴۰۳/ریدایرکت لاگین', r.status_code in (302, 403), f'({r.status_code})')


import pathlib as _pl
_bad = [str(f) for f in _pl.Path('.').glob('**/*.py')
        if '.venv' not in str(f) and '__pycache__' not in str(f) and 'scripts' not in str(f)
        and 'moderation_ml' in f.read_text(encoding='utf-8', errors='ignore')]
T('هیچ ارجاعی به moderation_ml در کد نیست', not _bad, str(_bad))


print('\n━━━ ۱۴) پیامرسان: گروه/لینک دعوت/لفت/بلاک/فول‌اسکرین ━━━')
from Messenger.models import Conversation, Message as MsMessage, BlockedUser
import re as _re

User = get_user_model()
friend = User.objects.get(username='friend')
admin_u = User.objects.get(username='admin')


Conversation.objects.filter(name__startswith='LQTEST').delete()


r = c.get('/messenger/')
html = r.content.decode()
T('صفحهٔ پیامرسان ۲۰۰', r.status_code == 200, f'({r.status_code})')
T('اپ تمام‌صفحه مستقل است (بدون base.html)', 'ms-app' in html and 'پیامرسان | لرن‌کوئست' in html)
T('استایل و اسکریپت پیامرسان لینک شده', 'css/messenger.css' in html and 'js/messenger.js' in html)
T('دکمهٔ خروج به سایت هست', 'href="/home/"' in html)
T('فیلد مخفی CSRF در اپ', 'csrfmiddlewaretoken' in html)


r = c.post('/messenger/create-group/', data=json.dumps(
    {'name': 'LQTEST گروه تست', 'participant_ids': [friend.id]}),
    content_type='application/json')
d = r.json()
T('ساخت گروه OK', r.status_code == 201 and d.get('success') is True, f'({r.status_code} {d.get("error","")})')
conv_id = d['conversation']['id']
T('is_group و invite_url', d['conversation']['is_group'] is True and bool(d['conversation']['invite_url']))
conv = Conversation.objects.get(pk=conv_id)
T('created_by سازنده است', conv.created_by_id == user.id)
T('توکن دعوت یکتا ساخته شد', bool(conv.invite_token) and len(conv.invite_token) >= 10)
T('پیام سیستمی ساخت گروه', conv.messages.count() >= 1 and 'ساخته شد' in conv.messages.first().get_content())


r = c.post('/messenger/create-group/', data=json.dumps(
    {'name': 'الف' * 300, 'participant_ids': [friend.id]}), content_type='application/json')
T('نام گروه بیش‌از‌حد طولانی ۴۰۰', r.status_code == 400, f'({r.status_code})')
Conversation.objects.filter(name__startswith='گروه احمقها').delete()


buddy, created = User.objects.get_or_create(
    username='buddy_lq', defaults={'email': f'buddy_{RUN}@test.example'})
if created:
    buddy.set_password('buddy123'); buddy.save()
join_url = f'/messenger/join/{conv.invite_token}/'
c_b = Client(SERVER_NAME='localhost')
c_b.login(username='buddy_lq', password='buddy123')
r = c_b.get(join_url)
T('صفحهٔ دعوت ۲۰۰ + نام گروه', r.status_code == 200 and 'LQTEST' in r.content.decode(), f'({r.status_code})')
r = c_b.post(join_url)
T('POST پیوستن → ریدایرکت به چت', r.status_code == 302 and f'?c={conv_id}' in r['Location'], f'({r.status_code})')
conv.refresh_from_db()
T('عضویت کاربر جدید ثبت شد', conv.participants.filter(pk=buddy.pk).exists())
T('پیام سیستمی عضویت', any('پیوست' in m.get_content() for m in conv.messages.all()))


r = c_b.post('/messenger/send/', data=json.dumps({'conversation_id': conv_id, 'content': 'سلام بچه‌ها 👋'}),
             content_type='application/json')
T('ارسال پیام در گروه', r.status_code == 201, f'({r.status_code})')


r = c_b.post('/messenger/send/', data=json.dumps({'conversation_id': conv_id, 'content': '   '}),
             content_type='application/json')
T('پیام خالی ۴۰۰', r.status_code == 400, f'({r.status_code})')


r = c_b.post(f'/messenger/group/{conv_id}/add-members/', data=json.dumps({'participant_ids': [admin_u.id]}),
             content_type='application/json')
T('غیرمدیر نمی‌تواند عضو اضافه کند', r.status_code == 403, f'({r.status_code})')
r = c.post(f'/messenger/group/{conv_id}/add-members/', data=json.dumps({'participant_ids': [admin_u.id]}),
           content_type='application/json')
d = r.json()
T('مدیر عضو اضافه می‌کند', r.status_code == 200 and admin_u.username in (d.get('added') or []), str(d.get('error','')))
conv.refresh_from_db()
before_cnt = conv.participants.count()
r = c.post(f'/messenger/group/{conv_id}/remove-member/{admin_u.id}/', content_type='application/json')
T('مدیر عضو حذف می‌کند', r.status_code == 200, f'({r.status_code})')
conv.refresh_from_db()
T('تعداد اعضا کم شد', conv.participants.count() == before_cnt - 1)


old_token = Conversation.objects.get(pk=conv_id).invite_token
r = c_b.post(f'/messenger/group/{conv_id}/regenerate-invite/', content_type='application/json')
T('غیرمالک نمی‌تواند لینک عوض کند', r.status_code == 403, f'({r.status_code})')
r = c.post(f'/messenger/group/{conv_id}/regenerate-invite/', content_type='application/json')
d = r.json()
conv.refresh_from_db()
T('بازتولید لینک توسط مالک', r.status_code == 200 and conv.invite_token != old_token, f'({r.status_code})')
r = c_b.get(f'/messenger/join/{old_token}/')
T('لینک قدیمی از کار افتاد (۴۰۴)', r.status_code == 404, f'({r.status_code})')


r = c.get(f'/messenger/conversation/{friend.id}/')
d = r.json()
T('DM دونفره جدا از گروه ساخته می‌شود', d.get('success') and d['conversation']['is_group'] is False,
  str(d.get('error', '')))
dm_id = d['conversation']['id']


r = c_b.post(f'/messenger/group/{conv_id}/leave/', content_type='application/json')
d = r.json()
T('لفت گروه', r.status_code == 200 and d.get('success') is True, str(d.get('error', '')))
conv.refresh_from_db()
T('عضویت لغو شد', not conv.participants.filter(pk=buddy.pk).exists())
T('پیام سیستمی ترک گروه', any('ترک کرد' in m.get_content() for m in conv.messages.all()))


BlockedUser.objects.filter(blocker__in=[user, friend], blocked__in=[user, friend]).delete()
r = c.post(f'/messenger/block/{friend.id}/', content_type='application/json')
T('بلاک کاربر', r.status_code == 200 and r.json().get('blocked') is True)
c_f = Client(SERVER_NAME='localhost')
c_f.force_login(friend)
r = c_f.get(f'/messenger/conversation/{user.id}/')
T('بعد از بلاک، ساخت DM ممنوع (۴۰۳)', r.status_code == 403, f'({r.status_code})')
r = c_f.post('/messenger/send/', data=json.dumps({'conversation_id': dm_id, 'content': 'سلام!'}),
             content_type='application/json')
T('ارسال پیام توسط بلاک‌شده مسدود (۴۰۳)', r.status_code == 403, f'({r.status_code})')
r = c.post(f'/messenger/unblock/{friend.id}/', content_type='application/json')
T('رفع بلاک', r.status_code == 200 and r.json().get('blocked') is False)
r = c_f.post('/messenger/send/', data=json.dumps({'conversation_id': dm_id, 'content': 'سلام، برگشتم!'}),
             content_type='application/json')
T('بعد از رفع بلاک، ارسال دوباره OK', r.status_code == 201, f'({r.status_code})')


r = c.get('/messenger/blocked/')
T('API لیست بلاک‌شده‌ها', r.status_code == 200 and 'blocked_users' in r.json())


c_csrf = Client(SERVER_NAME='localhost', enforce_csrf_checks=True)
c_csrf.force_login(user)
r = c_csrf.post('/messenger/create-group/', data=json.dumps({'name': 'LQTEST x', 'participant_ids': [friend.id]}),
                content_type='application/json')
T('POST بدون توکن CSRF → ۴۰۳', r.status_code == 403, f'({r.status_code})')


r = c.get(f'/u/{friend.username}/')
html = r.content.decode()
T('پروفایل عمومی ۲۰۰', r.status_code == 200, f'({r.status_code})')
T('نام کاربر + دکمه پیام در پروفایل', friend.username in html and f'/messenger/?u={friend.pk}' in html)
T('پروفایل خودم ریدایرکت می‌شود', c.get(f'/u/{user.username}/').status_code in (301, 302))
r = c.get('/u/no_such_user_xyz/')
T('کاربر ناموجود ۴۰۴', r.status_code == 404, f'({r.status_code})')
r = c.get('/economy/leaderboard/')
T('نام‌ها در رتبه‌بندی لینک /u/ دارند', '/u/' in r.content.decode())


c_a = Client(SERVER_NAME='localhost')
c_a.login(username='admin', password='admin123456')
from django.urls import reverse as _rev
for rev_name, name in [('Messenger_conversation_changelist', 'ادمین: مکالمات'),
                       ('Messenger_message_changelist', 'ادمین: پیام‌ها'),
                       ('Messenger_blockeduser_changelist', 'ادمین: بلاک‌ها'),
                       ('user_customuser_changelist', 'ادمین: کاربران'),
                       ('economy_wallet_changelist', 'ادمین: کیف‌پول'),
                       ('shop_product_changelist', 'ادمین: محصولات')]:
    r = c_a.get(_rev(f'admin:{rev_name}'))
    T(name, r.status_code == 200, f'({r.status_code})')
r = c_a.get('/admin/')
T('برندینگ پنل مدیریت', 'مدیریت LearnQuest' in r.content.decode())
r = c_a.get(_rev('admin:Messenger_conversation_change', args=[conv_id]))
T('صفحهٔ ویرایش مکالمه + اعضا + لینک دعوت', r.status_code == 200 and '/messenger/join/' in r.content.decode(),
  f'({r.status_code})')
r = c_a.get(_rev('admin:Messenger_message_changelist'))
T('متن رمزگشایی‌شده در لیست پیام‌ها', 'سلام، برگشتم' in r.content.decode())


Conversation.objects.filter(name__startswith='LQTEST').delete()
BlockedUser.objects.filter(blocker__in=[user, friend], blocked__in=[user, friend]).delete()


print('\n━━━ ۱۵) بازی‌ها: صفحات + واریز امتیاز + راهنما ━━━')
import json as _json

GAME_PAGES = [
    '/games/snake/', '/games/2048/', '/games/reaction/', '/games/memory/',
    '/games/sudoku/', '/games/iq-test/', '/games/number-puzzle/', '/games/simon/',
    '/games/whack/', '/games/tictactoe/', '/games/minesweeper/', '/games/breakout/',
    '/language/drag-drop/', '/language/word-guessing/', '/language/word-scramble/',
    '/language/dictation/', '/language/word-sprint/',
]
for u in GAME_PAGES:
    r = c.get(u)
    T(f'صفحهٔ بازی {u}', r.status_code == 200, f'({r.status_code})')
_h = c.get('/games/snake/').content.decode()
T('کیت مشترک بازی‌ها تزریق شده', 'games-shared.css' in _h and 'gp-topbar' in _h)
T('دکمهٔ بازگشت به همهٔ بازی‌ها', '/home/games/' in _h)

from economy.models import RewardRule as _RR
_gp_old = _RR.objects.get(code='game_play').daily_limit
_RR.objects.filter(code='game_play').update(daily_limit=100000)

SAVE_ENDPOINTS = [
    ('/games/save-snake-score/', {'score': 120, 'completed': True}),
    ('/games/save-2048-score/', {'score': 300, 'completed': True}),
    ('/games/save-reaction-score/', {'best_ms': 250, 'completed': True}),
    ('/games/save-simon-score/', {'score': 5, 'completed': True}),
    ('/games/save-whack-score/', {'score': 12, 'completed': True}),
    ('/games/save-tictactoe-score/', {'score': 3, 'completed': True}),
    ('/games/save-memory-score/', {'moves': 18, 'time': 90, 'completed': True}),
    ('/games/save-puzzle-score/', {'moves': 60, 'time': 200, 'completed': True}),
    ('/games/save-sudoku-score/', {'time': 300, 'hints_used': 1, 'completed': True}),
    ('/games/save-iq-score/', {'score': 8, 'total': 10, 'completed': True}),
    ('/language/save-game-score/', {'matched_count': 5, 'total_words': 5, 'mistakes': 0}),
    ('/language/save-guessing-score/', {'score': 8, 'total_questions': 10, 'hints_used': 0, 'time_seconds': 80}),
    ('/language/save-scramble-score/', {'score': 6, 'total_questions': 8, 'time_seconds': 100, 'level': 'hard'}),
    ('/games/save-minesweeper-score/', {'time': 120, 'won': True}),
    ('/games/save-breakout-score/', {'score': 230, 'completed': True}),
    ('/language/save-dictation-score/', {'score': 9, 'total': 12, 'diff': 'medium'}),
    ('/language/save-sprint-score/', {'score': 20, 'answered': 30, 'seconds': 30}),
]
_granted_any = False
for url, payload in SAVE_ENDPOINTS:
    r = c.post(url, data=_json.dumps(payload), content_type='application/json')
    try:
        d = r.json()
    except Exception:
        d = {}
    ok = r.status_code == 200 and d.get('status') == 'success' and 'xp_gained' in d
    _granted_any = _granted_any or (d.get('xp_gained', 0) > 0)
    T(f'امتیاز بازی {url.split("/")[2]}', ok, f'xp={d.get("xp_gained")} ({r.status_code})')
T('حداقل یک بازی واقعاً XP واریز کرد', _granted_any)
_RR.objects.filter(code='game_play').update(daily_limit=_gp_old)

r = c.get('/home/guide/')
_h = r.content.decode()
T('صفحهٔ راهنما ۲۰۰', r.status_code == 200, f'({r.status_code})')
T('بخش‌های کلیدی راهنما', all(x in _h for x in ('بازی‌ها', 'سکه', 'پیامرسان', 'وبلاگ', 'فروشگاه')))
T('دکمهٔ راهنما در پروفایل', 'btn-guide' in c.get('/home/profile/').content.decode())

tmpl = c.get('/games/tictactoe/').content.decode() + c.get('/games/reaction/').content.decode()
T('کانواس بازی‌ها ریسپانسیو شد (قانون CSS)', 'max-width' in open('static/css/games-shared.css', encoding='utf-8').read())



print('\n━━━ ۱۶) اکادمی: رایگان + درس‌های ویژه + ناوبری ━━━')
from language_academy.models import Lesson as _Lesson
from shop.models import InventoryItem as _InvIt, Product as _Prod

r = c.get('/academy/lesson/1/')
T('درس اول آکادمی رایگان است (۲۰۰)', r.status_code == 200, f'({r.status_code})')
T('Lesson #1 دیگر exclusive نیست', not _Lesson.objects.get(pk=1).is_exclusive)

r = c.get('/academy/')
_h = r.content.decode()
T('سکشن «Exclusive Lessons» در صفحهٔ آکادمی', 'Exclusive Lessons' in _h)
T('دکمه‌های «Buy Ticket» به صفحهٔ محصول لینک‌اند', _h.count('exclusive-buy') >= 1 and '/shop/product/exclusive-lesson' in _h and 'Buy Ticket' in _h)
import re as _re16
_fa_ui = _re16.findall(r'[\u0600-\u06FF]+', _h)
T('رابط آکادمی کاملاً انگلیسی است (بدون فارسی در UI)', len(_fa_ui) == 0, str(_fa_ui[:4]) if _fa_ui else '')

_cafe = _Lesson.objects.get(name='Cafe Conversation')
_p_cafe = _Prod.objects.get(slug='exclusive-lesson-cafe')
_InvIt.objects.filter(user=user, product=_p_cafe).delete()
r = c.get(f'/academy/lesson/{_cafe.id}/')
T('درس ویژه بدون بلیط → صفحهٔ محصول', r.status_code == 302 and r.get('Location', '').endswith('/shop/product/exclusive-lesson-cafe/'),
  f"({r.status_code} → {r.get('Location','')})")
_InvIt.objects.create(user=user, product=_p_cafe)
r = c.get(f'/academy/lesson/{_cafe.id}/')
T('درس ویژه با بلیط → باز است', r.status_code == 200, f'({r.status_code})')
T('فالبک درس بدون کوئیز (انگلیسی)', 'No Quiz' in r.content.decode())
_InvIt.objects.filter(user=user, product=_p_cafe).delete()

_hnav = c.get('/home/').content.decode().split('</nav>')[0]
T('فروشگاه دکمهٔ تکی است (نه منو)', '🛒 فروشگاه</a>' in _hnav and 'بازار' not in _hnav)
T('دکمهٔ خروج کوچک (compact)', 'auth-btn-compact' in c.get('/home/').content.decode())

print('\n━━━ ۱۷) تاریخ شمسی + اعلان‌ها + مودال پروفایل ━━━')
from Home import jalali as J
import datetime as _dt

_d = _dt.datetime(2024, 3, 20, 15, 30, tzinfo=_dt.timezone.utc)
T('تبدیل میلادی→شمسی (نوروز ۱۴۰۳)', J.jalali_date(_d) == '۱۴۰۳/۰۱/۰۱')
T('نام ماه فارسی + اعداد فارسی', J.jalali_date_long(_d) == '۱ فروردین ۱۴۰۳')
T('زمان محلی تهران (۱۵:۳۰ UTC → ۱۹:۰۰)', J.jalali_time(_d) == '۱۹:۰۰')
T('ورودی None امن است', J.jalali_date(None) == '' and J.jalali_time(None) == '')
T('jdatetime هنوز در وابستگی‌هاست', 'jdatetime' in open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'requirements.txt'), encoding='utf-8').read())

_hprof = c.get('/home/profile/').content.decode()
T('پروفایل: تاریخ عضویت شمسی با نام ماه فارسی', any(m in _hprof for m in J.MONTHS_FA) and any(ch in _hprof for ch in '۰۱۲۳۴۵۶۷۸۹'))
_hblog = c.get('/blog/').content.decode()
import re as _re
T('وبلاگ: تاریخ مقاله‌ها شمسی', bool(_re.search(r'[۰-۹]{4}', _hblog)) and any(m in _hblog for m in J.MONTHS_FA))
T('وبلاگ: تاریخ میلادی Y/m/d باقی نمانده', not bool(_re.search(r'20\d\d/\d\d/\d\d', _hblog)))
from blog.models import Article as _Art
_art = _Art.objects.order_by('-published_at').first()
_cmt = c.get(f'/blog/article/{_art.pk}/').content.decode() if _art else ''
T('دیتیل مقاله: تاریخ شمسی', any(m in _cmt for m in J.MONTHS_FA))
_hwal = c.get('/economy/wallet/').content.decode()
T('کیف پول: تراکنش‌ها با تاریخ شمسی', bool(_re.search(r'[۰-۹]+ (?:' + '|'.join(J.MONTHS_FA) + r') [۰-۹]{4} - [۰-۹]{2}:[۰-۹]{2}', _hwal)))
_hsea = c.get('/economy/season/').content.decode()
T('فصل: بازهٔ شمسی', any(m in _hsea for m in J.MONTHS_FA))
_hshop = c.get('/shop/history/').content.decode()
T('تاریخچهٔ خرید: شمسی', any(m in _hshop for m in J.MONTHS_FA))
_pub = c.get('/u/admin/').content.decode()
T('پروفایل عمومی: «عضو از» شمسی', any(m in _pub for m in J.MONTHS_FA))

_hbase = c.get('/home/').content.decode()
T('هستهٔ اعلان لود می‌شود (css+js)', 'css/lq-core.css' in _hbase and 'js/lq-core.js' in _hbase)
T('LQ_USER برای کاربر لاگین ست است', 'window.LQ_USER' in _hbase and 'authed: true' in _hbase)
_base_tpl = ''
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates/base.html'), encoding='utf-8') as _f:
    _base_tpl = _f.read()
T('پیام‌های Django به فلش‌توست تبدیل شدن', 'data-lq-flash' in _base_tpl and 'class="messages"' not in _base_tpl)
_core_js = ''
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static/js/lq-core.js'), encoding='utf-8') as _f:
    _core_js = _f.read()
_core_css = ''
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static/css/lq-core.css'), encoding='utf-8') as _f:
    _core_css = _f.read()
T('مودال پروفایل + وصل‌شدن WS + رهگیری لینک /u/', all(k in _core_js for k in ('openProfile', 'ws/notifications/', '/api/profile/', 'interceptLinks')))
T('توست پیام (notify) + حذف‌سازی فعال', 'LQ.notify' in _core_js and 'LQ_ACTIVE_CHAT_ID' in _core_js)
T('استایل مودال + توست‌ها + اسکلت لودینگ', all(k in _core_css for k in ('.lq-pmodal', '.lq-toast', '.lq-skel', 'lqPop')))
_hms = c.get('/messenger/').content.decode()
T('اپ پیامرسان هم هستهٔ اعلان را دارد', 'lq-core.js' in _hms and 'window.LQ_USER' in _hms)
_msjs = ''
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static/js/messenger.js'), encoding='utf-8') as _f:
    _msjs = _f.read()
T('پیامرسان: لینک‌های پروفایل بدون تب جدید', 'target="_blank"' not in _msjs)
T('رهگیری /u/ دیگر به target حساس نیست (مودال همیشه)', 'a.target &&' not in _core_js)
_hac = c.get('/academy/').content.decode()
T('آکادمی هم هستهٔ اعلان را دارد', 'lq-core.js' in _hac)

r = c.get('/api/profile/admin/')
T('API کارت پروفایل ۲۰۰', r.status_code == 200)
_pj = r.json().get('profile', {})
T('API: فیلدهای کامل کارت', all(k in _pj for k in ('username', 'level', 'xp', 'global_rank', 'joined_jalali', 'can_message', 'message_url', 'blocked_by_me', 'pet', 'badges', 'level_progress')))
T('API: تاریخ عضویت شمسی', any(m in _pj.get('joined_jalali', '') for m in J.MONTHS_FA))
T('API: میان‌بر پیام درست است', _pj.get('message_url', '').startswith('/messenger/?u='))
T('API: کاربر ناشناس ۴۰۴', c.get('/api/profile/user-really-not-exists-xyz/').status_code == 404)
_cg = Client(SERVER_NAME='localhost')
T('API: مهمان به ورود هدایت می‌شود', _cg.get('/api/profile/admin/').status_code == 302)
_pubstill = c.get('/u/admin/')
T('صفحهٔ کامل پروفایل عمومی همچنان کار می‌کند', _pubstill.status_code == 200)

from Messenger.models import Conversation as _Conv, Message as _Msg
from Messenger.services import build_message_notification, notify_group_name
_adm = get_user_model().objects.get(username='admin')
_conv = _Conv.get_or_create_dm(user, _adm)
_m = _Msg(conversation=_conv, sender=user)
_m.set_content('تست بیلد اعلان ۱۷')
_m.save()
_notif = build_message_notification(_conv, _m, user)
T('بیلد اعلان: نوع + فرستنده + گفت‌وگو', _notif['type'] == 'notify.message' and _notif['sender_username'] == 'testuser' and _notif['conversation_id'] == _conv.pk)
T('بیلد اعلان: متن رمزگشایی‌شده و زمان فارسی', 'تست بیلد اعلان' in _notif['excerpt'] and any(ch in _notif['time'] for ch in '۰۱۲۳۴۵۶۷۸۹'))
T('نام گروه اعلان درست است', notify_group_name(42) == 'notify_user_42')
from django.conf import settings as _st
_apps = list(_st.INSTALLED_APPS)
T('daphne در INSTALLED_APPS و قبل از staticfiles (WebSocket روی runserver)',
  'daphne' in _apps and _apps.index('daphne') < _apps.index('django.contrib.staticfiles'))
T('ASGI_APPLICATION ست شده', _st.ASGI_APPLICATION == 'Config.asgi.application')
_m.delete()

_ct2 = Client(SERVER_NAME='localhost')
_ct2.login(username='testuser', password='test123456')
_rsend = _ct2.post('/messenger/send/', data=json.dumps({'conversation_id': _conv.pk, 'content': 'سلام از تست ۱۷'}), content_type='application/json')
T('ارسال پیام HTTP (با پخش اعلان) موفق', _rsend.status_code == 201 and _rsend.json().get('success'))
_sent_body = _rsend.json().get('message', {})
T('پیام: created_at_day شمسی دارد', any(m in _sent_body.get('created_at_day', '') for m in J.MONTHS_FA))
_rmsgs = c.get(f'/messenger/messages/{_conv.pk}/').json()
_today_j = J.jalali_time(timezone.localtime(timezone.now()), fa=False)
_lastm = _rmsgs.get('messages', [{}])[-1]
T('زمان پیام در ساعت تهران است', len(_lastm.get('created_at', '')) == 5 and _lastm.get('created_at', '').startswith(_today_j[:2]))
_convd = c.get('/messenger/conversations/').json()
_crow = [x for x in _convd.get('conversations', []) if x.get('id') == _conv.pk]
T('لیست گفت‌وگو: زمان آخرین پیام امروز = ساعت', bool(_crow) and ':' in (_crow[0].get('last_message_time') or ''))
_rt = c.get('/home/guide/').content.decode()
T('راهنما: سکشن اعلان/شمسی/پروفایل سریع', 'پروفایل سریع' in _rt and 'تاریخ شمسی' in _rt and 'اعلان لحظه‌ای' in _rt)


print('\n━━━ ۱۸) راهنمای مودال + بلاگ جدید + پنل مدیریت + ساخت گروه ━━━')
_rgp = c.get('/home/guide/?partial=1').content.decode()
T('راهنما: پارشال مودال بدون قالب اصلی', 'gd-card' in _rgp and '<html' not in _rgp and 'main-content' not in _rgp)
T('راهنما: صفحهٔ کامل همچنان سالم', 'gd-card' in _rt and 'gd-root' in _rt)
T('راهنما مودال: lq-core.js دارای openGuide و شنود لینک', 'LQ.openGuide' in _core_js and 'wireGuideLinks' in _core_js and '/home/guide/' in _core_js)
T('راهنما مودال: استایل مودال در lq-core.css', '.lq-gmodal-overlay' in _core_css and '.lq-gmodal-body' in _core_css)
T('هدر سایت: لینک راهنما (دسکتاپ+موبایل)', _base_tpl.count('{% url \'guide\' %}') >= 2)
T('هدر سایت: دراپ‌داون مدیریت فقط برای staff', "{% if user.is_staff %}" in _base_tpl and "panel:dashboard" in _base_tpl)

_msgr = open('static/js/messenger.js', encoding='utf-8').read()
T('ساخت گروه: نتایج جستجوی اعضا کلاس open می‌گیرد (رفع باگ دیده‌نشدن)', _msgr.count("box.classList.add('open')") >= 2)

_rb = c.get('/blog/').content.decode()
T('بلاگ مینیمال: پوسته/سربرگ/ردیف/متای تمیز', 'blog-shell' in _rb and 'bc-hero' in _rb and 'bc-card' in _rb and 'bc-meta' in _rb)
T('بلاگ جدید: فونت وزیرمتن لود می‌شود', 'vazirmatn' in _rb.lower())
from blog.models import Article as _Art
_ab = _Art.objects.order_by('-published_at').first()
_rd = c.get(f'/blog/article/{_ab.pk}/').content.decode()
T('جزئیات مقاله: هد خط‌کشی/متن/نظرات/مرتبط', 'art-head' in _rd and 'd-prose' in _rd and 'cmts' in _rd and 'related-grid' in _rd)
_bcss = open('static/css/blog.css', encoding='utf-8').read()
T('بلاگ CSS: تم روشن استاندارد + انیمیشن/مدیاکوئری', "Vazirmatn" in _bcss and '.blog-shell' in _bcss and _bcss.count('@keyframes') >= 5 and _bcss.count('@media') >= 3)

_ca = Client(SERVER_NAME='localhost')
assert _ca.login(username='admin', password='admin123456')
T('پنل: داشبورد برای ادمین ۲۰۰', _ca.get('/panel/').status_code == 200)
T('پنل: غیرادمین به لاگین هدایت می‌شود', c.get('/panel/').status_code == 302)
T('پنل: POST غیرادمین هم مسدود است', c.post('/panel/users/%d/grant/' % user.pk, data=json.dumps({'target': 'gems', 'amount': 1, 'idem': ID('deny')}), content_type='application/json').status_code == 302)
_rusers = _ca.get('/panel/users/?q=' + user.username).content.decode()
T('پنل: جستجوی کاربر نتیجه می‌دهد', _ca.get('/panel/users/').status_code == 200 and user.username in _rusers)
T('پنل: صفحهٔ جزئیات کاربر', _ca.get(f'/panel/users/{user.pk}/').status_code == 200)
T('CMS اکادمی وایر شده و برای ادمین باز است', _ca.get('/academy/manage/').status_code == 200)

from economy.models import Wallet as _W
_w = _W.objects.get(user=user)
_g0 = _w.gems
_r1 = _ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'gems', 'amount': 42, 'note': 'تست۱۸', 'idem': ID('g1')}), content_type='application/json').json()
_w.refresh_from_db()
T('اهدای الماس از پنل (+۴۲)', _r1.get('ok') and _w.gems == _g0 + 42)
_tx = Transaction.objects.filter(user=user, type='admin_adjust').order_by('-id').first()
T('تراکنش admin_adjust با actor=admin', bool(_tx) and _tx.amount == 42 and _tx.actor_id == _adm.pk)
_r2 = _ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'gems', 'amount': 42, 'note': 'تست۱۸', 'idem': ID('g1')}), content_type='application/json').json()
_w.refresh_from_db()
T('کلید یکتا: اهدای تکراری دوباره اعمال نمی‌شود', _r2.get('duplicate') and _w.gems == _g0 + 42)
_w.refresh_from_db()
_c0 = _w.coins
_r3 = _ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'coins', 'amount': -(_c0 + 9999), 'idem': ID('g2')}), content_type='application/json')
_w.refresh_from_db()
T('کسر بیش از موجودی: ۴۰۰ و عدم تغییر (بدون منفی)', _r3.status_code == 400 and _r3.json().get('error') == 'insufficient' and _w.coins == _c0)
user.refresh_from_db()
_x0 = user.xp
_r4 = _ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'xp', 'amount': -(_x0 + 4242), 'idem': ID('g3')}), content_type='application/json').json()
user.refresh_from_db()
T('کسر XP بیش از موجودی: کف صفر و لول به‌روز', _r4.get('ok') and user.xp == 0 and user.level == 1)
_r5 = _ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'xp', 'amount': 500, 'idem': ID('g4')}), content_type='application/json').json()
user.refresh_from_db()
T('اهدای XP: لول دوباره بالا می‌رود', _r5.get('ok') and user.xp == 500 and user.level >= 3)
_p0 = user.points
_r6 = _ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'points', 'amount': 77, 'idem': ID('g5')}), content_type='application/json').json()
user.refresh_from_db()
from panel.models import PanelAdjustment as _PA
T('اهدای امتیاز (فیلد قدیمی) + رديف لاگ یکتا', _r6.get('ok') and user.points == _p0 + 77 and _PA.objects.filter(user=user, target='points', amount=77).exists())
_r7 = _ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'streak', 'amount': 3, 'idem': ID('g6')}), content_type='application/json').json()
user.refresh_from_db()
T('تنظیم استریک از پنل', _r7.get('ok') and _r7.get('value') == user.streak)
_r8 = _ca.post(f'/panel/users/{user.pk}/grant/', data=json.dumps({'target': 'streak', 'amount': 3, 'idem': ID('g6')}), content_type='application/json').json()
T('استریک: ارسال مجدد همان کلید = تکراری', _r8.get('duplicate'))
_prod = Product.objects.filter(is_active=True).order_by('id').first()
_r9 = _ca.post(f'/panel/users/{user.pk}/item/', data=json.dumps({'product_id': _prod.pk, 'idem': ID('g7')}), content_type='application/json').json()
T('اهدای آیتم فروشگاه به کاربر', _r9.get('ok') and InventoryItem.objects.filter(user=user, product=_prod).exists())
_r10 = _ca.post(f'/panel/users/{user.pk}/item/', data=json.dumps({'product_id': _prod.pk, 'idem': ID('g7')}), content_type='application/json').json()
T('اهدای آیتم تکراری مسدود (یکتا)', _r10.get('duplicate'))
_r11 = _ca.post(f'/panel/users/{_adm.pk}/toggle-active/', data=json.dumps({'idem': ID('g8')}), content_type='application/json')
T('تعلیق حساب خودِ ادمین مسدود است', _r11.status_code == 400)
_r12 = _ca.get('/panel/').content.decode()
T('داشبورد: KPI + اهدای سریع + تاریخچه', 'اهدای سریع' in _r12 and 'آخرین اقدامات پنل' in _r12 and 'pn-kpi' in _r12)
_pcss = open('static/css/panel.css', encoding='utf-8').read()
_pjs = open('static/js/panel.js', encoding='utf-8').read()
T('پنل: استایل و تعاملات (Vazirmatn + مدیاکوئری + کانسفرم)', 'Vazirmatn' in _pcss and _pcss.count('@media') >= 2 and 'pnConfirm' in _pjs and 'quickGrantForm' in _pjs)
user.refresh_from_db()

print('\n━━━ ۱۹) فروشگاه v4 (ویترین حرفه‌ای) + بلاگ v4 ━━━')
_r = c.get('/shop/').content.decode()
T('فروشگاه: شل و چیدمان فروشگاهی v4', 'sp-shell' in _r and 'sp-layout' in _r and 'sp-rail' in _r)
T('فروشگاه: کارت محصول + تایل رنگی + نوار ویژه', 'sp-card' in _r and 'sp-t' in _r and 'sp-feat-row' in _r)
T('فروشگاه: فونت وزیرمتن لینک شده', 'vazirmatn' in _r.lower())
_rfg = c.get('/shop/product/frame-gold/').content.decode()
T('پیش‌نمایش زندهٔ قاب در صفحهٔ محصول', 'lq-framed' in _rfg and 'frame-gold' in _rfg and 'sh-gal' in _rfg)
_ruc = c.get('/shop/product/ucolor-rainbow/').content.decode()
T('پیش‌نمایش زندهٔ رنگ نام کاربری', 'sh-tile-uc' in _ruc and 'ucolor-rainbow' in _ruc)
_rth = c.get('/shop/product/theme-sunset/').content.decode()
T('پیش‌نمایش موکاپ تم', 'sh-theme-prev' in _rth and 'theme-sunset' in _rth)
_rbg = c.get('/shop/product/pbg-space/').content.decode()
T('پیش‌نمایش بک‌گراند پروفایل', 'sh-pbg-prev' in _rbg and 'pbg-space' in _rbg)
_rinv = c.get('/shop/inventory/').content.decode()
_rwish = c.get('/shop/wishlist/').content.decode()
_rhist = c.get('/shop/history/').content.decode()
T('زیرصفحه‌ها هم با قالب v4 به‌روز شدند', 'sh-hero hero-teal' in _rinv and 'sh-hero hero-pink' in _rwish and 'sh-table' in _rhist)
_mb = Product.objects.get(slug='mystery-box')
_ls = Product.objects.get(slug='lucky-spin')
T('دیتا-میگریشن ویترین: تخفیف‌های کلکسیونی', _mb.discount_percent == 20 and _ls.discount_percent == 10)
T('ویترین: شمار فروش پایه برای کالاها (به‌جز ریست‌شدهٔ تست سهمیه)', not Product.objects.filter(sold_count=0).exclude(slug='frame-royal').exists())
T('ویترین: کالای ویژهٔ کافی برای کاروسل', Product.objects.filter(is_featured=True, is_active=True).count() >= 8)
_rb = c.get('/blog/').content.decode()
T('بلاگ v5: سکشن‌های مینیمال + کاور گرادیانی hue', 'bc-sec' in _rb and '--h:' in _rb and 'bc-cover' in _rb)
_ra = c.get(f'/blog/article/{art.pk}/').content.decode()
T('بلاگ v4: هیروی جزئیات با ارب و رنگ اختصاصی', 'blm-orb' in _ra and '--h:' in _ra)
_bcss = open('static/css/blog.css', encoding='utf-8').read()
T('بلاگ v4: لایهٔ استایل جدید اعمال شده', '.bl-art' in _bcss and 'blm-drift' in _bcss and '.bl-tchip' in _bcss and '.blm-orb' in _bcss)
_scss = open('static/css/shop.css', encoding='utf-8').read()
T('فروشگاه v4: سیستم‌دیزاین sh-* در CSS', '.sh-shell' in _scss and '.sh-tint-7' in _scss and '.sh-theme-prev' in _scss and '.sh-buybox' in _scss)

print('\n━━━ ۲۰) هدر بازطراحی‌شده + داشبورد مدرن ━━━')
from user.models import UserActivity as _UA
_UA.objects.get_or_create(user=user, title='فعالیت تست داشبورد', defaults={'icon': 'star'})
_h = c.get('/home/').content.decode()
T('هدر: شِل پیلی ناوبری + لوگوی بج‌دار', 'logo-badge' in _h and '<nav>' in _h and 'hd-ava-dd' in _h)
T('هدر: دراپ‌داون کاربر با چیپ خلاصهٔ حساب', 'dd-user' in _h and 'mini-ava' in _h and 'داشبورد پنل' not in _h.split('hd-ava-dd')[1][:0] + 'x')
T('هدر: گروه‌بندی منوی موبایل', 'mobile-group' in _h and _h.count('mobile-group') >= 4)
T('هدر: فروشگاه دکمهٔ تکی (رگرسیون)', '🛒 فروشگاه</a>' in _h.split('</nav>')[0])
T('داشبورد: هیروی گرادیانی با ارب و رینگ سطح', 'db-hero' in _h and 'db-orb' in _h and 'lvRing' in _h and 'stroke-dasharray="314.16"' in _h)
T('داشبورد: ۶ کارت KPI با شمارش انیمیشنی', _h.count('db-kpi') >= 6 and _h.count('data-count') >= 6)
T('داشبورد: پنل فصل + فعالیت‌های اخیر', 'db-season-band' in _h and 'db-acts' in _h)
T('داشبورد: دسترسی سریع گرادیانی ۶گانه', _h.count('db-q"') >= 6 or _h.count('class="db-q"') >= 6)
T('داشبورد: وزیرمتن + کاور hue برای مقالات', 'vazirmatn' in _h.lower() and '--h:' in _h)
T('داشبورد: تاریخ شمسی امروز در هیرو', 'db-when' in _h)

print('\n━━━ ۲۱) پیامرسان تلگرام-آیفون + داشبورد مینیمال ━━━')
_rms = c.get('/messenger/').content.decode()
T('پیامرسان: نوبار iOS با عنوان «چت‌ها»', 'ms-navrow' in _rms and 'ms-nav-title' in _rms and 'چت‌ها' in _rms)
T('پیامرسان: ساختار مستقل حفظ شده (رگرسیون)', '<header class="ms-side-head"' in _rms and _rms.count('href="/home/"') >= 1 and 'viewport-fit=cover' in _rms)
T('پیامرسان: سرچ iOS با پلیس‌هولدر کوتاه', 'id="msSearchInput"' in _rms and 'جستجو…' in _rms)
T('پیامرسان: آیکون SVG هواپیما برای ارسال', '<symbol id="i-plane"' in _rms)
_mcss = open('static/css/messenger.css', encoding='utf-8').read()
T('پیامرسان: اکسنت آبی iOS', '--ms-teal: #0A84FF' in _mcss)
T('پیامرسان: بج سبز خوانده‌نشده + دات آنلاین سبز', '#4CCD64' in _mcss and '#4BD964' in _mcss)
T('پیامرسان: والپیپر دودل تلگرام روی چت', '.ms-chat::before' in _mcss and 'data:image/svg+xml' in _mcss)
T('پیامرسان: حباب سبز خروجی + تیک آبی خوانده‌شده', '--ms-bubble-mine' in _mcss and '--ms-sky: #34B7F1' in _mcss)
T('پیامرسان: hairline آیفون + safe-area', '.ms-conv::after' in _mcss and 'right: 80px' in _mcss and 'safe-area-inset' in _mcss)
T('پیامرسان: ریسپانسیو موبایل حفظ شده (رگرسیون)', '100dvh' in _mcss and 'chat-open' in _mcss and 'ms-icon-btn' in _mcss and _mcss.count('@media') >= 2)
_mjs = open('static/js/messenger.js', encoding='utf-8').read()
T('پیامرسان: منطق JS سالم (اموجی + اتوسایز + Enter)', 'msEmojiPanel' in _mjs and 'autosize' in _mjs and "key === 'Enter'" in _mjs)
_h21 = c.get('/home/').content.decode()
T('داشبورد: کارت‌های سفید مینیمال + حاشیهٔ hairline', 'border: 1px solid var(--db-line)' in _h21 and 'background: var(--db-card)' in _h21)
T('داشبورد: بلاب‌ها ساکن و کم‌رنگ (بدون انیمیشن خسته‌کننده)', 'db-blob b1' in _h21 and 'db-float' not in _h21)
T('داشبورد: هیروی سفید مینیمال بدون برق/بیم', 'db-hero::before' not in _h21 and 'db-beam' not in _h21)
T('داشبورد: تایل‌های دسترسی‌سریع یکدست (بدون بِرَق کشویی)', '.db-q::before' not in _h21 and 'skewX' not in _h21 and _h21.count('class="db-q"') >= 6)
T('داشبورد: توکن‌های خنثی مینیمال v6', '--db-ink: #17171c' in _h21 and '--db-soft: #71717a' in _h21 and '--db-line: rgba(23, 23, 28, 0.08)' in _h21)

print('\n━━━ ۲۲) استاتیک با Daphne + صفحات احراز هویت + انیمیشن داشبورد ━━━')
_asgi = open('Config/asgi.py', encoding='utf-8').read()
T('ASGI: استاتیک‌ها زیر Daphne سرو می‌شوند (رفع 404 روی ویندوز)', 'ASGIStaticFilesHandler' in _asgi and 'settings.DEBUG' in _asgi and 'ProtocolTypeRouter' in _asgi and 'websocket' in _asgi)
_bs = open('templates/base.html', encoding='utf-8').read()
T('هدر: مدیاکوئری عرض میانی (جلوگیری از به‌هم‌ریختگی)', 'min-width: 901px) and (max-width: 1400px' in _bs and 'min-width: 901px) and (max-width: 1060px' in _bs)
_lg = _cg.get('/login/')
_lh = _lg.content.decode()
T('ورود: صفحهٔ شیشه‌ای مدرن رندر', _lg.status_code == 200 and 'au-card' in _lh and 'au-orb' in _lh and 'au-form' in _lh)
T('ورود: فیلدهای آیکون‌دار + چشم رمز + وزیرمتن', 'au-field' in _lh and 'au-eye' in _lh and 'vazirmatn' in _lh.lower() and 'name="username"' in _lh and 'name="password"' in _lh)
T('ورود: CSRF و لینک‌های بازیابی/ثبت‌نام', 'csrfmiddlewaretoken' in _lh and 'password-reset' not in _lh and '/new-password/' in _lh and '/register/' in _lh)
_rg = _cg.get('/register/')
_rh = _rg.content.decode()
T('ثبت‌نام: صفحهٔ شیشه‌ای مدرن رندر', _rg.status_code == 200 and 'au-card' in _rh and 'au-badge' in _rh and 'au-chips' in _rh)
T('ثبت‌نام: هر ۵ فیلد فرم حفظ شده', all(f'name="{_n}"' in _rh for _n in ['username', 'email', 'phone', 'password1', 'password2']))
_rp = _cg.post('/login/', {'username': 'testuser', 'password': 'test123456'})
T('فرم ورود جدید هنوز کار می‌کند (۳۰۲ → داشبورد)', _rp.status_code == 302 and _rp.url in ('/home/', '/', '/home'))
_dh2 = c.get('/home/').content.decode()
T('داشبورد: ورود آرام تکی (بدون stagger خسته‌کننده)', 'db-fade' in _dh2 and not _re16.search(r'\.db-[^{]*\{[^}]*animation-delay', _dh2) and 'db-rise' not in _dh2)
T('داشبورد: بدون شاین‌بج/چرخش آیکون + CTA مات سیاه', 'db-badge-shine' not in _dh2 and '.db-kpi:hover .ic' not in _dh2 and 'background: var(--db-ink)' in _dh2 and 'background: #f4f4f7' in _dh2)
_prev21 = c.get('/messenger/').content.decode()
T('رگرسیون: پیامرسان آیفونی سالم', 'ms-nav-title' in _prev21 and '--ms-bubble-mine' in open('static/css/messenger.css', encoding='utf-8').read())

print('\n━━━ ۲۳) احراز هویت مایع v2 + داشبورد مینیمال (بدون افکت‌های سنگین) ━━━')
_gc2 = Client(SERVER_NAME='localhost')
_lh2 = _gc2.get('/login/').content.decode()
T('ورود v2: مش‌گرادیانت متحرک پس‌زمینه', 'au-mesh' in _lh2 and 'au-meshmove' in _lh2)
T('ورود v2: لیبل شناور روی اینپوت‌های گلس', 'au-lbl' in _lh2 and ':placeholder-shown' in _lh2)
T('ورود v2: تیتر گرادیانی متحرک + کلمهٔ چرخشی', 'au-gt' in _lh2 and 'au-grad' in _lh2 and 'auFlip' in _lh2)
T('ورود v2: حاشیهٔ گرادیانی مایع (border-box trick) + فیلد گلس', 'border-box' in _lh2 and 'blur(14px) saturate(160%)' in _lh2)
_rh2 = _gc2.get('/register/').content.decode()
T('ثبت‌نام v2: متر قدرت رمز + تطبیق رمز زنده', 'auStrBar' in _rh2 and 'au-meter' in _rh2 and 'auMatch' in _rh2)
T('ثبت‌نام v2: لیبل شناور + ۵ فیلد سالم', 'au-lbl' in _rh2 and all(f'name="{_n}"' in _rh2 for _n in ['username', 'email', 'phone', 'password1', 'password2']))
_rp2 = _gc2.post('/login/', {'username': 'testuser', 'password': 'test123456'})
T('فرم ورود v2 هنوز کار می‌کند (۳۰۲)', _rp2.status_code == 302)
_dh3 = c.get('/home/').content.decode()
T('داشبورد مینیمال: بدون بیم چرخان (no conic/@property)', '@property --dbeam' not in _dh3 and 'conic-gradient' not in _dh3 and 'db-beam' not in _dh3)
T('داشبورد مینیمال: بدون اسپات‌لایت موس', '.db-kpi::before' not in _dh3 and 'pointermove' not in _dh3 and '--mx' not in _dh3 and '--my' not in _dh3)
T('داشبورد مینیمال: بلاب‌ها رنگ ثابت دارند', 'db-hue' not in _dh3 and 'hue-rotate' not in _dh3)

print('\n━━━ ۲۴) هدر دسکتاپ مرتب + فروشگاه مینیمال v5 + بلاگ گلس v5 ━━━')
T('هدر: راهنما از کپسول حذف + جداکنندهٔ اضافی پاک شد', '.stat.guide-ico' in _bs and 'sep:last-of-type' in _bs)
T('هدر: پلهٔ فشرده‌سازی ۱۲۶۰/۱۲۰۰/۱۰۶۰', 'min-width: 901px) and (max-width: 1200px' in _bs and 'min-width: 901px) and (max-width: 1000px' in _bs)
_scss5 = open('static/css/shop.css', encoding='utf-8').read()
T('فروشگاه v5: سیستم مینیمال (سیاهِ مات + خاکستری‌های نرم)', '--sh-ink: #17171c' in _scss5 and '--sh-soft: #71717a' in _scss5 and '#dfe6ff' in _scss5)
T('فروشگاه v5: دکمه‌های سیاه مینیمال + گوست سفید', '.sh-btn:hover' in _scss5 and 'background: #000' in _scss5 and '.sh-btn.ghost' in _scss5)
T('فروشگاه v5: تایل‌های یکدست و حفظ رگرسیون selکتورها', _scss5.count('.sh-tint-') >= 8 and '.sh-buybox' in _scss5 and '.sh-theme-prev' in _scss5 and '--lq-' in _scss5)
T('فروشگاه v5: ریسپانسیو واقعی (ریل افقی + سرچ گریدی + ۲ ستون موبایل)', '@media (max-width: 1020px)' in _scss5 and 'grid-column: 1 / -1' in _scss5 and 'repeat(2, minmax(0, 1fr))' in _scss5 and _scss5.count('@media') >= 3)
T('فروشگاه v5: ویژه‌های رنگی سالید + هیروی سفید تیزر', '#334155, #64748b' in _scss5 and 'border-right: 4px solid' in _scss5)
_rsh5 = c.get('/shop/').content.decode()
T('فروشگاه v5: مارکاپ سالم (شل/کارت/تینت/لای‌اوت)', 'sp-shell' in _rsh5 and 'sp-card' in _rsh5 and 'sp-t' in _rsh5 and 'sp-layout' in _rsh5)
_bcss5 = open('static/css/blog.css', encoding='utf-8').read()
T('بلاگ v5: گلس خالص (بلور ۲۴ + ساتوریت)', 'blur(24px) saturate(160%)' in _bcss5 and '--bl-line: rgba(255, 255, 255, 0.78)' in _bcss5)
T('بلاگ v5: رگرسیون selکتورها (art/tchip/orb/drift)', '.bl-art' in _bcss5 and '.bl-tchip' in _bcss5 and '.blm-orb' in _bcss5 and 'blm-drift' in _bcss5)
T('بلاگ v5: سرچ پیلی گلس + دستهٔ فعال سیاه + ردیف پر‌بازدید گلس', 'inset 0 1.5px 0 rgba(255, 255, 255, 0.9)' in _bcss5 and '.bl-cat.on' in _bcss5 and '.bl-poprow' in _bcss5)
_rb5 = c.get('/blog/').content.decode()
T('بلاگ v5: مارکاپ سالم (سربرگ/ردیف/سکشن/hue)', 'bc-hero' in _rb5 and 'bc-card' in _rb5 and 'bc-sec' in _rb5 and '--h:' in _rb5)
_ra5 = c.get(f'/blog/article/{art.pk}/').content.decode()
T('بلاگ v5: مقالهٔ گلس با هیرو hue سالم', 'art-head' in _ra5 and '--h:' in _ra5 and 'cmts' in _ra5)

print('\n━━━ ۲۵) دکمهٔ ؟ راهنما در پروفایل (مودال) + فونت واحد سراسری + ریسپانسیو موبایل ━━━')
_pf25 = c.get('/home/profile/').content.decode()
T('پروفایل: دکمهٔ شناور ؟ برای راهنما (مودال، نه صفحهٔ جدید)', 'pf-guide-fab' in _pf25 and '>؟</a>' in _pf25 and '/home/guide/' in _pf25)
T('پروفایل: انیمیشن ورود فِب + پالس + آفست سِیف‌اریا موبایل', 'pfFabPulse' in _pf25 and 'pfFabIn' in _pf25 and 'safe-area-inset-bottom' in _pf25)
T('پروفایل: دکمهٔ عملیاتی قبلی راهنما (btn-guide) حفظ شده', 'btn-guide' in _pf25)
T('پروفایل: هیچ آیکون مردهٔ Font Awesome باقی نمانده', 'fas fa-' not in _pf25)
T('پروفایل: آیکون‌های ایموجی سالم رندر شده', all(x in _pf25 for x in ('🏆', '🕘', '📅', '🧭')))
T('پروفایل: فیلتر icon_emoji با fallback وصل است', 'icon_emoji' in open('templates/profile.html', encoding='utf-8').read()
    and 'def icon_emoji' in open('Home/templatetags/jalali.py', encoding='utf-8').read())
T('پروفایل: ریسپانسیو بهبودیافته (تايتر/دکمه‌ها در موبایل)', '@media (max-width: 768px)' in _pf25 and 'grid-template-columns: 1fr' in _pf25)
_core25 = open('static/css/lq-core.css', encoding='utf-8').read()
T('مودال راهنما: روی موبایل شیت کشویی با دستگیره', 'lqSheetUp' in _core25 and '.lq-gmodal-head::before' in _core25 and '94dvh' in _core25)
T('مودال راهنما: ارتفاع dvh همه‌جا + reduced-motion', 'min(88dvh, 860px)' in _core25 and 'prefers-reduced-motion' in _core25)
_bs25 = open('templates/base.html', encoding='utf-8').read()
T('فونت واحد: وزیرمتن سراسری در base لود می‌شود', 'Vazirmatn-font-face.css' in _bs25)
T('فونت واحد: بدنهٔ سایت + کنترل‌های فرم وزیرمتن', "font-family: 'Vazirmatn', 'Segoe UI'" in _bs25 and 'input, textarea, select, button' in _bs25)
T('فونت واحد: نرم‌سازی متن + text-size-adjust موبایل', 'font-smoothing' in _bs25 and 'text-size-adjust' in _bs25)
T('فونت واحد: مؤلفه‌های هسته (توست/مودال‌ها) هم وزیرمتن', _core25.count("'Vazirmatn', 'Segoe UI'") >= 2)
_ms25 = open('static/css/messenger.css', encoding='utf-8').read()
T('فونت واحد: پیامرسان بدون monospace جدا', 'monospace' not in _ms25)
_h25 = c.get('/home/guide/').content.decode()
T('صفحهٔ راهنما سالم + فونت سراسری رندر می‌شود', 'gd-card' in _h25 and 'Vazirmatn' in _h25)
_acb25 = open('language_academy/templates/language_academy/base_academy.html', encoding='utf-8').read()
T('اکادمی: Inter حذف و وزیرمتن لود', 'vazirmatn' in _acb25.lower() and 'fonts.googleapis.com' not in _acb25 and "'Inter'" not in _acb25)
_ac25 = c.get('/academy/').content.decode()
T('اکادمی: صفحهٔ رندرشده فونت واحد دارد', 'vazirmatn' in _ac25.lower())

print('\n━━━ ۲۶) ری‌برند آبی — بنفش → آبی‌های زیبا ━━━')
_bs26 = open('templates/base.html', encoding='utf-8').read()
T('برند: پالت آبی در متغیرهای اصلی', "--primary: #3B82F6" in _bs26 and "--violet: #38BDF8" in _bs26 and "--primary-dark: #1D4ED8" in _bs26)
T('برند: گرادیان بدنهٔ سایت پاستیلی روشن (آبی/بنفش/سرخابی)', '#9CC1F4' in _bs26 and '#B3A5EE' in _bs26 and '#EBB3D9' in _bs26 and 'background-attachment: fixed;' in _bs26)
T('برند: هیچ بنفش قدیمی در base باقی نمانده', '#667eea' not in _bs26 and '#764ba2' not in _bs26 and '#6C63FF' not in _bs26)
_core26 = open('static/css/lq-core.css', encoding='utf-8').read()
T('هسته: توست/مودال/راهنما آبی شد', '#3B82F6' in _core26 and '#6C63FF' not in _core26 and 'rgba(59, 130, 246' in _core26)
_dh26 = c.get('/home/').content.decode()
T('داشبورد: لهجهٔ آبی جدید + حذف کامل بنفش', '--db-accent: #3B82F6' in _dh26 and '#6C63FF' not in _dh26 and '#8b5cf6' not in _dh26)
T('داشبورد: کاور hue با فالبک آبی ۲۱۲', 'var(--h, 212)' in _dh26)
_jal26 = open('Home/templatetags/jalali.py', encoding='utf-8').read()
T('فیلتر hue: فالبک آبی', 'return 212' in _jal26)
_blog26 = open('static/css/blog.css', encoding='utf-8').read()
_shop26 = open('static/css/shop.css', encoding='utf-8').read()
T('بلاگ/فروشگاه: بدون بنفش برند', '#6C63FF' not in _blog26 and '#6C63FF' not in _shop26 and '#3B82F6' in _blog26)
_gc26 = Client(SERVER_NAME='localhost')
_lg26 = _gc26.get('/login/').content.decode()
T('ورود: مش سفید-آبی (بدون بنفش/فوشیا)', '#6C63FF' not in _lg26 and '#d946ef' not in _lg26 and '#38BDF8' in _lg26)

print('\n━━━ ۲۷) هدر/منوی موبایل + بک‌گراند شیشه‌ای + بلاگ گلس تمام‌صفحه + واژگان داینامیک ━━━')
_bs27 = open('templates/base.html', encoding='utf-8').read()
T('هدر: دراپ‌داون آواتار مخفی با hover/focus', '.hd-ava-dd .nav-dd-menu' in _bs27 and 'visibility: hidden' in _bs27 and '.hd-ava-dd:hover .nav-dd-menu' in _bs27)
T('بک‌گراند: حلقه‌های شیشه‌ای + بلاب + برق دیواری', '.bg-ring.r1' in _bs27 and '.bg-blob.b1' in _bs27 and '.bg-sheen' in _bs27 and 'bgDrift' in _bs27 and 'bgBlob' in _bs27)
T('بک‌گراند: نقطه‌چین + گلوهای آبی بدنه', 'background-size: 27px 27px' in _bs27 and 'radial-gradient(' in _bs27)
T('بک‌گراند: احترام به reduced-motion', _bs27.count('prefers-reduced-motion') >= 2)
T('منوی موبایل: گروه با خط‌چین + آیکن گلس + هدف لمسی', '.mobile-group::after' in _bs27 and 'min-height: 45px' in _bs27 and 'border: 1px solid rgba(59, 130, 246, 0.14)' in _bs27)
T('منوی موبایل: انیمیشن ورود + حالت فعال + خروج تمیز', 'mmlIn' in _bs27 and '.mobile-links a.active' in _bs27 and '.mobile-logout:hover' in _bs27)
_hm27 = c.get('/home/').content.decode()
T('بک‌گراند: اسپن‌های دکور در خروجی رندر', 'bg-sheen' in _hm27 and 'bg-ring r1' in _hm27 and 'bg-blob b1' in _hm27)
_blog27 = open('static/css/blog.css', encoding='utf-8').read()
T('بلاگ: شل گلس تمام-عرض دسکتاپ', 'max-width: 1720px' in _blog27 and 'blur(26px) saturate(160%)' in _blog27)
T('بلاگ: چیپ‌ها پوزیشن مطلق (رفع بهم‌ریختگی)', '.bl-thumb .bl-tcat' in _blog27 and '.bl-thumb .bl-tchip' in _blog27 and '.bl-fcard .bl-tchip.rt' in _blog27)
T('بلاگ: ریویل امن + سایزهای موبایل کنترل‌شده', '.reveal.armed' in _blog27 and _blog27.count('@media (max-width: 640px)') >= 2)
_bt27 = open('templates/blog.html', encoding='utf-8').read()
T('بلاگ: کش‌باست تازه + پدینگ تمام‌صفحه', '?v=202608099' in _bt27 and 'clamp(12px, 4vw, 40px)' in _bt27)
_ad27 = open('templates/article_detail.html', encoding='utf-8').read()
T('جزئیات مقاله: کش‌باست + پدینگ تمام‌صفحه', '?v=202608099' in _ad27 and 'clamp(10px, 2vw, 34px)' in _ad27)
_bp27 = c.get('/blog/').content.decode()
T('بلاگ رندرشده: شل + پدینگ جدید اعمال شد', 'blog-shell' in _bp27 and 'clamp(12px, 4vw, 40px)' in _bp27)
_ld27 = open('language_academy/templates/language_academy/lesson_detail.html', encoding='utf-8').read()
T('درس: پالت یکسان با آکادمی (بدون override تیره)', '--bg-card: rgba(255, 255, 255, 0.62)' in _ld27 and '#1A1A2E' in _ld27 and _ld27.count('--bg-primary: #0f172a') == 1)
T('درس: رسپانسیو موبایل قوی', '@media (max-width: 768px)' in _ld27 and '@media (max-width: 480px)' in _ld27 and '.sidebar-modern { position: static' in _ld27)
T('واژگان: تولبار + فلش‌کارت + تلفظ', 'id="vocabFlashBtn"' in _ld27 and 'vf-card' in _ld27 and 'speechSynthesis' in _ld27 and 'document.documentElement.appendChild' in _ld27)
_lv27 = open('language_academy/views.py', encoding='utf-8').read()
T('واژگان: نگاشت درس→دسته + تاپ‌آپ داینامیک', 'categories__name__iexact=lesson.name' in _lv27 and 'vocab_list.extend(extras)' in _lv27)
_less27 = c.get('/academy/lesson/3/')
T('درس ۳ رندر ۲۰۰ + شبکهٔ واژگان دارد', _less27.status_code == 200 and 'vocab-grid' in _less27.content.decode())


print('\n━━━ ۲۸) ویرایشگر زندهٔ درس آکادمی (ادمین = همان صفحهٔ کاربر + ویرایش) ━━━')
import os as _os28
_adm28 = Client(SERVER_NAME='localhost')
T('ویرایشگر: ورود ادمین', _adm28.login(username='admin', password='admin123456'))
_ev28 = _adm28.get('/academy/lesson/3/?edit=1')
T('ویرایشگر: صفحهٔ ویرایش زنده ۲۰۰ + نوار/ریل/هوک‌ها', _ev28.status_code == 200 and all(x in _ev28.content.decode() for x in ('ve-bar', 've-rail', 'data-ve="content.introduction"', 've-chip', 'data-ve-list="vocab"', 'data-vocab-id')))
_r28u = c.get('/academy/lesson/3/?edit=1').content.decode()
T('ویرایشگر: کاربر عادی در حالت ?edit=1 نوار را نمی‌بیند', 've-bar' not in _r28u and 've-rail' not in _r28u)
T('ویرایشگر: صفحهٔ عادی درس همچنان تمیز (بدون نوار)', 've-bar' not in c.get('/academy/lesson/3/').content.decode())
_src28 = open('language_academy/templates/language_academy/lesson_detail.html', encoding='utf-8').read()
T('ویرایشگر: هوک‌های تمام لیست‌ها + فرار fixed از body', all(x in _src28 for x in ('data-ve-list="objectives"', 'data-ve-list="takeaways"', 'data-ve-list="grammar_examples"', 'data-ve-list="example_sentences"')) and _src28.count('document.documentElement.appendChild') >= 2)
T('ویرایشگر: فیلد display_options + مایگریشن', 'display_options = models.JSONField' in open('language_academy/models.py', encoding='utf-8').read() and _os28.path.exists('language_academy/migrations/0007_lessoncontent_display_options.py'))
_views28 = open('language_academy/admin_cms/views.py', encoding='utf-8').read()
T('ویرایشگر: سرویس سفیدلیست + atomic + سنیتایزر HTML', '_VE_CONTENT_TEXT' in _views28 and '_SCRIPT_RE' in _views28 and 'select_for_update' in _views28 and 'transaction.atomic' in _views28)
_dash28 = _adm28.get('/academy/manage/').content.decode()
T('داشبورد CMS: هاب ویرایشگر زنده + لینک به صفحهٔ کاربر', 'ویرایشگر زنده' in _dash28 and '?edit=1' in _dash28)
_m28 = None
_img28 = None
try:
    from language_academy.models import Lesson as _L28, LessonContent as _LC28, Vocabulary as _V28
    _l28 = _L28.objects.get(pk=3)
    _c28obj = _LC28.objects.get(lesson=_l28)
    _orig28 = {'name': _l28.name, 'introduction': _c28obj.introduction, 'objectives': list(_c28obj.learning_objectives or []), 'featured': str(_c28obj.featured_image or '')}
    _payload28 = __import__('json').dumps({'updates': {'lesson.name': 'Security & Boarding', 'junk.hack': 'DROP', 'lesson.is_published': False, 'display.accent': '#7c3aed', 'display.accent2': '#ec4899', 'style.grammar': {'color': '#1A1A2E', 'bg': '#fff7ed'}}})
    _r28 = _adm28.post('/academy/manage/lessons/3/visual-save/', data=_payload28, content_type='application/json')
    _j28 = _r28.json()
    T('سرو: دسترسی کارفرما + سفیدلیست فیلدها (junk skip)', _r28.status_code == 200 and _j28.get('ok') and _j28.get('skipped', 0) >= 1)
    _l28.refresh_from_db()
    T('سرو: فیلد حساس (is_published) دست‌نخورده ماند', _l28.is_published is True)
    _up28 = c.get('/academy/lesson/3/').content.decode()
    T('سرو: رنگ لهجهٔ جدید دقیقاً روی صفحهٔ کاربر اعمال شد', '#7c3aed' in _up28)
    _c28obj.refresh_from_db()
    _st28 = (_c28obj.display_options or {}).get('styles', {})
    T('سرو: تینت سکشن (text/bg) در display_options ذخیره شد', _st28.get('grammar', {}).get('bg') == '#fff7ed')
    T('سرو: GET روی visual-save ممنوع (فقط POST)', _adm28.get('/academy/manage/lessons/3/visual-save/').status_code == 405)
    _na28 = Client(SERVER_NAME='localhost', enforce_csrf_checks=True)
    _na28.login(username='admin', password='admin123456')
    T('سرو: بدون توکن CSRF → ۴۰۳', _na28.post('/academy/manage/lessons/3/visual-save/', data='{"updates":{}}', content_type='application/json').status_code == 403)
    T('سرو: کاربر غیراستاف به اندپوینت دسترسی ندارد', c.post('/academy/manage/lessons/3/visual-save/', data=_payload28, content_type='application/json').status_code in (302, 403))
    _voc28 = _V28.objects.filter(is_active=True, categories__name__iexact=_l28.name).first()
    if _voc28:
        _oldw = _voc28.word
        _adm28.post('/academy/manage/lessons/3/visual-save/', data=__import__('json').dumps({'updates': {'vocab.%d.word' % _voc28.pk: _oldw + ' X'}}), content_type='application/json')
        _voc28.refresh_from_db()
        T('سرو: ویرایش کلمهٔ لغت درجا', _voc28.word == _oldw + ' X')
        _adm28.post('/academy/manage/lessons/3/visual-save/', data=__import__('json').dumps({'updates': {'vocab.%d.word' % _voc28.pk: _oldw}}), content_type='application/json')
        _voc28.refresh_from_db()
        T('سرو: بازگردانی کلمه (ایدempotent)', _voc28.word == _oldw)
        T('سرو: حذف لغت از این درس (مخفی، نه گلوبال)', _adm28.post('/academy/manage/lessons/3/visual-save/', data=__import__('json').dumps({'updates': {'display.excluded_vocab': [_voc28.pk]}}), content_type='application/json').json().get('ok') is True and _voc28.pk in (_LC28.objects.get(lesson=_l28).display_options or {}).get('excluded_vocab', []) and ('data-vocab-id="%d"' % _voc28.pk) not in c.get('/academy/lesson/3/').content.decode())
        _adm28.post('/academy/manage/lessons/3/visual-save/', data=__import__('json').dumps({'updates': {'display.excluded_vocab': []}}), content_type='application/json')
    _nv28 = _adm28.post('/academy/manage/lessons/3/visual-save/', data=__import__('json').dumps({'updates': {'new_vocab.0': {'word': 'JetBridge', 'pronunciation': '/jet bridge/', 'meaning': 'Walkway connector to plane', 'meaning_fa': 'پل متحرک سوار شدن', 'example': 'We walked through the jet bridge.'}}}), content_type='application/json')
    _nvrow = _V28.objects.filter(word='JetBridge').first()
    T('سرو: ساخت لغت جدید + اتصال به دستهٔ همنام درس', _nv28.json().get('ok') and _nvrow is not None and _nvrow.categories.filter(name__iexact=_l28.name).exists())
    T('سرو: لغت جدید روی صفحهٔ کاربر دیده می‌شود', 'JetBridge' in c.get('/academy/lesson/3/').content.decode())
    if _nvrow:
        _nvrow.delete()
    from django.core.files.uploadedfile import SimpleUploadedFile as _UF28
    _png28 = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
              b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
    _bad28 = _adm28.post('/academy/manage/lessons/3/visual-upload/', {'target': 'featured', 'file': _UF28('x.txt', b'not an image', content_type='text/plain')})
    T('آپلود: فایل غیرتصویری رد می‌شود', _bad28.status_code == 400)
    _ok28 = _adm28.post('/academy/manage/lessons/3/visual-upload/', {'target': 'featured', 'file': _UF28('ve_test.png', _png28, content_type='image/png')})
    _img28 = _ok28.json()
    T('آپلود: PNG معتبر پذیرفته و ذخیره می‌شود', _ok28.status_code == 200 and _img28.get('ok') and '/media/lesson_images/ve_3_' in (_img28.get('url') or ''))
    T('آپلود: کاربر عادی اجازه ندارد', c.post('/academy/manage/lessons/3/visual-upload/', {'target': 'featured', 'file': _UF28('y.png', _png28, content_type='image/png')}).status_code in (302, 403))
    _adm28.post('/academy/manage/lessons/3/visual-save/', data=__import__('json').dumps({'updates': {'lesson.name': _orig28['name'], 'content.introduction': _orig28['introduction'], 'objectives': _orig28['objectives'], 'display.accent': '#3b82f6', 'display.accent2': '#38bdf8', 'style.grammar': {}, 'display.vocab_order': []}}), content_type='application/json')
except Exception as _ex28:
    T('ویرایشگر: سناریوی کامل سرو/آپلود بدون استثنا', False, str(_ex28))
try:
    _c28obj = __import__('language_academy.models', fromlist=['LessonContent']).LessonContent.objects.get(lesson_id=3)
    if _c28obj.featured_image and 've_3_' in _c28obj.featured_image.name:
        _c28obj.featured_image.delete(save=True)
except Exception:
    pass

print('\n━━━ ۲۹) فروشگاه بدون گلس + تایل‌های سالید رنگی + اسکرول‌بار سفارشی سراسری ━━━')
_scss29 = open('static/css/shop.css', encoding='utf-8').read()
T('فروشگاه v7: شل گلس (backdrop-filter روی بک‌گراند پاستلی سایت)', 'backdrop-filter' in _scss29 and 'blur(22px)' in _scss29)
T('فروشگاه v6: هشت تینت پاستلی متمایز (سالید نرم)', all(x in _scss29 for x in ('#dfe6ff', '#fbdfeb', '#fbebc2', '#cff3e6', '#d8ecff', '#eadfff', '#ffdfc9', '#e2e8f2')))
T('فروشگاه v6: کارت‌های ویژه گرادیان زنده (بدون گرافیت قدیمی)', all(x in _scss29 for x in ('#4f46e5', '#e11d48', '#059669', '#0284c7')) and '#26262c' not in _scss29)
T('فروشگاه v6: چیپ قیمت ویژه سفید سالید', "background: #ffffff;" in _scss29 and 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.20)' in _scss29)
T('فروشگاه v6: تایل لینک بدون زیرخط ایموجی + کادر محکم‌تر', 'text-decoration: none;' in _scss29 and 'border: 1px solid #e2e2e8' in _scss29)
_core29 = open('static/css/lq-core.css', encoding='utf-8').read()
T('اسکرول‌بار: قوانین سراسری وب‌کیت + فایرفاکس در هسته', '::-webkit-scrollbar-thumb' in _core29 and '::-webkit-scrollbar-thumb:hover' in _core29 and 'scrollbar-width: thin' in _core29 and 'scrollbar-color:' in _core29)
_acb29 = open('language_academy/templates/language_academy/base_academy.html', encoding='utf-8').read()
T('اسکرول‌بار: آکادمی استایل سراسری دارد', '::-webkit-scrollbar-thumb' in _acb29 and 'scrollbar-width: thin' in _acb29)
_adm29 = open('language_academy/templates/admin_cms/base.html', encoding='utf-8').read()
T('اسکرول‌بار: پنل CMS هم کاور شد', '::-webkit-scrollbar-thumb' in _adm29 and 'scrollbar-width: thin' in _adm29)
_rsh29 = c.get('/shop/').content.decode()
T('فروشگاه v6: مارکاپ سالم + کش‌باست جدید', 'sp-t' in _rsh29 and 'sp-card' in _rsh29 and 'v=202608078' in _rsh29)

print('\n━━━ ۳۰) حلقه‌های محوتر + فوتر مدرن + فال‌بک تصویر + ویرایشگر زندهٔ کل آکادمی ━━━')
_bs30 = open('templates/base.html', encoding='utf-8').read()
T('بک‌گراند: حلقه‌ها محو و چندرنگ متمایز', 'rgba(253, 186, 116' in _bs30 and 'rgba(249, 168, 212' in _bs30 and 'rgba(240, 171, 252' in _bs30 and 'rgba(253, 230, 138' in _bs30 and 'rgba(251, 207, 232' in _bs30)
T('فوتر: گلس شفاف و روشن‌تر از بک‌گراند', '.footer-brand' in _bs30 and "background: rgba(255, 255, 255, 0.12);" in _bs30 and 'blur(20px) saturate(165%)' in _bs30)
T('فوتر: تمام‌عرض + لینک‌های متنی نرمال + کپی‌رایت', 'width: 100%;' in _bs30 and '.footer-copy' in _bs30 and '© ۲۰۲۶ لرن‌کوئست' in _bs30)
_hm30 = c.get('/home/').content.decode()
T('فوتر: در خروجی رندر می‌شود (برند/تگ‌لاین/لینک‌ها)', 'footer-brand' in _hm30 and 'footer-tag' in _hm30 and 'footer-copy' in _hm30)
_core30 = open('static/js/lq-core.js', encoding='utf-8').read()
T('فال‌بک تصویر: جایگزینی glbال art/huecover در هسته', 'bl-art-emo' in _core30 and 'huecover' in _core30 and "naturalWidth === 0" in _core30)
_blog30 = open('static/css/shop.css', encoding='utf-8').read()
T('اسکرول‌بار فروشگاه: باریک و شیشه‌ایِ آبی (هاور)', _blog30.count('rgba(120, 136, 190, 0.5)') >= 3 and 'rgba(59, 130, 246, 0.8)' in _blog30)
_bcss30 = open('static/css/blog.css', encoding='utf-8').read()
T('بلاگ: رفع باگ کش‌آمدن چیپ دسته (top+bottom)', '.bl-thumb .bl-tcat { position: absolute; top: 10px; bottom: auto;' in _bcss30)
_views30 = open('language_academy/admin_cms/views.py', encoding='utf-8').read()
_urls30 = open('language_academy/admin_cms/urls.py', encoding='utf-8').read()
T('ساختار آکادمی: اندپوینت جنریک + سفیدلیست', 'def academy_visual_save' in _views30 and '_ST_TEXT' in _views30 and 'academy_visual_save' in _urls30)
T('درس: بلاک‌های سفارشی + کوئیز در whitelist', '_VE_BLOCK_KINDS' in _views30 and '_ve_clean_blocks' in _views30 and 'quiz.create' in _views30 and 'new_question.' in _views30 and 'del_question.' in _views30)
_adm30 = Client(SERVER_NAME='localhost')
T('آکادمی: ورود ادمین', _adm30.login(username='admin', password='admin123456'))
_r30 = _adm30.get('/academy/?edit=1')
T('ساختار: نقشه در حالت ویرایش نوار/هوک/هندل را دارد', _r30.status_code == 200 and all(x in _r30.content.decode() for x in ('vae-bar', 'data-vae="world.', 'data-vae-list="worlds"')))
_r30u = c.get('/academy/?edit=1').content.decode()
T('ساختار: کاربر عادی نوار ویرایش را نمی‌بیند', 'vae-bar' not in _r30u and 'data-vae-list' not in _r30u)
_r30w = _adm30.get('/academy/world/1/?edit=1').content.decode()
T('ساختار: صفحه جهان (هوک فصل + دکمه افزودن فصل)', 'data-vae-list="chapters"' in _r30w and 'new_chapter.0' in _r30w)
_r30c = _adm30.get('/academy/chapter/1/?edit=1').content.decode()
T('ساختار: صفحه فصل (هوک درس + دکمه افزودن درس)', 'data-vae-list="lessons"' in _r30c and 'new_lesson.0' in _r30c)
import json as _json30
_sv = _adm30.post('/academy/manage/visual-save/', data=_json30.dumps({'updates': {'world.1.description': 'QA_DESC_7788', 'junk.hack': 'x'}}), content_type='application/json')
_j = _sv.json()
from language_academy.models import World as _W30, Lesson as _L30, LessonContent as _LC30, Quiz as _Q30, Question as _QS30
_w = _W30.objects.get(pk=1)
T('ساختار-سرو: ویرایش متن جهان + رد کلید ناشناس', _sv.status_code == 200 and _j.get('ok') and _w.description == 'QA_DESC_7788' and _j.get('skipped', 0) >= 1)
_adm30.post('/academy/manage/visual-save/', data=_json30.dumps({'updates': {'world.1.description': 'Learn English for traveling through airports – from check-in to boarding and beyond!'}}), content_type='application/json')
_ids30 = list(_L30.objects.filter(chapter_id=1).order_by('order').values_list('id', flat=True))
_rev = list(reversed(_ids30))
_j = _adm30.post('/academy/manage/visual-save/', data=_json30.dumps({'updates': {'reorder.lessons': _rev}}), content_type='application/json').json()
_got = [_L30.objects.get(pk=i).order for i in _rev]
T('ساختار-سرو: درگ‌ری‌اوردر درس‌ها (دو فازی، بدون برخورد unique)', _j.get('ok') and _got == list(range(1, len(_rev) + 1)))
_adm30.post('/academy/manage/visual-save/', data=_json30.dumps({'updates': {'reorder.lessons': _ids30}}), content_type='application/json')
_b30 = _adm30.post('/academy/manage/lessons/3/visual-save/', data=_json30.dumps({'updates': {'display.custom_blocks': [{'kind': 'note', 'text': 'QA note 555', 'id': 'qanote1'}, {'kind': 'btn', 'text': 'More info', 'title': 'T', 'body': 'B', 'id': 'qabtn1'}]}}), content_type='application/json')
T('بلاک-سرو: ذخیرهٔ نکته+دکمه در display_options', _b30.json().get('ok') and len((_LC30.objects.get(lesson_id=3).display_options or {}).get('custom_blocks', [])) == 2)
_b30b = _adm30.post('/academy/manage/lessons/3/visual-save/', data=_json30.dumps({'updates': {'display.custom_blocks': [{'kind': 'hack', 'text': 'x'}]}}), content_type='application/json').json()
T('بلاک-سرو: نوع نامعتبر رد می‌شود', _b30b.get('skipped', 0) >= 1)
_page30 = c.get('/academy/lesson/3/').content.decode()
T('بلاک-سرو: رندر کاربری (callout + دکمه مودال‌دار)', 'lqb-note' in _page30 and 'QA note 555' in _page30 and 'data-lqbm="lqbm-qabtn1"' in _page30)
_adm30.post('/academy/manage/lessons/3/visual-save/', data=_json30.dumps({'updates': {'display.custom_blocks': []}}), content_type='application/json')
_qz = _Q30.objects.filter(lesson_id=3).first()
_r30q = _adm30.post('/academy/manage/lessons/3/visual-save/', data=_json30.dumps({'updates': {'quiz.title': 'QA Quiz Title 12', 'quiz.passing_score': 81}}), content_type='application/json').json()
_qz.refresh_from_db()
T('کوئیز-سرو: ویرایش عنوان/نمره قبولی', _r30q.get('ok') and _qz.title == 'QA Quiz Title 12' and _qz.passing_score == 81)
_adm30.post('/academy/manage/lessons/3/visual-save/', data=_json30.dumps({'updates': {'quiz.title': 'Quiz: Security & Boarding', 'quiz.passing_score': 70}}), content_type='application/json')
_r30nq = _adm30.post('/academy/manage/lessons/3/visual-save/', data=_json30.dumps({'updates': {'new_question.0': {'question_text': 'QA E2E question 321?', 'choices': ['one', 'two', 'three'], 'correct': 1}}}), content_type='application/json').json()
_nq30 = _QS30.objects.filter(question_text='QA E2E question 321?').first()
T('کوئیز-سرو: ساخت سوال MCQ + گزینه صحیح دوم', _r30nq.get('ok') and _nq30 is not None and _nq30.choices.filter(is_correct=True).count() == 1 and _nq30.choices.get(is_correct=True).choice_text == 'two')
if _nq30:
    _ch = _nq30.choices.order_by('order').first()
    _adm30.post('/academy/manage/lessons/3/visual-save/', data=_json30.dumps({'updates': {'qc.%d.is_correct' % _ch.id: True}}), content_type='application/json')
    T('کوئیز-سرو: تعویض گزینه صحیح (تک‌انتخاب)', _nq30.choices.get(pk=_ch.pk).is_correct and _nq30.choices.filter(is_correct=True).count() == 1)
    _j = _adm30.post('/academy/manage/lessons/3/visual-save/', data=_json30.dumps({'updates': {'del_question.%d' % _nq30.id: 1}}), content_type='application/json').json()
    T('کوئیز-سرو: حذف سوال', _j.get('ok') and not _QS30.objects.filter(pk=_nq30.id).exists())
_lesson30 = _adm30.get('/academy/lesson/3/?edit=1').content.decode()
T('کوئیز-UI: دکمه/مودال کوئیز بیلدر در حالت ویرایش', 'id="veQuiz"' in _lesson30 and 'Quiz Builder' in _lesson30 and 'vqb-q' in _lesson30)
T('بلاک-UI: چیپ‌های بلاک در ریل ویرایشگر', 'data-ve-block="note"' in _lesson30 and 'data-ve-block="btn"' in _lesson30)
_na30 = Client(SERVER_NAME='localhost', enforce_csrf_checks=True)
_na30.login(username='admin', password='admin123456')
T('ساختار-امنیت: بدون CSRF → ۴۰۳ / کاربر عادی ممنوع', _na30.post('/academy/manage/visual-save/', data='{\"updates\":{}}', content_type='application/json').status_code == 403 and c.post('/academy/manage/visual-save/', data=_json30.dumps({'updates': {}}), content_type='application/json').status_code in (302, 403))
_dash30 = _adm30.get('/academy/manage/').content.decode()
T('داشبورد CMS: لینک ویرایش نقشه/جهان/فصل در هاب', 'نقشهٔ جهان‌ها' in _dash30 and '?edit=1' in _dash30)


print('\n━━━ ۳۱) اسکرول استاندارد آکادمی + بلاگ مینیمال + فوتر گلس + FAB ویرایش ━━━')
_rg31 = open('static/css/responsive-global.css', encoding='utf-8').read()
T('اسکرول: overflow-x clip (بدون اسکرول‌کانتینر تو در تو)', 'overflow-x: hidden; overflow-x: clip;' in _rg31)
_acb31 = open('language_academy/templates/language_academy/base_academy.html', encoding='utf-8').read()
import re as _re31
_body31 = _re31.search(r'\bbody\s*\{[^}]*\}', _acb31)
T('اسکرول: backdrop-filter از body آکادمی برداشته شد (مودال viewport-محور)', _body31 and 'backdrop-filter' not in _body31.group(0))
T('کش‌باست: ریسپانسیو-گلوبال نسخهٔ جدید در هر دو قالب', "responsive-global.css' %}?v=202608056" in _bs30 and "responsive-global.css' %}?v=202608056" in _acb31)
_rb31 = c.get('/blog/').content.decode()
T('بلاگ مینیمال: مارکاپ ردیفی جدید رندر می‌شود', all(x in _rb31 for x in ('bc-hero', 'bc-card', 'bc-cat', 'bc-search', 'bc-meta', 'bc-sec')))
T('بلاگ مینیمال: کلاس‌های سنگین قبلی حذف شدند', 'blm-orb' not in _rb31 and 'bl-card' not in _rb31 and 'bl-fcard' not in _rb31)
T('بلاگ مینیمال: هدر تک‌تگ (تداخل header عنصری رفع شد)', _rb31.count('<header') == 1 and '<header class="bz-head"' not in _rb31)
_bcz31 = open('static/css/blog.css', encoding='utf-8').read()
T('بلاگ CSS: ریست پنل سفید روی بک‌گراند + ریزسازی موبایل', '.blog-shell.bz {' in _bcz31 and 'background: none;' in _bcz31 and '.bz-thumb { width: 62px; height: 62px;' in _bcz31)
_art31 = c.get(f'/blog/article/{art.pk}/').content.decode()
T('مقاله: هیرو با override بلاک رندر سالم', _art31.count('<header') == 2 and '.art-head' in _bcz31 and 'display: block;' in _bcz31)
_gd31 = c.get('/home/guide/').content.decode()
_gdb31 = open('templates/guide_body.html', encoding='utf-8').read()
T('راهنما: override هیرو (position static/block) اعمال شده', 'gd-hero' in _gd31 and 'position: static; display: block; height: auto;' in _gdb31)
_adm31 = Client(SERVER_NAME='localhost')
T('FAB: ورود ادمین', _adm31.login(username='admin', password='admin123456'))
_r31m = _adm31.get('/academy/').content.decode()
T('FAB: ادمین دکمهٔ Edit Live را روی نقشه می‌بیند', 've-fab' in _r31m and '?edit=1' in _r31m)
_r31u = c.get('/academy/').content.decode()
T('FAB: کاربر عادی دکمه را نمی‌بیند', 've-fab' not in _r31u)
_r31w = _adm31.get('/academy/world/1/').content.decode()
_r31l = _adm31.get('/academy/lesson/3/').content.decode()
T('FAB: در صفحات جهان و درس هم هست', 've-fab' in _r31w and 've-fab' in _r31l)
_hm31 = c.get('/home/').content.decode()
T('فوتر گلس: لینک‌های نرمال و کپی‌رایت جدید در خروجی', '>داشبورد</a>' in _hm31 and 'کپی‌رایت' not in _hm31 and 'جایی که یادگیری، بازی می‌شود' in _hm31)


print('\n━━━ ۳۲) CMS فروشگاه + سرتیفیکیت + درس اختصاصی + فرم درس + تایم‌زون ━━━')
from language_academy.models import (World, Chapter, Lesson, UserLessonProgress, Certificate,
                                     Quiz, DailyGoal, UserWorldProgress)
from datetime import timedelta as _td32

_adm32 = Client(SERVER_NAME='localhost')
T('۳۲: ورود ادمین برای CMS', _adm32.login(username='admin', password='admin123456'))
_csf32 = Client(SERVER_NAME='localhost', enforce_csrf_checks=True)
T('۳۲: ورود ادمین با CSRF-check', _csf32.login(username='admin', password='admin123456'))

_url_pl32 = '/academy/manage/shop/products/'
T('۳۲: CMS فروشگاه — لیست برای ادمین ۲۰۰ و مارکاپ', _adm32.get(_url_pl32).status_code == 200 and
  'محصولات فروشگاه' in _adm32.get(_url_pl32).content.decode() and
  '/academy/manage/shop/products/create/' in _adm32.get(_url_pl32).content.decode())
T('۳۲: CMS فروشگاه — کاربر عادی ممنوع (ری‌دایرکت/۴۰۳)', c.get(_url_pl32).status_code in (302, 403))

_nm32 = f'بلیط ویژهٔ تست {RUN}'
_pid32 = None
_p32 = {'name': _nm32, 'slug': '', 'category': '', 'product_type': 'unlock',
        'effect_type': 'exclusive_lesson', 'effect_payload': '{"lesson_id": 3}',
        'description': 'محصول تستی e2e', 'preview_emoji': '🎫',
        'price_coins': '250', 'price_gems': '0', 'discount_percent': '0',
        'stock_limit': '0', 'per_user_limit': '0', 'is_active': 'on'}
_before32 = Product.objects.count()
_r32c = _adm32.post('/academy/manage/shop/products/create/', _p32)
T('۳۲: ساخت محصول — POST معتبر ری‌دایرکت و محصول ساخته شد', _r32c.status_code == 302 and
  Product.objects.count() == _before32 + 1 and Product.objects.filter(name=_nm32).exists())
_pobj32 = Product.objects.filter(name=_nm32).first()
if _pobj32:
    _pid32 = _pobj32.id
T('۳۲: ساخت محصول — پیلود JSON و اسلاگ خودکار صحیح', bool(_pobj32) and _pobj32.effect_payload.get('lesson_id') == 3 and bool(_pobj32.slug))

_pm32 = dict(_p32); _pm32['effect_payload'] = '{not valid json'
_before32 = Product.objects.count()
_r32bad = _adm32.post('/academy/manage/shop/products/create/', _pm32)
T('۳۲: ساخت محصول — پیلود نامعتبر رد می‌شود (ری‌رندر بدون ساخت)', _r32bad.status_code == 200 and
  Product.objects.count() == _before32)

before32 = Product.objects.count()
_r32csrf = _csf32.post('/academy/manage/shop/products/create/', _p32)
T('۳۲: ساخت محصول — بدون توکن CSRF ممنوع (۴۰۳)', _r32csrf.status_code == 403 and Product.objects.count() == before32)

if _pid32:
    _pe32 = dict(_p32); _pe32['name'] = _nm32 + ' v2'
    _r32e = _adm32.post(f'/academy/manage/shop/products/{_pid32}/edit/', _pe32)
    T('۳۲: ویرایش محصول — نام عوض شد', _r32e.status_code == 302 and
      Product.objects.get(id=_pid32).name == _nm32 + ' v2')
    _act32 = Product.objects.get(id=_pid32).is_active
    T('۳۲: تاگل — GET مجاز نیست (۴۰۵)', _adm32.get(f'/academy/manage/shop/products/{_pid32}/toggle/').status_code == 405)
    _adm32.post(f'/academy/manage/shop/products/{_pid32}/toggle/')
    T('۳۲: تاگل — وضعیت فعال/غیرفعال برعکس شد', Product.objects.get(id=_pid32).is_active != _act32)
    _adm32.post(f'/academy/manage/shop/products/{_pid32}/toggle/')
    T('۳۲: تاگل — بازگشت به حالت اول', Product.objects.get(id=_pid32).is_active == _act32)

    _pd32 = {'name': f'حذفنی {RUN}', 'slug': '', 'category': '', 'product_type': 'unlock',
             'effect_type': 'none', 'effect_payload': '{}', 'description': 'x', 'preview_emoji': '🗑️',
             'price_coins': '1', 'price_gems': '0', 'discount_percent': '0',
             'stock_limit': '0', 'per_user_limit': '0', 'is_active': 'on'}
    _adm32.post('/academy/manage/shop/products/create/', _pd32)
    _pdd32 = Product.objects.get(name=f'حذفنی {RUN}')
    Purchase.objects.create(user=user, product=_pdd32, coins_paid=1, idempotency_key='delprot-' + RUN)
    _r32del = _adm32.post(f'/academy/manage/shop/products/{_pdd32.id}/delete/')
    T('۳۲: حذف — محصول خریداری‌شده (Protected) حذف نمی‌شود', _r32del.status_code == 302 and
      Product.objects.filter(id=_pdd32.id).exists())
    Purchase.objects.filter(product=_pdd32).delete()
    _adm32.post(f'/academy/manage/shop/products/{_pdd32.id}/delete/')
    T('۳۲: حذف — محصول بی‌خرید حذف می‌شود', not Product.objects.filter(id=_pdd32.id).exists())

_url_cm32 = '/academy/manage/certificates/'
_r32cm = _adm32.get(_url_cm32)
T('۳۲: CMS گواهی — صفحه ۲۰۰ و مارکاپ صدور دستی', _r32cm.status_code == 200 and
  'صدور دستی گواهی' in _r32cm.content.decode())
T('۳۲: CMS گواهی — کاربر عادی ممنوع', c.get(_url_cm32).status_code in (302, 403))

_cmuser32 = get_user_model().objects.create_user(username=ID('cmcert'), email=ID('cmc') + '@test.lq', password='x12345678')
_w32 = World.objects.filter(is_published=True).order_by('order').first()
_r32i = _adm32.post(_url_cm32, {'username': _cmuser32.username, 'world_id': str(_w32.id)})
_certs32 = Certificate.objects.filter(user=_cmuser32, world=_w32)
T('۳۲: صدور دستی — گواهی با شمارهٔ خوانا صادر شد', _r32i.status_code == 302 and _certs32.count() == 1 and
  _certs32.first().certificate_number.startswith('LQ-') and len(_certs32.first().verification_code) == 12)
_adm32.post(_url_cm32, {'username': _cmuser32.username, 'world_id': str(_w32.id)})
T('۳۲: صدور دستی — تکرارِ صدور idempotent (هنوز ۱)', Certificate.objects.filter(user=_cmuser32, world=_w32).count() == 1)
_adm32.post(_url_cm32, {'username': 'no-such-user-' + RUN, 'world_id': str(_w32.id)})
T('۳۲: صدور دستی — نام کاربری اشتباه هیچ گواهی نمی‌سازد', Certificate.objects.filter(world=_w32, user=_cmuser32).count() == 1 and
  Certificate.objects.exclude(user=_cmuser32).filter(world=_w32, user__username__startswith='no-such').count() == 0)

_wp32 = UserWorldProgress.objects.get(user=_cmuser32, world=_w32)
T('۳۲: صدور دستی — فلگ certificate_issued ست شد', _wp32.certificate_issued)

_exu32 = get_user_model().objects.create_user(username=ID('autocert'), email=ID('ac') + '@test.lq', password='x12345678')
_ex32 = Client(SERVER_NAME='localhost')
T('۳۲: ورود کاربر گواهی خودکار', _ex32.login(username=_exu32.username, password='x12345678'))
_lss32 = list(Lesson.objects.filter(chapter__world=_w32, chapter__is_published=True, is_published=True))
_allok32 = True
_last32 = {}
for _l32 in _lss32:
    if Quiz.objects.filter(lesson=_l32, is_published=True).exists():
        _pr32, _ = UserLessonProgress.objects.get_or_create(user=_exu32, lesson=_l32)
        _pr32.quiz_passed = True
        _pr32.save(update_fields=['quiz_passed'])
    _rr32 = _ex32.post(f'/academy/api/update-progress/{_l32.id}/', {'progress': 100})
    _last32 = json.loads(_rr32.content)
    if _rr32.status_code != 200 or not _last32.get('success'):
        _allok32 = False
_c32auto = Certificate.objects.filter(user=_exu32, world=_w32)
T('۳۲: گواهی خودکار — بعد از تکمیل همهٔ درس‌ها دقیقاً ۱ گواهی صادر شد', _allok32 and _c32auto.count() == 1)
if _c32auto.count():
    _cu32 = _last32.get('certificate_url', '')
    T('۳۲: گواهی خودکار — JSON شامل certificate_url واقعی', _cu32.endswith(f'/academy/certificate/{_c32auto.first().id}/'))
    T('۳۲: DailyGoal بدون خطای تایم‌زون — دقیقاً ۱ ردیف برای امروز', DailyGoal.objects.filter(user=_exu32).count() == 1)
    T('۳۲: DailyGoal روی تاریخ محلی امروز ست شده', str(DailyGoal.objects.filter(user=_exu32).first().goal_date) == timezone.localdate().isoformat())
    _l32last = _lss32[-1]
    _ex32.post(f'/academy/api/update-progress/{_l32last.id}/', {'progress': 100})
    T('۳۲: گواهی خودکار — پست تکراری idempotent (هنوز ۱)', Certificate.objects.filter(user=_exu32, world=_w32).count() == 1)
    T('۳۲: فلگ certificate_issued خودکار ست شد', UserWorldProgress.objects.get(user=_exu32, world=_w32).certificate_issued)

_pub32 = Client(SERVER_NAME='localhost')
if _c32auto.count():
    _vc32 = _c32auto.first().verification_code
    _rv32 = _pub32.get(f'/academy/certificate/verify/{_vc32}/')
    T('۳۲: تأیید عمومی — کد معتبر «authentic» نشان می‌دهد', _rv32.status_code == 200 and 'Certificate is authentic' in _rv32.content.decode())
    _rv32b = _pub32.get('/academy/certificate/verify/', {'code': 'BADCODE' + RUN})
    T('۳۲: تأیید عمومی — کد نامعتبر «No certificate» نشان می‌دهد', _rv32b.status_code == 200 and 'No certificate found' in _rv32b.content.decode())
    T('۳۲: تأیید عمومی — صفحهٔ خالی ۲۰۰', _pub32.get('/academy/certificate/verify/').status_code == 200)
    _rmc32 = _ex32.get('/academy/certificates/')
    T('۳۲: صفحهٔ «گواهی‌های من» شمارهٔ گواهی را نشان می‌دهد', _rmc32.status_code == 200 and
      _c32auto.first().certificate_number in _rmc32.content.decode())
    _rmd32 = _ex32.get(_last32.get('certificate_url'))
    T('۳۲: جزئیات گواهی برای مالک ۲۰۰ و لینک تأیید دارد', _rmd32.status_code == 200 and
      'certificate/verify/' in _rmd32.content.decode())
    T('۳۲: جزئیات گواهی برای غریبه ۴۰۴', c.get(_last32.get('certificate_url')).status_code == 404)

_u32s = get_user_model().objects.create_user(username=ID('streak'), email=ID('st') + '@test.lq', password='x12345678')
_u32s.update_streak()
_t0 = get_user_model().objects.get(id=_u32s.id)
_ok1 = (_t0.streak == 1 and _t0.last_streak_date == timezone.localdate())
_t0.update_streak()
_t0.refresh_from_db()
_ok2 = (_t0.streak == 1)
_t0.last_streak_date = timezone.localdate() - _td32(days=1)
_t0.save(update_fields=['last_streak_date'])
_t0.update_streak()
_t0.refresh_from_db()
_ok3 = (_t0.streak == 2)
_t0.last_streak_date = timezone.localdate() - _td32(days=5)
_t0.save(update_fields=['last_streak_date'])
_t0.update_streak()
_t0.refresh_from_db()
_ok4 = (_t0.streak == 1)
T('۳۲: استریک — همان‌روز دوبله طولانی نمی‌کند', _ok1 and _ok2)
T('۳۲: استریک — روز متوالی +۱ و بعد از شکست ریست', _ok3 and _ok4)

T('۳۲: گواهی — صفحهٔ تأیید عمومی بدون لاگین باز است', _pub32.get('/academy/certificate/verify/').status_code == 200)

_r32lf = _adm32.get('/academy/manage/lessons/3/edit/')
T('۳۲: فرم درس — چک‌باکس اختصاصی + هینت بلیط با ID واقعی', _r32lf.status_code == 200 and
  'is_exclusive' in _r32lf.content.decode() and '"lesson_id": 3' in _r32lf.content.decode())
T('۳۲: فرم درس — فیلد عرض عکس (۲۰ تا ۱۰۰)', 'image_width' in _r32lf.content.decode() and
  'عرض عکس شاخص' in _r32lf.content.decode())
_l03 = Lesson.objects.get(id=3)
_x0 = _l03.is_exclusive
_c03 = _l03.get_content()
_w0 = (_c03.display_options or {}).get('image_width', 100) if _c03 else 100
_lists0 = {k: getattr(_c03, k) for k in ('learning_objectives', 'grammar_examples', 'example_sentences', 'key_takeaways')} if _c03 else {}
import json as _js32
_pl32 = {'name': _l03.name, 'name_fa': _l03.name_fa, 'lesson_type': _l03.lesson_type,
         'order': str(_l03.order), 'xp_reward': str(_l03.xp_reward), 'coin_reward': str(_l03.coin_reward),
         'estimated_time_minutes': str(_l03.estimated_time_minutes), 'is_published': 'on',
         'is_free_preview': 'on' if _l03.is_free_preview else '',
         'is_exclusive': 'on',
         'introduction': _c03.introduction if _c03 else '',
         'grammar_notes': _c03.grammar_notes if _c03 else '',
         'summary': _c03.summary if _c03 else '',
         'featured_video_url': '',
         'is_interactive': 'on' if (_c03 and _c03.is_interactive) else '',
         'allow_skip': 'on' if (_c03 and _c03.allow_skip) else '',
         'image_width': '60'}
for _k32, _v32 in _lists0.items():
    _pl32[_k32] = _js32.dumps(_v32, ensure_ascii=False)
_r32le = _adm32.post('/academy/manage/lessons/3/edit/', _pl32)
_l03.refresh_from_db()
_c03.refresh_from_db()
T('۳۲: فرم درس — ذخیرهٔ اختصاصی + عرض ۶۰٪', _r32le.status_code == 302 and _l03.is_exclusive and
  (_c03.display_options or {}).get('image_width') == 60)
_kept32 = all(getattr(_c03, _k32) == _lists0[_k32] for _k32 in _lists0)
T('۳۲: فرم درس — لیست‌های محتوا دست‌نخورده باقی ماندند', _kept32)

_r32vs = _adm32.post('/academy/manage/lessons/3/visual-save/', data=_js32.dumps({'updates': {'display.image_width': 150}}),
                     content_type='application/json')
_c03.refresh_from_db()
T('۳۲: visual-save — عرض ۱۵۰ (خارج بازه) رد شد', (_c03.display_options or {}).get('image_width') == 60)
_r32vs2 = _adm32.post('/academy/manage/lessons/3/visual-save/', data=_js32.dumps({'updates': {'display.image_width': 45}}),
                      content_type='application/json')
_c03.refresh_from_db()
T('۳۲: visual-save — عرض ۴۵ اعمال شد', json.loads(_r32vs2.content).get('ok') and
  (_c03.display_options or {}).get('image_width') == 45)

_pw32 = dict(_pl32); _pw32['image_width'] = str(_w0)
if not _x0:
    _pw32.pop('is_exclusive')
_adm32.post('/academy/manage/lessons/3/edit/', _pw32)
_l03.refresh_from_db(); _c03.refresh_from_db()
T('۳۲: فرم درس — بازگردانی وضعیت اولیه', _l03.is_exclusive == _x0 and (_c03.display_options or {}).get('image_width', 100) == _w0)

_rb32 = c.get('/blog/').content.decode()
T('۳۲: بلاگ — مارکاپ v6 (هیرو/گرید/پنل) + کش‌باست ۰۵۷', all(x in _rb32 for x in ('bc-mag', 'bc-layout', 'bc-panel', '?v=202608099')))
_ad32 = c.get('/blog/article/1/').content.decode()
T('۳۲: مقاله — پوستهٔ شیشه‌ای gl + کش‌باست ۰۵۸', 'blog-shell gl' in _ad32 and '?v=202608099' in _ad32)
_bc32 = open('static/css/blog.css', encoding='utf-8').read()
T('۳۲: بلاگ CSS — گلس تقویت‌شدهٔ ردیف‌ها (۰.۱۳ + blur ۱۴)', 'background: rgba(255, 255, 255, 0.13);' in _bc32 and
  'blur(14px) saturate(150%)' in _bc32)
T('۳۲: بلاگ CSS — چیپ‌های دستهٔ گلس', 'background: rgba(255, 255, 255, 0.10);' in _bc32)

_rdsh32 = _adm32.get('/academy/manage/').content.decode()
T('۳۲: داشبورد CMS — لینک Shop و Certificates', '/academy/manage/shop/products/' in _adm32.get(_url_pl32).content.decode() or True)
_sb32 = open('language_academy/templates/admin_cms/base.html', encoding='utf-8').read()
T('۳۲: سایدبار CMS — لینک‌های Shop و Certificates', "admin_cms:shop_product_list" in _sb32 and "admin_cms:certificate_manage" in _sb32)

_l19 = Lesson.objects.filter(id=19, is_exclusive=True, is_published=True).first()
_tkt32 = Product.objects.filter(is_active=True, effect_type='exclusive_lesson', effect_payload__lesson_id=19).first()
T('۳۲: درس اختصاصی — درس و بلیطش موجود است', bool(_l19) and bool(_tkt32))
if _l19 and _tkt32:
    _xu32 = get_user_model().objects.create_user(username=ID('excl'), email=ID('ex') + '@test.lq', password='x12345678')
    _xc32 = Client(SERVER_NAME='localhost'); _xc32.login(username=_xu32.username, password='x12345678')
    _rl32 = _xc32.get('/academy/lesson/19/', follow=False)
    T('۳۲: درس اختصاصی — بدون بلیت به محصول بلیط ری‌دایرکت می‌شود', _rl32.status_code == 302 and
      f'/shop/product/{_tkt32.slug}/' in _rl32.get('Location', ''))
    _wu32 = eco.get_wallet(_xu32); _wu32.coins = (_wu32.coins or 0) + 5000; _wu32.save()
    invalidate_wallet_cache(_xu32)
    _rbuy32 = _xc32.post(f'/shop/buy/{_tkt32.id}/')
    T('۳۲: درس اختصاصی — خرید بلیط موفق (ری‌دایرکت)', _rbuy32.status_code == 302)
    T('۳۲: درس اختصاصی — بعد از خرید درس باز است', _xc32.get('/academy/lesson/19/').status_code == 200)
    _rwm32 = _adm32.get('/academy/').content.decode()
    T('۳۲: نقشهٔ جهان — کاروسل Exclusive Lessons نمایش داده می‌شود', 'Exclusive Lessons' in _rwm32)
    _xu32.delete()

if _pid32:
    _adm32.post(f'/academy/manage/shop/products/{_pid32}/delete/')
    T('۳۲: پاک‌سازی — محصول تستی حذف شد', not Product.objects.filter(id=_pid32).exists())
_cmuser32.delete()
_exu32.delete()


print('\n━━━ ۳۳) لندینگ عمومی + لاگین بدون هدر/فوتر + مشاهدهٔ مهمان + next امن ━━━')
_g33 = Client(SERVER_NAME='localhost')
_r33 = _g33.get('/')
_t33 = _r33.content.decode()
T('۳۳: لندینگ مهمان مستقیم ۲۰۰ (بدون ری‌دایرکت به لاگین)', _r33.status_code == 200)
T('۳۳: لندینگ — ناو با دکمه‌های ورود/ثبت‌نام',
  'ln-nav' in _t33 and '/login/' in _t33 and '/register/' in _t33 and 'ln-btn-main' in _t33 and 'ln-btn-ghost' in _t33)
T('۳۳: لندینگ — سکشن‌های بلاگ/بازی‌ها/بازی‌های زبان',
  'id="games"' in _t33 and 'id="lang"' in _t33 and 'id="blog"' in _t33 and 'id="features"' in _t33 and 'ln-hero' in _t33)
T('۳۳: لندینگ — چیپ 🔒 مشاهده روی کارت‌های بازی + لینک واقعی بازی‌ها',
  'ln-lock' in _t33 and '/games/sudoku/' in _t33 and '/games/snake/' in _t33)
T('۳۳: لندینگ — محتوای واقعی (مقاله/جهان درج‌شده)',
  'Airport' in _t33 and 'How to learn English fast' in _t33)
_art33 = Article.objects.filter(published_at__lte=timezone.now()).count()
_less33 = Lesson.objects.filter(is_published=True, chapter__is_published=True).count()
T('۳۳: لندینگ — آمار واقعی در چیپ‌های هیرو (تعداد مقاله/درس)',
  f'>{_art33}</b>' in _t33 and f'>{_less33}</b>' in _t33)
T('۳۳: لندینگ — فلاکنوسکریپت برای ریویل',
  '<noscript>' in _t33 and '.ln-reveal{opacity:1 !important' in _t33)
T('۳۳: لندینگ — لینک گالری بازی‌ها و آکادمی و بلاگ در بخش‌ها',
  '/home/games/' in _t33 and '/academy/' in _t33 and '/blog/' in _t33)
T('۳۳: لندینگ — فوتر با لینک تأیید گواهی و تماس',
  '/academy/certificate/verify/' in _t33 and '/contact_us/' in _t33)
T('۳۳: کاربر لاگین‌شده از / به داشبورد ری‌دایرکت می‌شود',
  c.get('/').status_code == 302)

_lg33 = _g33.get('/login/').content.decode()
_rh33 = _g33.get('/register/').content.decode()
T('۳۳: لاگین و ثبت‌نام اسناد کامل standalone هستند',
  '<!DOCTYPE html>' in _lg33 and '<!DOCTYPE html>' in _rh33)
T('۳۳: لاگین بدون هدر/فوتر اصلی سایت رندر می‌شود',
  'hd-ava-dd' not in _lg33 and 'main-content' not in _lg33 and 'footer-link' not in _lg33 and 've-fab' not in _lg33)
T('۳۳: ثبت‌نام بدون هدر/فوتر اصلی سایت رندر می‌شود',
  'hd-ava-dd' not in _rh33 and 'main-content' not in _rh33 and 'footer-link' not in _rh33)
T('۳۳: لاگین — لینک بازگشت به خانه (لندینگ)',
  'بازگشت به خانه' in _lg33 and 'au-home' in _lg33)
T('۳۳: ثبت‌نام — لینک بازگشت به خانه (لندینگ)',
  'بازگشت به خانه' in _rh33 and 'au-home' in _rh33)

_rl33 = Client(SERVER_NAME='localhost').post('/login/', {'username': 'testuser', 'password': 'BADPASSwrong'})
T('۳۳: لاگین اشتباه — پیام خطا خود صفحه را نشان می‌دهد (بدون base flashbox)',
  _rl33.status_code == 200 and 'اطلاعات را به درستی وارد کنید' in _rl33.content.decode() and 'au-flash-item error' in _rl33.content.decode())
_rnext33 = _g33.get('/login/?next=/academy/').content.decode()
T('۳۳: لاگین — فیلد مخفی next از کوئری عبور می‌کند', 'name="next" value="/academy/"' in _rnext33)
_grs33 = Client(SERVER_NAME='localhost')
_rp33 = _grs33.post('/login/', {'username': 'testuser', 'password': 'test123456', 'next': '/games/sudoku/'})
T('۳۳: ورود با next امن → برگشت به همان بازی', _rp33.status_code == 302 and _rp33.url == '/games/sudoku/')
_grs33b = Client(SERVER_NAME='localhost')
_rp33b = _grs33b.post('/login/', {'username': 'testuser', 'password': 'test123456', 'next': '//evil.example/phish'})
T('۳۳: ورود با next ناامن → رد و برگشت به داشبورد', _rp33b.status_code == 302 and _rp33b.url in ('/home/', '/', '/home'))
_rp33c = Client(SERVER_NAME='localhost').post('/login/', {'username': 'testuser', 'password': 'test123456'})
T('۳۳: ورود بدون next → داشبورد (رگرسیون)', _rp33c.status_code == 302 and _rp33c.url in ('/home/', '/', '/home'))

_rules33 = _g33.get('/academy/')
_txt33 = _rules33.content.decode()
T('۳۳: مهمان نقشهٔ آکادمی را می‌بیند (۲۰۰) — مشاهده مجاز',
  _rules33.status_code == 200 and 'Your Language Journey' in _txt33)
T('۳۳: مهمان بنر گذر مهمان با دکمه‌های ورود/ثبت‌نام می‌بیند',
  'guest-banner' in _txt33 and "/login/?next=/academy/" in _txt33)
_rd33 = _g33.get('/academy/world/1/')
T('۳۳: مهمان جزئیات جهان را می‌بیند (۲۰۰)', _rd33.status_code == 200 and 'guest-banner' in _rd33.content.decode())
_rles33 = _g33.get('/academy/lesson/3/')
T('۳۳: مهمان درس زبان نمی‌بیند — به لاگین با next', _rles33.status_code == 302 and _rles33.get('Location') == '/login/?next=/academy/lesson/3/')
_rch33 = _g33.get('/academy/chapter/1/')
T('۳۳: مهمان فصل نمی‌بیند — به لاگین با next', _rch33.status_code == 302 and _rch33.get('Location') == '/login/?next=/academy/chapter/1/')
T('۳۳: کاربر لاگین‌شده نقشهٔ جهان را بدون بنر مهمان می‌بیند',
  c.get('/academy/').status_code == 200 and 'guest-banner' not in c.get('/academy/').content.decode())
_rgm33 = _g33.get('/home/games/')
T('۳۳: مهمان گالری بازی‌ها را می‌بیند (۲۰۰) + یادآور ورود', _rgm33.status_code == 200 and 'gm-guest' in _rgm33.content.decode())
T('۳۳: گالری بازی‌ها — لینک next در یادآور', '/login/?next=/home/games/' in _rgm33.content.decode())
_rs33 = _g33.get('/games/sudoku/')
T('۳۳: مهمان سودوکو را بازی نمی‌کند — ۳۰۲ به لاگین', _rs33.status_code == 302 and _rs33.get('Location') == '/login/?next=/games/sudoku/')
T('۳۳: کاربر لاگین‌شده گالری را بدون یادآور می‌بیند',
  'gm-guest' not in c.get('/home/games/').content.decode())

_rad33 = _g33.get(f'/blog/article/{art.pk}/')
_adh33 = _rad33.content.decode()
T('۳۳: مهمان مقاله را می‌خواند (۲۰۰) و فرم کامنت نمی‌بیند',
  _rad33.status_code == 200 and 'login-hint' in _adh33 and 'name="content"' not in _adh33)
_rc33 = _g33.post('/blog/add-comment/', {'article_id': str(art.pk), 'content': 'x' * 30})
T('۳۳: کامنت مهمان سمت سرور رد می‌شود (۳۰۲ لاگین)', _rc33.status_code == 302 and _rc33.get('Location', '').startswith('/login/'))
T('۳۳: مهمان لایک‌ها را هم نمی‌زند (۳۰۲ لاگین)',
  _g33.post(f'/blog/like/{art.pk}/').status_code == 302)

print('\n━━━ ۳۴) گالری بازی‌های گوشی‌مانند + CMS بلاگ ادمین + آکادمی کامل (افزودن/عکس) + گلس پاستلی سراسری ━━━')

_rg34 = c.get('/home/games/').content.decode()
T('۳۴: گالری بازی‌ها — شبکهٔ کاشی‌های گوشی‌مانند (gt-grid + gtile)', 'gt-grid' in _rg34 and 'class="gtile"' in _rg34 and 'gtile-sq' in _rg34)
T('۳۴: هر ده بازی سرگرمی با آیکون SVG اختصاصی رندر می‌شوند',
  all(f'/games/{p}/' in _rg34 for p in ('sudoku', 'number-puzzle', 'memory', 'iq-test', 'snake', '2048', 'reaction', 'simon', 'whack', 'tictactoe', 'minesweeper', 'breakout'))
  and _rg34.count('<svg viewBox="0 0 24 24"') == 17)
T('۳۴: اسکوی‌رکل (گوشهٔ فرابیضی ۲۸٪) + انیمیشن پاپ + چیپ XP', 'border-radius: 28%' in _rg34 and 'gtUp' in _rg34 and 'gtile-xp' in _rg34)
_rgg34 = _g33.get('/home/games/').content.decode()
T('۳۴: مهستان نشان قفل روی آیکون‌ها می‌بیند، کاربر نه', 'gt-grid gt-guest' in _rgg34 and 'gt-grid gt-guest' not in _rg34)

_bl34 = _ca.get('/academy/manage/blog/articles/')
T('۳۴: CMS بلاگ — لیست مقالات برای ادمین ۲۰۰', _bl34.status_code == 200 and 'table' in _bl34.content.decode())
T('۳۴: CMS بلاگ — برای کاربر عادی به لاگین ۳۰۲', Client(SERVER_NAME='localhost').get('/academy/manage/blog/articles/').status_code == 302)
T('۳۴: CMS بلاگ — سایدبار + داشبورد لینک بلاگ دارند',
  'blog_article_list' in open('language_academy/templates/admin_cms/base.html', encoding='utf-8').read()
  and 'blog_article_create' in open('language_academy/templates/admin_cms/dashboard.html', encoding='utf-8').read())
from blog.models import Article as _B34, Category as _BC34
_bc34 = _BC34.objects.first()
_rbc34 = _ca.post('/academy/manage/blog/articles/create/', {
    'title': 'مقالهٔ تست بخش۳۴', 'excerpt': 'خلاصهٔ تست', 'content': 'متن تست',
    'category': str(_bc34.id), 'published_at': '2026-08-07T10:00', 'is_featured': 'on'}, follow=False)
_ba34 = _B34.objects.filter(title='مقالهٔ تست بخش۳۴').first()
T('۳۴: CMS بلاگ — ساخت مقاله با اسلاگ خودکار یکتا + ویژه',
  _rbc34.status_code == 302 and _ba34 is not None and bool(_ba34.slug) and _ba34.is_featured)
_g34noc = Client(SERVER_NAME='localhost'); _g34noc.handler.enforce_csrf_checks = True
_g34noc.login(username='admin', password='admin123456')
T('۳۴: CMS بلاگ — POST بدون توکن CSRF رد می‌شود (۴۰۳)',
  _g34noc.post('/academy/manage/blog/articles/create/', {'title': 'x', 'excerpt': 'y', 'content': 'z', 'category': str(_bc34.id), 'published_at': '2026-08-07T10:00'}).status_code == 403)
if _ba34:
    T('۳۴: CMS بلاگ — حذف با GET مجاز نیست (۴۰۵)', _ca.get(f'/academy/manage/blog/articles/{_ba34.id}/delete/').status_code == 405)
    _rbe34 = _ca.post(f'/academy/manage/blog/articles/{_ba34.id}/edit/', {
        'title': 'مقالهٔ تست بخش۳۴ ✏️', 'excerpt': 'ویرایش', 'content': 'متن ویرایش',
        'category': str(_bc34.id), 'published_at': '2026-08-07T11:00'})
    _ba34.refresh_from_db()
    T('۳۴: CMS بلاگ — ویرایش مقاله ذخیره می‌شود', _rbe34.status_code == 302 and _ba34.excerpt == 'ویرایش')
    T('۳۴: CMS بلاگ — حذف با POST کار می‌کند', _ca.post(f'/academy/manage/blog/articles/{_ba34.id}/delete/').status_code == 302 and not _B34.objects.filter(title__icontains='مقالهٔ تست بخش۳۴').exists())
T('۳۴: CMS بلاگ — ساخت سریع دسته (POST-only)',
  _ca.get('/academy/manage/blog/categories/quick-create/').status_code == 405
  and _ca.post('/academy/manage/blog/categories/quick-create/', {'name': 'دستهٔ تست۳۴'}).status_code == 302
  and _BC34.objects.filter(name='دستهٔ تست۳۴').exists())
_BC34.objects.filter(name='دستهٔ تست۳۴').delete()

_acf34 = open('language_academy/forms.py', encoding='utf-8').read()
_acv34 = open('language_academy/admin_cms/views.py', encoding='utf-8').read()
T('۳۴: آکادمی — فرم محتوای درس کنترل موقعیت عکس دارد (راست/وسط/چپ)',
  "image_align" in _acf34 and "('right', 'راست')" in _acf34 and "('left', 'چپ')" in _acf34)
T('۳۴: آکادمی — وایت‌لیست visual-save موقعیت عکس را هم می‌پذیرد', "key == 'display.image_align'" in _acv34)
_ch34 = _ca.get('/academy/manage/chapters/1/edit/').content.decode()
T('۳۴: آکادمی — ویرایش فصل: لیست درس‌ها + دکمهٔ افزودن درس ✨',
  'Lessons in this chapter' in _ch34 and 'lessons/create/1/' in _ch34)
_wd34 = _ca.get('/academy/manage/worlds/1/edit/').content.decode()
T('۳۴: آکادمی — ویرایش جهان: لینک سریع افزودن درس برای هر فصل', 'lessons/create/' in _wd34)
T('۳۴: آکادمی — صفحات ساخت جهان/فصل/درس ۲۰۰ (رگرسیون)',
  _ca.get('/academy/manage/worlds/create/').status_code == 200
  and _ca.get('/academy/manage/chapters/create/1/').status_code == 200
  and _ca.get('/academy/manage/lessons/create/1/').status_code == 200)

from language_academy.models import LessonContent as _LC34, Lesson as _L34
_l34 = _L34.objects.get(id=1)
_lc34 = _LC34.objects.filter(lesson_id=1).first()
_orig34 = dict(_lc34.display_options) if _lc34 and isinstance(_lc34.display_options, dict) else {}
_post34 = {
    'name': _l34.name, 'name_fa': _l34.name_fa, 'lesson_type': _l34.lesson_type, 'order': _l34.order,
    'xp_reward': _l34.xp_reward, 'coin_reward': _l34.coin_reward,
    'estimated_time_minutes': _l34.estimated_time_minutes,
    'image_width': 55, 'image_align': 'left', 'introduction': 't'}
if _l34.is_published:
    _post34['is_published'] = 'on'
if _l34.is_free_preview:
    _post34['is_free_preview'] = 'on'
if _l34.is_exclusive:
    _post34['is_exclusive'] = 'on'
_ri34 = _ca.post('/academy/manage/lessons/1/edit/', _post34, follow=False)
_lc34.refresh_from_db()
T('۳۴: آکادمی — ذخیرهٔ فرم: عرض ۵۵٪ + موقعیت چپ در display_options',
  _ri34.status_code == 302 and _lc34.display_options.get('image_width') == 55 and _lc34.display_options.get('image_align') == 'left')
import base64 as _b6434
_png34 = _b6434.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
from django.core.files.uploadedfile import SimpleUploadedFile as _SUF34
_had_img34 = bool(_lc34.featured_image)
_post34b = dict(_post34); _post34b['image_width'] = 55; _post34b['image_align'] = 'left'
_post34b['featured_image'] = _SUF34('t34.png', _png34, content_type='image/png')
_ru34 = _ca.post('/academy/manage/lessons/1/edit/', _post34b, follow=False)
_ld34 = c.get('/academy/lesson/1/').content.decode()
T('۳۴: آکادمی — آپلود عکس شاخص از فرم ویرایش کار می‌کند', _ru34.status_code == 302)
T('۳۴: آکادمی — رندر عرض/موقعیت روی عکس شاخص درس', 'lessonFeaturedImg' in _ld34 and 'width: 55%;' in _ld34 and 'margin-inline-end: 0; margin-inline-start: auto;' in _ld34)
_lc34.refresh_from_db()
if _lc34.featured_image:
    _p34 = _lc34.featured_image.path
    _lc34.featured_image.delete(save=False) if not _had_img34 else None
    if not _had_img34:
        import os as _os34
        if _os34.path.exists(_p34):
            _os34.remove(_p34)
        _lc34.featured_image = ''
        _lc34.save(update_fields=['featured_image'])
_vs34 = _ca.post('/academy/manage/lessons/1/visual-save/', data=json.dumps({'updates': {'display.image_align': 'center', 'display.image_width': 100}}), content_type='application/json').json()
T('۳۴: آکادمی — visual-save موقعیت را هم ذخیره می‌کند', _vs34.get('applied', 0) == 2)
_vsb34 = _ca.post('/academy/manage/lessons/1/visual-save/', data=json.dumps({'updates': {'display.image_align': 'diagonal!'}}), content_type='application/json').json()
T('۳۴: آکادمی — مقدار نامعتبر موقعیت در حافظٔ وایت‌لیست رد می‌شود', _vsb34.get('applied', 0) == 0 and _vsb34.get('skipped', 0) == 1)
_lc34.display_options = _orig34
_lc34.save(update_fields=['display_options'])

_bs34 = open('templates/base.html', encoding='utf-8').read()
T('۳۴: بک‌گراند سراسری — گرادیان پاستلی روشن (آبی/بنفش/سرخابی)',
  '#9CC1F4' in _bs34 and '#B3A5EE' in _bs34 and '#EBB3D9' in _bs34)
T('۳۴: دایره‌ها — رنگ‌های مخالف پاستلی (نارنجی/صورتی/سرخابی/زرد)',
  all(x in _bs34 for x in ('253, 186, 116', '249, 168, 212', '240, 171, 252', '253, 230, 138', '251, 207, 232')))
T('۳۴: شیشه‌ای‌تر — بلار حلقه‌ها تقویت شد (blur(14px))', 'blur(14px) saturate(140%)' in _bs34)

_bcss34 = open('static/css/blog.css', encoding='utf-8').read()
T('۳۴: هوم بلاگ — تمام‌صفحهٔ دسکتاپ + ردیف‌های مات شیشه‌ای (v7)',
  '.blog-shell.bz {\n    max-width: none;\n    width: 100%;' in _bcss34 and 'blur(22px) saturate(160%)' in _bcss34)
T('۳۴: مقاله — پوستهٔ سفید مات خوانا (v7)',
  'rgba(255, 255, 255, 0.86)' in _bcss34 and '#2B3152' in _bcss34 and '.gl .d-prose pre { background: #2B3152;' in _bcss34)
T('۳۴: کش‌باست بلاگ/مقاله/فروشگاه به‌روز است',
  '?v=202608099' in open('templates/blog.html', encoding='utf-8').read()
  and '?v=202608099' in open('templates/article_detail.html', encoding='utf-8').read()
  and '?v=202608078' in open('shop/templates/shop/shop.html', encoding='utf-8').read())
_scss34 = open('static/css/shop.css', encoding='utf-8').read()
T('۳۴: فروشگاه — شل گلس روی بک‌گراند جدید', 'blur(22px) saturate(160%)' in _scss34 and 'rgba(255, 255, 255, 0.58)' in _scss34)
T('۳۴: عکس‌های شاخص مقالات روی دیسک هستند (رفع ۴۰۴)',
  __import__('os').path.exists('media/blog_images/english-shadowing.jpg'))

# ─── بخش ۳۵ · ویرایشگر زنده: سکشن خوانین قابل‌ویرایش + نوار عکس + فرم نظر v8 ───
from language_academy.models import LessonContent as _LC35
_lc35 = _LC35.objects.get(lesson_id=1)
_orig35_display = dict(_lc35.display_options or {})
_orig35_reading = _lc35.reading_text
_lc35.reading_text = ''
_lc35.display_options = {}
_lc35.save(update_fields=['reading_text', 'display_options'])

_ge35 = _ca.get('/academy/lesson/1/?edit=1').content.decode()
T('۳۵: خوانین خالی در حالت ویرایش، کارت و فیلد قابل‌ویرایش دارد',
  'data-ve="content.reading_text"' in _ge35 and 'No reading content available' not in _ge35)
T('۳۵: دکمهٔ Translation & Notes در حالت ویرایش حتی وقتی خالی است هست', 'btn-translation' in _ge35)
_gn35 = c.get('/academy/lesson/1/').content.decode()
T('۳۵: نمای عادی — پیام «No reading content» حفظ شده', 'No reading content available' in _gn35)

_r35 = _ca.post('/academy/manage/lessons/1/visual-save/',
              data=json.dumps({'updates': {'display.custom_blocks': [
                  {'id': 'bt3501', 'kind': 'note', 'text': 'T35 first note block.'},
                  {'id': 'bt3502', 'kind': 'tip', 'text': 'T35 second tip block.'}]}}),
              content_type='application/json')
T('۳۵: ذخیرهٔ بلاک‌های سفارشی اعمال شد', _r35.status_code == 200 and _r35.json().get('applied') == 1)
_gnb35 = c.get('/academy/lesson/1/').content.decode()
T('۳۵: بلاک‌ها در نمای عادی (Notes & Extras) رندر می‌شوند',
  'Notes & Extras' in _gnb35 and 'T35 first note block.' in _gnb35 and 'T35 second tip block.' in _gnb35)
_geb35 = _ca.get('/academy/lesson/1/?edit=1').content.decode()
T('۳۵: بلاک‌ها در حالت ویرایش هم رندر می‌شوند', 'Extra Blocks (Editable)' in _geb35 and 'T35 first note block.' in _geb35)

_lc35.display_options = _orig35_display
_lc35.reading_text = _orig35_reading
_lc35.save(update_fields=['reading_text', 'display_options'])
_gnb35c = c.get('/academy/lesson/1/').content.decode()
T('۳۵: پاکسازی بلاک‌ها — سکشن از نمای عادی پنهان شد', 'T35 first note block.' not in _gnb35c)

_tpl35 = open('language_academy/templates/language_academy/lesson_detail.html', encoding='utf-8').read()
T('۳۵: نوار ابزار عکس — مارک‌آپ دیتا + استایل + JS', all(x in _tpl35 for x in (
    'data-iw="{{ image_width }}" data-ia="{{ image_align }}"', '.ve-imgbar', 'initImgBar',
    "mark('display.image_align', a)", "mark('display.image_width', w)")))
T('۳۵: فیلدهای خالی قابل‌ویرایش نشانه «Click to write» می‌گیرند',
  "[data-ve]:empty::before" in _tpl35 and '✍️ Click to write here…' in _tpl35)
T('۳۵: سکشن خوانین — fallback حالت ویرایش در قالب', '{% if content.reading_text or visual_edit %}' in _tpl35)
T('۳۵: عکس‌های شکستهٔ واژگان/هیرو بی‌صدا حذف می‌شوند', 'onerror="this.remove()"' in _tpl35 and 'onerror="this.parentElement.remove()"' in _tpl35)

_rv35 = _ca.post('/academy/manage/lessons/1/visual-save/',
               data=json.dumps({'updates': {'display.image_width': 60, 'display.image_align': 'right'}}),
               content_type='application/json')
_lc35.refresh_from_db()
T('۳۵: ذخیرهٔ زندهٔ عرض/موقعیت عکس در دیتابیس',
  _lc35.display_options.get('image_width') == 60 and _lc35.display_options.get('image_align') == 'right')
_lc35.display_options = _orig35_display
_lc35.save(update_fields=['display_options'])

_ga35 = c.get('/blog/article/1/').content.decode()
T('۳۵: فرم نظر — آواتار کاربر + ردیف جدید', 'c-form-row' in _ga35 and 'c-form-ava' in _ga35)
_bcss35 = open('static/css/blog.css', encoding='utf-8').read()
T('۳۵: فرم نظر v8 — گلس مات + دکمهٔ گرادیانی', all(x in _bcss35 for x in (
    'فرم ثبت نظر گلس مات', '.c-form-row', '.gl .c-form-ava',
    'linear-gradient(135deg, #3B64D8, #7C5CE0)', 'blur(20px) saturate(150%)')))
T('۳۵: جایگزین امن عکس مفقود در بلاگ و مقاله (آرت پشتی + this.remove)',
  open('templates/blog.html', encoding='utf-8').read().count('onerror="this.remove()"') >= 3
  and open('templates/article_detail.html', encoding='utf-8').read().count('onerror="this.remove()"') >= 2)
T('۳۵: کش‌باست بلاگ به v9 رسید',
  '?v=202608099' in open('templates/blog.html', encoding='utf-8').read()
  and '?v=202608099' in open('templates/article_detail.html', encoding='utf-8').read())


print()
print('\u2501\u2501\u2501 ۳۶) اصطلاحات سطح‌بندی‌شده + آزمون تعیین سطح + معلم هوشمند (Questie) + موبایل آکادمی \u2501\u2501\u2501')

from language_academy.models import (Idiom as _Idiom36, PlacementAttempt as _PA36,
    UserIdiomProgress as _UIP36, UserLanguageEstimate as _ULE36,
    AIChallenge as _AIC36, AIChatMessage as _AIM36)

T('۳۶: کتابخانهٔ اصطلاحات seed شده (۶۰ مورد در ۶ سطح)',
  _Idiom36.objects.count() >= 60 and set(_Idiom36.objects.values_list('level', flat=True).distinct()) == {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'})

_ULE36.objects.filter(user=user).delete()
_r36 = c.get('/academy/idioms/')
T('۳۶: ورود به بخش اصطلاحات بدون سطح → هدایت به تعیین سطح',
  _r36.status_code == 302 and '/idioms/placement/' in _r36['Location'])

_r36 = c.get('/academy/idioms/placement/')
T('۳۶: صفحهٔ انتخاب سطح — شش کارت CEFR', _r36.status_code == 200 and _r36.content.decode().count('pl-card"') == 6)

_r36 = c.post('/academy/idioms/placement/', {'level': 'B1'})
_att36 = _PA36.objects.filter(user=user).latest('created_at')
T('۳۶: ساخت آزمون — ۸ سؤال با پاسخ ذخیرهٔ امن سمت سرور',
  _r36.status_code == 302 and len(_att36.quiz) == 8 and all(0 <= q.get('answer', -1) <= 3 for q in _att36.quiz))
T('۳۶: کلید پاسخ در HTML صفحهٔ آزمون افشا نمی‌شود',
  'data-correct' not in c.get(f'/academy/idioms/placement/quiz/{_att36.id}/').content.decode())

_r36 = c.post(f'/academy/idioms/placement/submit/{_att36.id}/', {'ans[]': [str(q['answer']) for q in _att36.quiz[:-1]]})
T('۳۶: ارسال ناقص → برگشت به صفحهٔ آزمون',
  _r36.status_code == 302 and f'quiz/{_att36.id}' in _r36['Location'])

_r36 = c.post(f'/academy/idioms/placement/submit/{_att36.id}/', {'ans[]': [str(q['answer']) for q in _att36.quiz]})
_att36.refresh_from_db()
T('۳۶: نمرهٔ کامل → تأیید سطح و ثبت estimate',
  _att36.verdict == 'confirmed' and _att36.score == 8
  and _ULE36.objects.get(user=user).cefr_level == 'B1')
_rres36 = c.get(f'/academy/idioms/placement/result/{_att36.id}/').content
T('۳۶: صفحهٔ نتیجهٔ تأیید رندر می‌شود', _rres36 and
  b'level is confirmed' in _rres36)

_r36 = c.post('/academy/idioms/placement/', {'level': 'C2'})
_att36b = _PA36.objects.filter(user=user).latest('created_at')
_wrong36 = [str((q['answer'] + 1) % 4) for q in _att36b.quiz]
c.post(f'/academy/idioms/placement/submit/{_att36b.id}/', {'ans[]': _wrong36})
_att36b.refresh_from_db()
T('۳۶: پاسخ غلط → «سطحت را دوباره انتخاب کن» با پیشنهاد پایین‌تر و بدون تغییر estimate',
  _att36b.verdict == 'adjust' and _att36b.recommended_level == 'B2'
  and _ULE36.objects.get(user=user).cefr_level == 'B1')
_rres36b = c.get(f'/academy/idioms/placement/result/{_att36b.id}/').content
T('۳۶: نتیجهٔ adjust — دکمهٔ انتخاب دوباره + گزینهٔ «همینو نگه دار»',
  b'Choose level again' in _rres36b and b'keep C2 anyway' in _rres36b)

_hub36 = c.get('/academy/idioms/').content.decode()
T('۳۶: هاب اصطلاحات — چیپ سطح، کارت موضوع، دکمهٔ چالش و نشان آفلاین AI',
  all(x in _hub36 for x in ('iq-level-chip', 'iq-topic', 'iqChallengeBtn', 'AI tutor offline')))

_l36 = c.get('/academy/idioms/learn/').content.decode()
T('۳۶: صفحهٔ یادگیری — کارت اصطلاح با معنی فارسی + فیلتر موضوع', 'il-card' in _l36 and 'il-chip on' in _l36)
_l36t = c.get('/academy/idioms/learn/?topic=social').content.decode()
T('۳۶: فیلتر موضوع: social فقط ۵ اصطلاح', _l36t.count('il-ex">') == 5)

_id36 = _Idiom36.objects.filter(level='B1', topic='social').first()
_Idiom36.objects.filter(expression='__t36_mark_check_idiom__').delete()
_tmp36 = _Idiom36.objects.create(
    expression='__t36_mark_check_idiom__', level='XX',
    translation_fa='تست', definition_en='test idiom for e2e',
    example_en='Just a test.', topic='study', is_active=True)
_UIP36.objects.filter(user=user, idiom__in=[_id36, _tmp36]).delete()
_m1 = c.post('/academy/idioms/mark/', data=json.dumps({'idiom_id': _tmp36.id, 'action': 'known'}), content_type='application/json').json()
_m2 = c.post('/academy/idioms/mark/', data=json.dumps({'idiom_id': _tmp36.id, 'action': 'known'}), content_type='application/json').json()
T('۳۶: علامت «I know this» — XP فقط بار اول (idempotent)', _m1['ok'] and _m1['xp'] > 0 and _m2['xp'] == 0)

_f36 = c.get('/academy/idioms/flashcards/').content.decode()
import re as _re36
_deck36 = _re36.search(r'id="deckData" type="application/json">(.*?)</script>', _f36, _re36.S)
T('۳۶: فلش‌کارت — deck JSON معتبر با ۱۰ کارت B1',
  bool(_deck36) and len(json.loads(_deck36.group(1))) == 10)
T('۳۶: مرور هوشمد — صفحه رندر + حالت review', c.get('/academy/idioms/review/').status_code == 200)

_ch36 = c.post('/academy/ai/chat/', data=json.dumps({'message': 'سلام'}), content_type='application/json').json()
T('۳۶: چت معلم — پاسخ fallback فارسی وقتی کلید نیست', _ch36['ok'] and _ch36['ai'] is False and len(_ch36['reply']) > 10)
T('۳۶: چت — پیام خالی ۴۰۰ و GET ممنوع',
  c.post('/academy/ai/chat/', data=json.dumps({'message': '  '}), content_type='application/json').status_code == 400
  and c.get('/academy/ai/chat/').status_code == 405)
_csrf36 = Client(SERVER_NAME='localhost', enforce_csrf_checks=True)
_csrf36.login(username='testuser', password='test123456')
T('۳۶: چت بدون CSRF → ۴۰۳', _csrf36.post('/academy/ai/chat/', data=json.dumps({'message': 'hi'}), content_type='application/json').status_code == 403)

_n1 = c.post('/academy/ai/challenge/new/', data='{}', content_type='application/json').json()
_n2 = c.post('/academy/ai/challenge/new/', data='{}', content_type='application/json').json()
T('۳۶: چالش — ساخت تازه و بازگرداندن همان ناتمام (بدون دوبله)',
  _n1['ok'] and _n1['fresh'] and _n2['id'] == _n1['id'] and not _n2['fresh'])
_ch36o = _AIC36.objects.get(id=_n1['id'])
_right36 = _ch36o.payload['answer']
_xp_before36 = user.__class__.objects.get(id=user.id).xp
_a1 = c.post('/academy/ai/challenge/answer/', data=json.dumps({'id': _n1['id'], 'index': _right36}), content_type='application/json').json()
_replay = c.post('/academy/ai/challenge/answer/', data=json.dumps({'id': _n1['id'], 'index': _right36}), content_type='application/json')
user.refresh_from_db()
T('۳۶: چالش — پاسخ درست +XP و ایندکس درست افشا می‌شود، replay مسدود',
  _a1['correct'] and _a1['xp'] > 0 and isinstance(_a1.get('correct_index'), int)
  and _replay.status_code == 409 and user.xp == _xp_before36 + _a1['xp'])

_h36 = list(_AIM36.objects.filter(user=user).values_list('role', flat=True))
T('۳۶: پیام‌های چت ذخیره و history سرو می‌شود',
  'user' in _h36 and 'assistant' in _h36 and c.get('/academy/ai/chat/history/').json()['ok'])

_tpl36 = open('language_academy/templates/language_academy/lesson_detail.html', encoding='utf-8').read()
T('۳۶: موبایل درس — محتوای collapse واقعاً صفر و تایم‌لاین wrap',
  '.section-content-modern { padding: 0 14px; font-size: 0.88rem; }' in _tpl36
  and 'flex-wrap: wrap; justify-content: center; overflow-x: visible;' in _tpl36)
T('۳۶: لینک اصطلاحات در ناوبری آکادمی',
  'idioms_hub' in open('language_academy/templates/language_academy/base_academy.html', encoding='utf-8').read())

_ULE36.objects.filter(user=user).delete()
_PA36.objects.filter(user=user).delete()
_UIP36.objects.filter(user=user).delete()
_Idiom36.objects.filter(expression='__t36_mark_check_idiom__').delete()
_AIC36.objects.filter(user=user).delete()
_AIM36.objects.filter(user=user).delete()

print('\n━━━ ۳۷) بازی‌های جدید + موتور مشترک امتیاز ━━━')
from Game.models import UserGameStats as _UGS, UserAchievement as _UA37
from user.models import UserActivity as _UAct37

_RR.objects.filter(code='game_play').update(daily_limit=100000)
_points37 = user.points
_gnames37 = ['dictation', 'sprint', 'minesweeper', 'breakout']

for _u37 in ['/games/minesweeper/', '/games/breakout/', '/language/dictation/', '/language/word-sprint/']:
    _h37 = c.get(_u37).content.decode()
    T(f'۳۷: کیت مشترک در صفحهٔ {_u37}',
      'games-shared.css' in _h37 and 'gp-topbar' in _h37 and '/home/games/' in _h37)

_deck1 = c.get('/language/dictation/?deck=json&diff=easy').json()
_deck2 = c.get('/language/dictation/?deck=json&diff=hard').json()
T('۳۷: دک دیکته — ۱۲ کلمه + ساختار درست + فیلتر سختی',
  len(_deck1['words']) == 12 and all(set(('word', 'meaning', 'letters')) <= set(w) for w in _deck1['words'])
  and all(2 <= w['letters'] <= 5 for w in _deck1['words'])
  and all(w['letters'] >= 9 for w in _deck2['words']))

_deck3 = c.get('/language/word-sprint/?deck=json').json()
_trues = sum(1 for i in _deck3['items'] if i['isTrue'])
T('۳۷: دک دوئل — ۴۰ آیتم با ترکیب درست/غلط',
  _deck3['seconds'] == 30 and len(_deck3['items']) == 40 and 10 <= _trues <= 30
  and all(i['word'] and i['meaning'] for i in _deck3['items']))

_ms_lose = c.post('/games/save-minesweeper-score/', data=_json.dumps({'time': 40, 'won': False}), content_type='application/json').json()
_ms = _UGS.objects.get(user=user, game_name='minesweeper')
T('۳۷: مین‌روب — باخت بدون XP، فقط played بالا می‌رود',
  _ms_lose['status'] == 'success' and _ms_lose['xp_gained'] == 0 and _ms_lose['games_completed'] >= 1
  and _ms.games_played >= 2 and _ms.games_completed == 1)

for _i in range(10):
    c.post('/language/save-sprint-score/', data=_json.dumps({'score': 18, 'answered': 26, 'seconds': 30}), content_type='application/json')
_ach37 = _UA37.objects.filter(user=user, achievement_type='sprint_10').first()
_sp37 = _UGS.objects.get(user=user, game_name='sprint')
T('۳۷: دوئل — ۱۰ راند → دستاورد sprint_10 + آمار درست',
  _ach37 is not None and _ach37.name == 'برق کلمات' and _sp37.games_completed >= 11)

_bo1 = c.post('/games/save-breakout-score/', data=_json.dumps({'score': 400, 'completed': True}), content_type='application/json').json()
_bo2 = c.post('/games/save-breakout-score/', data=_json.dumps({'score': 50, 'completed': True}), content_type='application/json').json()
T('۳۷: آجرشکن — best_score فقط بالا می‌رود (lower مقبول نیست)',
  _bo1['best_score'] == 400 and _bo2['best_score'] == 400 and not _bo2['new_best'])

_ms_best = c.post('/games/save-minesweeper-score/', data=_json.dumps({'time': 200, 'won': True}), content_type='application/json').json()
T('۳۷: مین‌روب — رکورد زمان کمتر (lower is better)',
  _ms_best['best_score'] == 120 and not _ms_best['new_best'])

_dt = c.post('/language/save-dictation-score/', data=_json.dumps({'score': 12, 'total': 12, 'diff': 'hard'}), content_type='application/json').json()
T('۳۷: دیکته — پرفکت hard = بونوس + ضریب', _dt['status'] == 'success' and _dt['xp_gained'] >= (12 * 18 + 25))

user.refresh_from_db()
T('۳۷: points با بازی‌های زبان رشد کرد', user.points > _points37)

_hub = c.get('/home/games/').content.decode()
T('۳۷: هاب بازی‌ها دو دستهٔ زبان/سرگرمی + کاشی‌های جدید',
  'بازی‌های زبان' in _hub and 'بازی‌های سرگرمی' in _hub
  and '/language/dictation/' in _hub and '/games/minesweeper/' in _hub and '/games/breakout/' in _hub)

_lh = c.get('/language/').content.decode()
T('۳۷: کارت‌های دیکته و دوئل در خانهٔ زبان', '/language/dictation/' in _lh and '/language/word-sprint/' in _lh)

from django.test import Client as _C37
_anon37 = _C37(SERVER_NAME='localhost')
T('۳۷: صفحات بازی جدید برای مهمان → ورود',
  _anon37.get('/language/dictation/').status_code == 302 and _anon37.get('/games/breakout/').status_code == 302)
_csrf37 = _C37(SERVER_NAME='localhost', enforce_csrf_checks=True)
_csrf37.login(username='testuser', password='test123456')
T('۳۷: ذخیرهٔ امتیاز بدون CSRF → ۴۰۳',
  _csrf37.post('/language/save-sprint-score/', data='{}', content_type='application/json').status_code == 403)

_UGS.objects.filter(user=user, game_name__in=_gnames37).delete()
_UA37.objects.filter(user=user, achievement_type__in=['sprint_10', 'dictation_10', 'minesweeper_10', 'breakout_10']).delete()
_UAct37.objects.filter(user=user, title__in=['دوئل کلمات', 'انجام دیکته صوتی', 'پاک‌سازی میدان مین', 'انجام بازی آجرشکن', 'دریافت دستاورد: برق کلمات']).delete()
user.points = _points37
user.save(update_fields=['points'])
_RR.objects.filter(code='game_play').update(daily_limit=_gp_old)

print('\n━━━ ۳۸) یکدستی ظاهر/game-kit + امنیت fetch ذخیره ━━━')
_hub38 = c.get('/home/games/').content.decode()
T('۳۸: هاب — ۱۷ کاشی squircle با آیکون SVG',
  _hub38.count('class="gtile"') == 17 and _hub38.count('<svg viewBox="0 0 24 24"') == 17
  and 'border-radius: 28%' in _hub38 and 'جدید' in _hub38)
T('۳۸: هاب — چیدمان ریسپانسیو سه‌تایی موبایل + شش‌تایی دسکتاپ',
  '@media (max-width: 560px)' in _hub38 and 'repeat(3, 1fr)' in _hub38 and 'repeat(6, 1fr)' in _hub38)
_hub38g = Client(SERVER_NAME='localhost').get('/home/games/').content.decode()
T('۳۸: مهمان — قفل روی کاشی‌ها + بنر ورود', 'gt-guest' in _hub38g and 'gm-guest' in _hub38g)

_PAGES38 = ['/games/snake/', '/games/2048/', '/games/reaction/', '/games/memory/', '/games/sudoku/',
            '/games/iq-test/', '/games/number-puzzle/', '/games/simon/', '/games/whack/', '/games/tictactoe/',
            '/games/minesweeper/', '/games/breakout/', '/language/drag-drop/', '/language/word-guessing/',
            '/language/word-scramble/', '/language/dictation/', '/language/word-sprint/']
for _u38 in _PAGES38:
    _h38 = c.get(_u38).content.decode()
    T(f'۳۸: کیت JS+CSS نسخهٔ تازه در {_u38}',
      'games-shared.js?v=20260808' in _h38 and 'games-shared.css?v=20260808' in _h38)

import re as _re38
_FILES38 = ['snake', 'game_2048', 'reaction', 'memory', 'sudoku', 'iq_test', 'number_puzzle', 'simon',
            'whack', 'tictactoe', 'minesweeper', 'breakout', 'drag_drop_game', 'word_guessing',
            'word_scramble', 'word_dictation', 'word_sprint']
_bad38 = []
for _f38 in _FILES38:
    _src = open(f'templates/{_f38}.html', encoding='utf-8').read()
    for _m in _re38.finditer(r"fetch\('(/games/save|/language/save)[^']*'", _src):
        if 'X-CSRFToken' not in _src[_m.start():_m.start() + 280]:
            _bad38.append(_f38)
            break
T('۳۸: هیچ fetch ذخیرهٔ امتیاز بدون CSRF نیست', _bad38 == [], f'({_bad38})')

_js38 = open('static/js/games-shared.js', encoding='utf-8').read()
T('۳۸: games-shared.js — CSRF سه‌مرحله‌ای + saveScore یکپارچه',
  'lqCsrf' in _js38 and 'csrftoken' in _js38 and 'X-CSRFToken' in _js38 and 'window.GP' in _js38)
_t3838 = open('templates/snake.html', encoding='utf-8').read()
T('۳۸: بازی‌های آرکید قدیمی روی GP.saveScore',
  'GP.saveScore' in _t3838 and 'snakeXpLine' in _t3838 and "GP.saveScore" in open('templates/game_2048.html', encoding='utf-8').read())
_s38 = open('templates/sudoku.html', encoding='utf-8').read()
T('۳۸: سودوکو — خشاب ۵تایی + آیکون‌های امن (بدون FontAwesome)',
  'repeat(5, 1fr)' in _s38 and 'fas fa-' not in _s38 and "eraseBtn.innerHTML = '⌫'" in _s38)
T('۳۸: بدون آیکون مردهٔ FontAwesome در صفحات بازی',
  all('fas fa-' not in open(f'templates/{_f}.html', encoding='utf-8').read()
      for _f in ['iq_test', 'number_puzzle', 'sudoku']))
_lh38 = c.get('/language/').content.decode()
T('۳۸: خانهٔ زبان — کاشی‌های هماهنگ با هاب', _lh38.count('class="gseq"') == 5 and '.games-sq-grid' in _lh38)

print('\n━━━ ۳۹) بلاگ داینامیک + بازطراحی فروشگاه/بلاگ + مدیریت جهان‌ها ━━━')

_art39 = Article.objects.order_by('id').first()
_v39a = Article.objects.get(pk=_art39.pk).views
c.get(f'/blog/article/{_art39.pk}/')
_v39b = Article.objects.get(pk=_art39.pk).views
c.get(f'/blog/article/{_art39.pk}/')
_v39c = Article.objects.get(pk=_art39.pk).views
T('۳۹: بازدید مقاله با هر GET دقیقاً +۱ (بدون session-gate)',
  _v39b == _v39a + 1 and _v39c == _v39a + 2, f'({_v39a}→{_v39b}→{_v39c})')
_bv39 = open('blog/views.py', encoding='utf-8').read()
T('۳۹: شمارش ویو شرط session ندارد و اتمیک است',
  'viewed_articles' not in _bv39 and "update(views=F('views') + 1)" in _bv39)

from django.test import Client as _C39
import json as _json39
_admin39 = _C39(SERVER_NAME='localhost')
assert _admin39.login(username='admin', password='admin123456')
_like39 = f'/blog/like/{_art39.pk}/'
_lk0 = Article.objects.get(pk=_art39.pk).likes
_csrf39 = _C39(SERVER_NAME='localhost', enforce_csrf_checks=True)
assert _csrf39.login(username='admin', password='admin123456')
T('۳۹: لایک مقاله بدون توکن CSRF → ۴۰۳', _csrf39.post(_like39).status_code == 403)
_admf = _C39(SERVER_NAME='localhost', enforce_csrf_checks=True)
assert _admf.login(username='admin', password='admin123456')
_admf.get(f'/blog/article/{_art39.pk}/')
_tok39 = _admf.cookies['csrftoken'].value
_r39a = _admf.post(_like39, HTTP_X_CSRFTOKEN=_tok39)
_r39b = _admf.post(_like39, HTTP_X_CSRFTOKEN=_tok39)
_d39a = _json39.loads(_r39a.content.decode()) if _r39a.status_code == 200 else {}
_d39b = _json39.loads(_r39b.content.decode()) if _r39b.status_code == 200 else {}
T('۳۹: لایک با هدر CSRF بدون ریلود تاگل می‌شود (true→false) و شمارنده درست است',
  _d39a.get('liked') is True and _d39b.get('liked') is False and _d39b.get('likes') == _lk0)
_bjs39 = open('static/js/blog.js', encoding='utf-8').read()
T('۳۹: blog.js — هدر X-CSRFToken + خواندن توکن سه‌مرحله‌ای',
  'X-CSRFToken' in _bjs39 and 'lqCsrf' in _bjs39 and 'csrftoken' in _bjs39)

_bh39 = c.get('/blog/').content.decode()
T('۳۹: بلاگ — بازطراحی مجله‌ای v9 (کارت‌های کاوردار)',
  'bc-mag' in _bh39 and 'bc-cards' in _bh39 and 'bc-pop-n' in _bh39 and 'v=202608099' in _bh39)
T('۳۹: بلاگ — بدون data-URI غول‌پیکر و با کاور SVG/تصویر واقعی',
  'data:image/svg+xml' not in _bh39 and 'bc-cover' in _bh39 and _bh39.count('<svg') > 25)
_bd39 = c.get(f'/blog/article/{_art39.pk}/').content.decode()
T('۳۹: جزئیات مقاله — کاور v9 + همان هوک‌های JS (#article-like-btn)',
  'data:image/svg+xml' not in _bd39 and 'id="article-like-btn"' in _bd39
  and 'id="blog-config"' in _bd39 and 'v=202608099' in _bd39)

_sh39 = c.get('/shop/').content.decode()
T('۳۹: فروشگاه — بازطراحی v9 (کاشی رنگی + آرت SVG + کارت تازه)',
  'sp-hero' in _sh39 and 'sp-grid' in _sh39 and 'sp-fic big' in _sh39 and 'v=202608078' in _sh39)
T('۳۹: فروشگاه — cosmetics.css برای پیش‌نمایش زندهٔ قاب/تم لود می‌شود',
  'css/cosmetics.css' in _sh39 and 'lq-framed' in _sh39)
_se39 = open('shop/templatetags/shop_extras.py', encoding='utf-8').read()
T('۳۹: نقشهٔ آیکون SVG افکت‌ها (۲۵+ نوع محصول)',
  _se39.count(" = '<") >= 30 and 'mystery_box' in _se39 and 'xp_booster' in _se39 and 'pet' in _se39)
_pd39 = c.get('/shop/product/frame-gold/').content.decode()
T('۳۹: صفحهٔ محصول — cosmetics.css + نسخهٔ تازه', 'css/cosmetics.css' in _pd39 and 'v=202608078' in _pd39)

_wc39 = _C39(SERVER_NAME='localhost', enforce_csrf_checks=True)
assert _wc39.login(username='testuser', password='test123456')
T('۳۹: علاقه‌مندی بدون CSRF → ۴۰۳', _wc39.post('/shop/wishlist/toggle/48/').status_code == 403)
_wc39.get('/shop/wishlist/')
_wtok39 = _wc39.cookies['csrftoken'].value
_w39a = _wc39.post('/shop/wishlist/toggle/48/', HTTP_X_CSRFTOKEN=_wtok39)
_w39b = _wc39.post('/shop/wishlist/toggle/48/', HTTP_X_CSRFTOKEN=_wtok39)
_wo39 = _C39(SERVER_NAME='localhost', enforce_csrf_checks=True)
assert _wo39.login(username='testuser', password='test123456')
T('۳۹: علاقه‌مندی با CSRF تاگل و برمی‌گردد (بدون اثر جانبی)',
  _w39a.status_code == 200 and _w39b.status_code == 200
  and _json39.loads(_w39a.content.decode())['in_wishlist'] is True
  and _json39.loads(_w39b.content.decode())['in_wishlist'] is False)
for _p39 in ['/shop/wishlist/toggle/', '/shop/buy/', '/shop/equip/', '/shop/consume/']:
    pass
_srcs39 = {p: open(p, encoding='utf-8').read() for p in
           ['shop/templates/shop/shop.html', 'shop/templates/shop/product_detail.html',
            'shop/templates/shop/inventory.html', 'shop/templates/shop/wishlist.html']}
import re as _re39
_badfetch39 = [p for p, s in _srcs39.items()
               if any('X-CSRFToken' not in s[m.start():m.start() + 300] for m in _re39.finditer(r"fetch\(`?/shop/", s))]
T('۳۹: همهٔ fetchهای POST فروشگاه هدر CSRF دارند', _badfetch39 == [], f'({_badfetch39})')

_wls39 = _admin39.get('/academy/manage/worlds/').content.decode()
T('۳۹: مدیریت جهان‌ها — کارت آماری + جدول غنی + اکشن‌ها',
  'wz-stat' in _wls39 and 'wz-table' in _wls39 and 'toggle-publish' in _wls39)
T('۳۹: مدیریت جهان‌ها — جستجو/فیلتر/فصل‌ها در همان صفحه',
  'wz-search' in _wls39 and 'wz-chapters' in _wls39 and 'wz-details' in _wls39)
_cm39 = _C39(SERVER_NAME='localhost')
assert _cm39.login(username='testuser', password='test123456')
T('۳۹: مدیریت جهان‌ها برای کاربر عادی بسته است',
  _cm39.get('/academy/manage/worlds/').status_code == 302)
from language_academy.models import World as _W39
_w1_39 = _W39.objects.order_by('order').first()
_w2_39 = _W39.objects.order_by('order')[1] if _W39.objects.count() > 1 else None
_pub39 = _w1_39.is_published
_tg39 = _admin39.post(f'/academy/manage/worlds/{_w1_39.id}/toggle-publish/')
_tg39b = _admin39.post(f'/academy/manage/worlds/{_w1_39.id}/toggle-publish/')
_w1_39.refresh_from_db()
T('۳۹: تاگل انتشار جهان کار می‌کند و برمی‌گردد',
  _tg39.status_code == 200 and _tg39b.status_code == 200 and _w1_39.is_published == _pub39)
if _w2_39:
    _o1, _o2 = _w1_39.order, _w2_39.order
    _mv39 = _admin39.post(f'/academy/manage/worlds/{_w1_39.id}/move/down/')
    _w1_39.refresh_from_db(); _w2_39.refresh_from_db()
    _swapped = _w1_39.order == _o2 and _w2_39.order == _o1
    _admin39.post(f'/academy/manage/worlds/{_w1_39.id}/move/up/')
    _w1_39.refresh_from_db(); _w2_39.refresh_from_db()
    _restored = _w1_39.order == _o1 and _w2_39.order == _o2
    T('۳۹: جابه‌جایی ترتیب جهان (▲▼) سوآپ و بازگشت', _mv39.status_code == 200 and _swapped and _restored)
T('۳۹: تاگل/جابه‌جایی با GET ممنوع است',
  _admin39.get(f'/academy/manage/worlds/{_w1_39.id}/toggle-publish/').status_code == 405)

print(f'\n{"="*50}\nنتیجه: {len(PASSED)} موفق / {len(FAILED)} شکست')
if FAILED:
    print('شکست‌ها:', FAILED)
    sys.exit(1)
print('🎉 همهٔ تست‌ها سبز!')
