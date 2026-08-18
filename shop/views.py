from __future__ import annotations

import json
import time
import uuid

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from economy.services import InsufficientFunds, audit
from .models import Product, Category, Purchase, InventoryItem, Wishlist, RecentlyViewed
from .services import (purchase_product, PurchaseError, equip_item, unequip_item,
                       consume_item, record_view, toggle_wishlist, get_equipped_cosmetics,
                       bound_note)
from .effects import EQUIP_SLOTS, is_equippable, is_directly_consumable, slot_of
from .tiles import annotate_tiles

# حداکثر خرید مجاز در هر دقیقه (ضد اسپم/اتومات)
BUY_RATE_LIMIT = 12
BUY_RATE_WINDOW = 60


def _buy_rate_limited(user) -> bool:
    """بیش از BUY_RATE_LIMIT خرید در یک دقیقه → رد می‌شود."""
    minute = int(time.time() // BUY_RATE_WINDOW)
    key = f'buy_rate:{user.pk}:{minute}'
    n = cache.get(key, 0)
    if n >= BUY_RATE_LIMIT:
        return True
    cache.set(key, n + 1, BUY_RATE_WINDOW + 5)
    return False


@login_required
def shop_home(request):
    qs = Product.objects.select_related('category').filter(is_active=True)

    cat_slug = request.GET.get('cat', '')
    if cat_slug:
        qs = qs.filter(Q(category__slug=cat_slug) | Q(category__parent__slug=cat_slug))
    ptype = request.GET.get('type', '')
    if ptype:
        qs = qs.filter(product_type=ptype)
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

    sort = request.GET.get('sort', 'featured')
    sort_map = {
        'featured': ('-is_featured', '-created_at'),
        'new': ('-created_at',),
        'cheap': ('price_coins',),
        'expensive': ('-price_coins',),
        'popular': ('-sold_count',),
        'discount': ('-discount_percent',),
    }
    qs = qs.order_by(*sort_map.get(sort, sort_map['featured']))

    page = Paginator(qs, 12).get_page(request.GET.get('page', 1))
    annotate_tiles(page.object_list)
    for p in page.object_list:
        p.price_c = p.final_price_coins()
        p.price_g = p.final_price_gems()
        p.disc = p.active_discount()
        p.remaining = p.remaining_stock()

    owned_ids = set(InventoryItem.objects.filter(user=request.user)
                    .values_list('product_id', flat=True))
    wish_ids = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    recent = (RecentlyViewed.objects.filter(user=request.user).select_related('product'))[:6]
    annotate_tiles([rv.product for rv in recent])
    featured = Product.objects.select_related('category').filter(is_active=True, is_featured=True)[:8]
    featured = annotate_tiles(featured)
    for p in featured:
        p.price_c = p.final_price_coins()
        p.price_g = p.final_price_gems()
        p.disc = p.active_discount()

    return render(request, 'shop/shop.html', {
        'title': 'فروشگاه 🛒', 'page': page,
        'categories': Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children'),
        'product_types': Product.PRODUCT_TYPES,
        'cat': cat_slug, 'ptype': ptype, 'search': search, 'sort': sort,
        'owned_ids': owned_ids, 'wish_ids': wish_ids, 'recent_viewed': recent,
        'featured_products': featured,
    })


@login_required
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    record_view(request.user, product)
    owned_item = InventoryItem.objects.filter(user=request.user, product=product).first()
    in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    bundle_items = product.bundle_items.filter(is_active=True) if product.product_type == 'bundle' else []
    similar = (Product.objects.filter(is_active=True, category=product.category)
               .exclude(pk=product.pk).order_by('-is_featured', '-sold_count')[:4])
    annotate_tiles([product, *similar])
    for p in similar:
        p.price_c = p.final_price_coins()
        p.price_g = p.final_price_gems()
        p.disc = p.active_discount()

    return render(request, 'shop/product_detail.html', {
        'title': product.name, 'product': product,
        'price_c': product.final_price_coins(), 'price_g': product.final_price_gems(),
        'disc': product.active_discount(), 'remaining': product.remaining_stock(),
        'owned_item': owned_item, 'in_wishlist': in_wishlist,
        'bundle_items': bundle_items, 'similar_products': similar,
        'equippable': is_equippable(product.effect_type),
        'consumable_direct': is_directly_consumable(product.effect_type),
        'bound_note': bound_note(product.effect_type),
        'slot_name': EQUIP_SLOTS.get(slot_of(product.effect_type) or '', ''),
    })


@login_required
@require_http_methods(['POST'])
def buy_product(request, product_id):

    if _buy_rate_limited(request.user):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False,
                                 'error': 'زیادی سریع خریدی! یک دقیقه صبر کن و دوباره تلاش کن.'},
                                status=429)
        messages.error(request, 'زیادی سریع خریدی! یک دقیقه صبر کن و دوباره تلاش کن.')
        return redirect('shop:home')

    idem = request.POST.get('idem') or (json.loads(request.body or '{}').get('idem') if request.content_type == 'application/json' else None)
    if isinstance(idem, str):
        idem = idem.strip()[:80] or None
    try:
        result = purchase_product(request.user, product_id, idempotency_key=idem)
    except InsufficientFunds as e:
        cur_fa = {'coin': 'سکه', 'gem': 'الماس'}[e.currency]
        msg = f'{cur_fa} کافی نداری! ({e.have} از {e.need})'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': msg, 'code': 'insufficient'}, status=402)
        messages.error(request, msg)
        return redirect('shop:product', slug=Product.objects.get(pk=product_id).slug)
    except PurchaseError as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': e.fa, 'code': 'purchase'}, status=400)
        messages.error(request, e.fa)
        return redirect('shop:home')


    safe_next = request.POST.get('next', '')
    if not (safe_next.startswith('/') and not safe_next.startswith('//')):
        safe_next = ''

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(result | {'duplicate': result.get('duplicate', False)})
    if result.get('duplicate'):
        messages.info(request, 'این خرید قبلاً ثبت شده بود — همین الان هم فعال است ✅')
    else:
        messages.success(request, f'🎉 خرید انجام شد! «{", ".join(result["items"])}» به حسابت اضافه شد.')
    if safe_next:
        return redirect(safe_next)
    return redirect('shop:inventory')


@login_required
def inventory_view(request):
    items = (InventoryItem.objects.filter(user=request.user, quantity__gt=0)
             .select_related('product', 'product__category').order_by('-equipped', '-acquired_at'))
    rows = []
    annotate_tiles([it.product for it in items])
    for it in items:
        et = it.product.effect_type
        rows.append({
            'item': it, 'equippable': is_equippable(et) and it.quantity > 0,
            'consumable': is_directly_consumable(et), 'bound': bound_note(et),
            'slot': EQUIP_SLOTS.get(slot_of(et) or '', ''),
        })
    cosmetics = get_equipped_cosmetics(request.user, cached=False)
    return render(request, 'shop/inventory.html', {
        'title': 'موجودی من 🎒', 'rows': rows, 'cosmetics': cosmetics,
    })


@login_required
@require_http_methods(['POST'])
def equip_view(request, item_id):
    r = equip_item(request.user, item_id)
    return JsonResponse(r)


@login_required
@require_http_methods(['POST'])
def unequip_view(request, item_id):
    r = unequip_item(request.user, item_id)
    return JsonResponse(r)


@login_required
@require_http_methods(['POST'])
def consume_view(request, item_id):
    r = consume_item(request.user, item_id)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(r)
    if r.get('ok'):
        messages.success(request, r.get('message', 'استفاده شد!'))
    else:
        messages.error(request, r.get('error', 'خطا'))
    return redirect('shop:inventory')


@login_required
def purchase_history_view(request):
    page = Paginator(
        Purchase.objects.filter(user=request.user).select_related('product').order_by('-created_at'), 15
    ).get_page(request.GET.get('page', 1))
    return render(request, 'shop/history.html', {'title': 'تاریخچه خریدها 🧾', 'page': page})


@login_required
def wishlist_view(request):
    rows = list(Wishlist.objects.filter(user=request.user).select_related('product', 'product__category')
                .order_by('-added_at'))
    annotate_tiles([w.product for w in rows])
    return render(request, 'shop/wishlist.html', {'title': 'علاقه‌مندی‌ها ❤️', 'rows': rows})


@login_required
@require_http_methods(['POST'])
def wishlist_toggle_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return JsonResponse(toggle_wishlist(request.user, product))
