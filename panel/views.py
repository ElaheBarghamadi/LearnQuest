import json
import re
import uuid
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from Home.jalali import jalali_date, jalali_date_long, jalali_human, fa_digits
from .models import PanelAdjustment

User = get_user_model()

MAX_ADJUST = 1_000_000
IDEM_RE = re.compile(r'^[A-Za-z0-9_:\-]{6,80}$')
ECONOMY_TARGETS = {'coins': 'coin', 'gems': 'gem', 'xp': 'xp'}
FIELD_TARGETS = ['coins', 'gems', 'xp', 'points', 'streak']
PAGE_SIZE = 15


def _client_ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@staff_member_required
def dashboard(request):
    from blog.models import Article, Comment
    from Messenger.models import Conversation, Message
    from economy.models import Transaction, Wallet
    from shop.models import Product, Purchase

    now = timezone.now()
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    agg = Wallet.objects.aggregate(c=Sum('coins'), g=Sum('gems'))
    stats = {
        'users_total': User.objects.count(),
        'users_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'users_active': User.objects.filter(is_active=True).count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
        'articles': Article.objects.count(),
        'comments': Comment.objects.count(),
        'conversations': Conversation.objects.count(),
        'messages': Message.objects.count(),
        'products_active': Product.objects.filter(is_active=True).count(),
        'purchases_24h': Purchase.objects.filter(created_at__gte=day_ago).count(),
        'tx_24h': Transaction.objects.filter(created_at__gte=day_ago).count(),
        'coins_total': agg['c'] or 0,
        'gems_total': agg['g'] or 0,
        'xp_total': User.objects.aggregate(x=Sum('xp'))['x'] or 0,
    }
    recent_users = User.objects.order_by('-date_joined')[:6]
    recent_adjustments = (PanelAdjustment.objects
                          .select_related('user', 'actor')[:8])
    recent_tx = (Transaction.objects.select_related('user', 'actor')[:8])
    recent_tx = list(recent_tx)
    for t in recent_tx:
        t.jcreated = jalali_human(t.created_at)
    top_users = User.objects.filter(is_active=True).order_by('-xp')[:5]
    return render(request, 'panel/dashboard.html', {
        'stats': stats,
        'recent_users': recent_users,
        'recent_adjustments': recent_adjustments,
        'recent_tx': recent_tx,
        'top_users': top_users,
        'today_jalali': jalali_date_long(now),
        'active_tab': 'dashboard',
    })


@staff_member_required
def users_list(request):
    q = request.GET.get('q', '').strip()
    qs = User.objects.order_by('-date_joined')
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q)
                       | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    from economy.models import Wallet
    wallets = {w.user_id: w for w in Wallet.objects.filter(user__in=page_obj.object_list)}
    rows = []
    for u in page_obj.object_list:
        w = wallets.get(u.pk)
        rows.append({'user': u, 'coins': w.coins if w else 0, 'gems': w.gems if w else 0})
    return render(request, 'panel/users.html', {
        'rows': rows,
        'page_obj': page_obj,
        'paginator': paginator,
        'q': q,
        'active_tab': 'users',
    })


def _user_context(target):
    from economy.models import Transaction, Wallet
    from shop.models import InventoryItem, Product

    wallet, _ = Wallet.objects.get_or_create(user=target)
    target.jalali_joined = jalali_date_long(target.date_joined)
    target.jalali_last_login = jalali_human(target.last_login)
    adjustments = (PanelAdjustment.objects.filter(user=target)
                   .select_related('actor')[:12])
    transactions = (Transaction.objects.filter(user=target)
                    .select_related('actor')[:12])
    transactions = list(transactions)
    for t in transactions:
        t.jcreated = jalali_human(t.created_at)
    inventory_count = InventoryItem.objects.filter(user=target).count()
    products = (Product.objects.filter(is_active=True)
                .select_related('category').order_by('category__order', 'name')[:200])
    return {
        'target': target,
        'wallet': wallet,
        'adjustments': adjustments,
        'transactions': transactions,
        'inventory_count': inventory_count,
        'products': products,
        'level_progress': int(target.get_level_progress() or 0),
        'active_tab': 'users',
    }


@staff_member_required
def user_detail(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)
    return render(request, 'panel/user_detail.html', _user_context(target))


def _parse_body(request):
    try:
        return json.loads(request.body or b'{}'), None
    except json.JSONDecodeError:
        return None, JsonResponse({'ok': False, 'error': 'فرمت JSON نامعتبر است'}, status=400)


def _idem_from(body):
    idem = str(body.get('idem') or '').strip()
    if not IDEM_RE.match(idem):
        idem = uuid.uuid4().hex
    return idem


def _adjust_log(*, user, actor, target, amount, note, idem, extra=None):
    try:
        with transaction.atomic():
            PanelAdjustment.objects.create(
                user=user, actor=actor, target=target, amount=amount,
                note=note[:220], extra=extra or {}, idempotency_key=f'adj:{idem}'[:100])
        return False
    except IntegrityError:
        return True


@staff_member_required
@require_POST
def grant(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)
    body, err = _parse_body(request)
    if err:
        return err
    kind = str(body.get('target') or '').strip()
    note = str(body.get('note') or '').strip()
    try:
        amount = int(body.get('amount'))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'مقدار باید عدد صحیح باشد'}, status=400)
    if kind not in FIELD_TARGETS:
        return JsonResponse({'ok': False, 'error': 'نوع مورد نامعتبر است'}, status=400)
    if amount == 0:
        return JsonResponse({'ok': False, 'error': 'مقدار نمی‌تواند صفر باشد'}, status=400)
    if abs(amount) > MAX_ADJUST:
        return JsonResponse({'ok': False, 'error': f'سقف هر اقدام {fa_digits(MAX_ADJUST)} است'}, status=400)
    if len(note) > 220:
        return JsonResponse({'ok': False, 'error': 'دلیل خیلی طولانی است'}, status=400)

    idem = _idem_from(body)

    if kind in ECONOMY_TARGETS:
        from economy.services import admin_adjust, audit
        from economy.context_processors import invalidate_wallet_cache
        result = admin_adjust(target, ECONOMY_TARGETS[kind], amount, actor=request.user,
                              reason=note, idempotency_key=f'panel:{idem}')
        target.refresh_from_db(fields=['xp', 'level'])
        invalidate_wallet_cache(target)
        audit('panel.grant', user=target, actor=request.user, ip=_client_ip(request),
              details={'target': kind, 'amount': amount, 'note': note, 'idem': idem,
                       'ok': bool(result.get('ok'))})
        if not result.get('ok'):
            if result.get('duplicate'):
                return JsonResponse({'ok': True, 'duplicate': True,
                                     'error': 'تراکنش تکراری شناسایی شد؛ دوباره اعمال نشد'})
            if result.get('error') == 'insufficient':
                return JsonResponse({'ok': False, 'error': 'insufficient',
                                     'have': result.get('have', 0)}, status=400)
            return JsonResponse({'ok': False, 'error': 'اعمال نشد'}, status=400)
        _adjust_log(user=target, actor=request.user, target=kind, amount=amount,
                    note=note, idem=idem,
                    extra={'balance': result.get('balance')})
        from economy.models import Wallet
        wallet = Wallet.objects.filter(user=target).first()
        return JsonResponse({
            'ok': True, 'target': kind, 'amount': amount,
            'coins': wallet.coins if wallet else 0,
            'gems': wallet.gems if wallet else 0,
            'xp': target.xp, 'level': target.level,
            'progress': int(target.get_level_progress() or 0),
        })

    if _adjust_log(user=target, actor=request.user, target=kind, amount=amount,
                   note=note, idem=idem):
        return JsonResponse({'ok': True, 'duplicate': True,
                             'error': 'این درخواست قبلاً ثبت شده؛ دوباره اعمال نشد'})
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=target.pk)
        cur = getattr(locked, kind) or 0
        new_val = max(0, cur + amount)
        setattr(locked, kind, new_val)
        locked.save(update_fields=[kind])
    from economy.services import audit
    audit('panel.grant_field', user=target, actor=request.user, ip=_client_ip(request),
          details={'target': kind, 'amount': amount, 'note': note, 'idem': idem})
    return JsonResponse({'ok': True, 'target': kind, 'amount': amount, 'value': new_val})


@staff_member_required
@require_POST
def grant_item(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)
    body, err = _parse_body(request)
    if err:
        return err
    try:
        product_id = int(body.get('product_id'))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'محصول نامعتبر است'}, status=400)
    note = str(body.get('note') or '').strip()[:220]
    idem = _idem_from(body)

    from shop.models import Product
    from shop.services import grant_product_item
    product = Product.objects.filter(pk=product_id, is_active=True).first()
    if not product:
        return JsonResponse({'ok': False, 'error': 'محصول یافت نشد یا غیرفعال است'}, status=404)

    if _adjust_log(user=target, actor=request.user, target='item', amount=1, note=note,
                   idem=idem, extra={'product_id': product.pk, 'slug': product.slug,
                                     'name': product.name}):
        return JsonResponse({'ok': True, 'duplicate': True,
                             'error': 'این درخواست قبلاً ثبت شده؛ دوباره اعمال نشد'})

    res = grant_product_item(target, product.slug, source='admin_panel')
    from economy.services import audit
    audit('panel.grant_item', user=target, actor=request.user, ip=_client_ip(request),
          details={'product': product.slug, 'note': note, 'idem': idem,
                   'ok': bool(res.get('ok'))})
    if not res.get('ok'):
        return JsonResponse({'ok': False, 'error': res.get('error', 'اعمال نشد')}, status=400)
    return JsonResponse({'ok': True, 'product': product.name})


@staff_member_required
@require_http_methods(['POST'])
def toggle_active(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk:
        return JsonResponse({'ok': False, 'error': 'نمی‌توانید حساب خودتان را تعلیق کنید'}, status=400)
    if target.is_superuser and not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'تغییر وضعیت سوپریوزر فقط برای سوپریوزر مجاز است'}, status=403)

    body, err = _parse_body(request)
    if err:
        return err
    idem = _idem_from(body)
    want_active = body.get('is_active')
    if _adjust_log(user=target, actor=request.user, target='status',
                   amount=0, note='', idem=idem,
                   extra={'requested': want_active}):
        return JsonResponse({'ok': True, 'duplicate': True, 'is_active': target.is_active})
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=target.pk)
        locked.is_active = (not locked.is_active) if want_active is None else bool(want_active)
        locked.save(update_fields=['is_active'])
        PanelAdjustment.objects.filter(idempotency_key=f'adj:{idem}'[:100]).update(
            amount=1 if locked.is_active else -1,
            note='فعال‌سازی حساب' if locked.is_active else 'تعلیق حساب',
            extra={'is_active': locked.is_active})
    from economy.services import audit
    audit('panel.toggle_active', user=target, actor=request.user, ip=_client_ip(request),
          details={'is_active': locked.is_active, 'idem': idem})
    return JsonResponse({'ok': True, 'is_active': locked.is_active})
