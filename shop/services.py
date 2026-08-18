from __future__ import annotations

import random
import uuid

from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from economy.services import (spend, refund, grant_coins, grant_gems, grant_xp,
                              InsufficientFunds, audit, ActiveBoost, invalidate_boost_cache)
from .effects import (slot_of, is_equippable, SLOT_CAPACITY, EQUIP_SLOTS,
                      is_directly_consumable, bound_note)
from .models import Product, Purchase, InventoryItem, Wishlist, RecentlyViewed


class PurchaseError(Exception):
    def __init__(self, fa_message: str):
        super().__init__(fa_message)
        self.fa = fa_message


def _grant_item(user, product: Product, source: str) -> InventoryItem:
    item, created = InventoryItem.objects.get_or_create(
        user=user, product=product, defaults={'quantity': 1, 'source': source})
    if not created:
        if product.product_type in ('consumable', 'booster'):
            item.quantity = F('quantity') + 1
            item.save(update_fields=['quantity'])
            item.refresh_from_db(fields=['quantity'])
    _apply_immediate_effect(user, product)
    return item


def grant_product_item(user, slug: str, source: str) -> dict:
    product = Product.objects.filter(slug=slug, is_active=True).first()
    if not product:
        return {'ok': False, 'error': f'محصول {slug} یافت نشد'}
    _grant_item(user, product, source=source)
    return {'ok': True, 'product': product.name}


def _apply_immediate_effect(user, product: Product):
    et = product.effect_type
    if et == 'pet':
        from economy.models import PetSpecies, UserPet
        species = PetSpecies.objects.filter(product_slug=product.slug).first()
        if species:
            pet, created = UserPet.objects.get_or_create(
                user=user, species=species, defaults={'name': species.name})
            if created and not UserPet.objects.filter(user=user, is_active=True).exists():
                pet.is_active = True
                pet.save(update_fields=['is_active'])
    elif et == 'season_pass':
        from economy.services import get_active_season
        from economy.models import UserSeasonPass
        season = get_active_season()
        if season:
            usp, _ = UserSeasonPass.objects.get_or_create(user=user, season=season)
            if not usp.has_pass:
                usp.has_pass = True
                usp.save(update_fields=['has_pass'])


@transaction.atomic
def purchase_product(user, product_id: int, idempotency_key: str | None = None) -> dict:
    idem = (idempotency_key or uuid.uuid4().hex)[:100]
    idem = f'purchase:{user.pk}:{idem}'


    existing = Purchase.objects.filter(idempotency_key=idem).first()
    if existing:
        return {'ok': True, 'duplicate': True, 'purchase_id': existing.pk}

    product = Product.objects.select_for_update().filter(pk=product_id).first()
    if not product:
        raise PurchaseError('محصول پیدا نشد.')
    if not product.is_available():
        raise PurchaseError('این محصول در حال حاضر قابل خرید نیست (ناموجود/منقضی).')

    owned_qty = (InventoryItem.objects.filter(user=user, product=product)
                 .values_list('quantity', flat=True).first() or 0)
    bought = Purchase.objects.filter(user=user, product=product, status='completed').count()
    if product.per_user_limit and (owned_qty + bought) >= product.per_user_limit \
            and product.product_type not in ('consumable', 'booster'):
        raise PurchaseError('به حد مجاز خرید این محصول رسیدی.')


    price_coins = product.final_price_coins()
    price_gems = product.final_price_gems()

    coins_tx = gems_tx = None
    nonce = uuid.uuid4().hex[:16]


    if price_coins > 0:
        r = spend(user, 'coin', price_coins, source='shop_purchase', source_id=product.pk,
                  idempotency_key=f'{idem}:coin:{nonce}', metadata={'product': product.name})
        coins_tx = r.get('transaction_id')

    if price_gems > 0:
        r = spend(user, 'gem', price_gems, source='shop_purchase', source_id=product.pk,
                  idempotency_key=f'{idem}:gem:{nonce}', metadata={'product': product.name})
        gems_tx = r.get('transaction_id')


    if product.stock_limit is not None:
        updated = Product.objects.filter(
            pk=product.pk, sold_count__lt=product.stock_limit).update(sold_count=F('sold_count') + 1)
        if not updated:
            raise PurchaseError('موجودی این محصول به پایان رسید.')
    else:
        Product.objects.filter(pk=product.pk).update(sold_count=F('sold_count') + 1)

    purchase = Purchase.objects.create(
        user=user, product=product, coins_paid=price_coins, gems_paid=price_gems,
        idempotency_key=idem, transaction_id=coins_tx or gems_tx)


    items = [product]
    if product.product_type == 'bundle':
        items = list(product.bundle_items.filter(is_active=True))
        if not items:
            items = [product]
    for p in items:
        _grant_item(user, p, source='shop')

    audit('purchase', user=user, details={
        'purchase_id': purchase.pk, 'product': product.slug,
        'coins': price_coins, 'gems': price_gems, 'items': [p.slug for p in items],
    })
    invalidate_cosmetics_cache(user)
    from economy.context_processors import invalidate_wallet_cache
    invalidate_wallet_cache(user)

    return {'ok': True, 'purchase_id': purchase.pk, 'coins_paid': price_coins,
            'gems_paid': price_gems, 'items': [p.name for p in items]}


@transaction.atomic
def refund_purchase(admin_user, purchase_id: int, reason: str = '') -> dict:
    purchase = Purchase.objects.select_for_update().filter(pk=purchase_id).first()
    if not purchase or purchase.status != 'completed':
        return {'ok': False, 'error': 'این خرید قابل بازگشت نیست.'}
    purchase.status = 'refunded'
    purchase.refunded_at = timezone.now()
    purchase.save(update_fields=['status', 'refunded_at'])

    if purchase.coins_paid:
        refund(purchase.user, 'coin', purchase.coins_paid, source='refund',
               source_id=purchase.pk, idempotency_key=f'refund:{purchase.pk}:coin',
               actor=admin_user, metadata={'reason': reason})
    if purchase.gems_paid:
        refund(purchase.user, 'gem', purchase.gems_paid, source='refund',
               source_id=purchase.pk, idempotency_key=f'refund:{purchase.pk}:gem',
               actor=admin_user, metadata={'reason': reason})

    item = InventoryItem.objects.filter(user=purchase.user, product=purchase.product).first()
    if item:
        if item.quantity > 1 and purchase.product.product_type in ('consumable', 'booster'):
            item.quantity = F('quantity') - 1
            item.save(update_fields=['quantity'])
        else:
            item.delete()
    audit('refund', user=purchase.user, actor=admin_user,
          details={'purchase_id': purchase.pk, 'reason': reason})
    return {'ok': True}


@transaction.atomic
def equip_item(user, item_id: int) -> dict:
    item = InventoryItem.objects.select_for_update().select_related('product') \
        .filter(pk=item_id, user=user).first()
    if not item:
        return {'ok': False, 'error': 'آیتم در موجودی تو نیست.'}
    slot = slot_of(item.product.effect_type)
    if not slot:
        return {'ok': False, 'error': 'این آیتم قابلیت استفاده به‌صورت Equip ندارد.'}
    capacity = SLOT_CAPACITY.get(slot, 1)
    slot_types = _slot_effect_types(slot)
    equipped_count = InventoryItem.objects.filter(
        user=user, equipped=True, product__effect_type__in=slot_types).count()
    if equipped_count >= capacity:

        oldest = (InventoryItem.objects.filter(user=user, equipped=True,
                                               product__effect_type__in=_slot_effect_types(slot))
                  .order_by('acquired_at').first())
        if oldest:
            oldest.equipped = False
            oldest.save(update_fields=['equipped'])
    item.equipped = True
    item.save(update_fields=['equipped'])
    audit('equip', user=user, details={'item': item.product.slug, 'slot': slot})
    invalidate_cosmetics_cache(user)
    return {'ok': True, 'slot': slot}


def _slot_effect_types(slot: str) -> list[str]:
    from .effects import EFFECT_TO_SLOT
    return [et for et, s in EFFECT_TO_SLOT.items() if s == slot]


@transaction.atomic
def unequip_item(user, item_id: int) -> dict:
    item = InventoryItem.objects.select_for_update().filter(pk=item_id, user=user).first()
    if not item:
        return {'ok': False, 'error': 'آیتم موجود نیست.'}
    item.equipped = False
    item.save(update_fields=['equipped'])
    audit('unequip', user=user, details={'item': item.product.slug})
    invalidate_cosmetics_cache(user)
    return {'ok': True}


def get_equipped_cosmetics(user, cached: bool = True) -> dict:
    key = f'cosmetics:{user.pk}'
    if cached:
        hit = cache.get(key)
        if hit is not None:
            return hit
    equipped = (InventoryItem.objects.filter(user=user, equipped=True)
                .select_related('product'))
    out: dict = {}
    for it in equipped:
        slot = slot_of(it.product.effect_type)
        if not slot:
            continue
        payload = dict(it.product.effect_payload or {})
        payload.update({
            'name': it.product.name, 'slug': it.product.slug,
            'emoji': it.product.preview_emoji,
        })
        out.setdefault(slot, []).append(payload)
    if cached:
        cache.set(key, out, 120)
    return out


def invalidate_cosmetics_cache(user):
    cache.delete(f'cosmetics:{user.pk}')


@transaction.atomic
def consume_item(user, item_id: int) -> dict:
    item = InventoryItem.objects.select_for_update().select_related('product') \
        .filter(pk=item_id, user=user).first()
    if not item or item.quantity < 1:
        return {'ok': False, 'error': 'این آیتم را نداری.'}
    et = item.product.effect_type
    if bound_note(et):
        return {'ok': False, 'error': f'این آیتم فقط در محل خودش قابل استفاده است: {bound_note(et)}'}
    if not is_directly_consumable(et):
        return {'ok': False, 'error': 'این آیتم مصرفی نیست (با داشتنش فعال است).'}
    return _do_consume(user, item, source='inventory')


@transaction.atomic
def consume_item_by_effect(user, effect_type: str, source: dict | None = None) -> dict:
    item = (InventoryItem.objects.select_for_update().select_related('product')
            .filter(user=user, product__effect_type=effect_type, quantity__gt=0)
            .order_by('acquired_at').first())
    if not item:
        return {'ok': False, 'error': 'این آیتم را نداری.'}
    return _do_consume(user, item, source=str(source or effect_type))


def user_has_effect_item(user, effect_type: str) -> bool:
    return InventoryItem.objects.filter(user=user, product__effect_type=effect_type,
                                        quantity__gt=0).exists()


def _do_consume(user, item: InventoryItem, source: str) -> dict:
    product = item.product
    et = product.effect_type
    payload = dict(product.effect_payload or {})

    item.quantity = item.quantity - 1
    item.used_at = timezone.now()
    item.save(update_fields=['quantity', 'used_at'])

    from economy.models import Transaction
    Transaction(
        user=user, currency='coin', amount=0, balance_after=user.wallet.coins if hasattr(user, 'wallet') else 0,
        type='consume', source=source, source_id=product.slug,
        idempotency_key=f'consume:{user.pk}:{item.id}:{item.quantity}:{uuid.uuid4().hex[:8]}',
        metadata={'product': product.name, 'effect': et},
    ).save(force_insert=True)

    result = {'ok': True, 'product': product.name, 'remaining_quantity': item.quantity,
              'payload': payload}


    if et in ('xp_booster', 'coin_booster'):
        btype = 'xp' if et == 'xp_booster' else 'coin'
        mult = float(payload.get('multiplier', 1.5))
        hours = float(payload.get('hours', 24))
        ActiveBoost.objects.create(
            user=user, boost_type=btype, multiplier=mult,
            expires_at=timezone.now() + timezone.timedelta(hours=hours),
            inventory_item_id=item.pk)
        invalidate_boost_cache(user)
        result['message'] = f'⚡ بوستر {btype} فعال شد: ×{mult:g} به مدت {hours:g} ساعت!'

    elif et == 'extra_hearts':
        r = grant_xp(user, int(payload.get('xp', 20)), source='extra_hearts', source_id=product.slug,
                     idempotency_key=f'hearts:{user.pk}:{uuid.uuid4().hex[:8]}')
        result['message'] = f"💗 قلب‌ها تبدیل شد به {r.get('granted', 0)} XP!"

    elif et in ('mystery_box', 'lucky_spin'):
        loot_table = payload.get('loot', [])
        prize = _weighted_pick(loot_table)
        if prize is None:
            result['message'] = 'جعبه خالی بود! (جدول جایزه تنظیم نشده)'
        else:
            prize_desc = _grant_loot(user, prize, parent=f'{et}:{product.slug}')
            result['prize'] = prize
            result['message'] = f'🎁 جایزه‌ات: {prize_desc}'

    invalidate_cosmetics_cache(user)
    return result


def _weighted_pick(loot_table: list) -> dict | None:
    if not loot_table:
        return None
    weights = [max(0, float(x.get('weight', 1))) for x in loot_table]
    return random.choices(loot_table, weights=weights, k=1)[0]


def _grant_loot(user, prize: dict, parent: str) -> str:
    nonce = uuid.uuid4().hex[:8]
    if prize.get('coins'):
        r = grant_coins(user, int(prize['coins']), source=parent,
                        idempotency_key=f'loot:{user.pk}:{parent}:coin:{nonce}')
        return f"{r.get('granted', 0)} سکه 🪙"
    if prize.get('gems'):
        r = grant_gems(user, int(prize['gems']), source=parent,
                       idempotency_key=f'loot:{user.pk}:{parent}:gem:{nonce}')
        return f"{r.get('granted', 0)} الماس 💎"
    if prize.get('xp'):
        r = grant_xp(user, int(prize['xp']), source=parent,
                     idempotency_key=f'loot:{user.pk}:{parent}:xp:{nonce}')
        return f"{r.get('granted', 0)} XP ⭐"
    if prize.get('product_slug'):
        r = grant_product_item(user, prize['product_slug'], source=parent)
        return r.get('product', 'یک آیتم') if r.get('ok') else 'آیتم نامشخص'
    return '...!'


def has_unlock(user, effect_type: str, **payload_match) -> bool:
    items = (InventoryItem.objects.filter(user=user, product__effect_type=effect_type)
             .select_related('product'))
    for it in items:
        payload = it.product.effect_payload or {}
        if all(payload.get(k) == v for k, v in payload_match.items()):
            return True
    return False


def record_view(user, product: Product):
    RecentlyViewed.objects.update_or_create(user=user, product=product)
    stale_ids = list(RecentlyViewed.objects.filter(user=user).order_by('-viewed_at')
                     .values_list('pk', flat=True)[20:])
    if stale_ids:
        RecentlyViewed.objects.filter(pk__in=stale_ids).delete()
    Product.objects.filter(pk=product.pk).update(views_count=F('views_count') + 1)


def toggle_wishlist(user, product: Product) -> dict:
    obj, created = Wishlist.objects.get_or_create(user=user, product=product)
    if not created:
        obj.delete()
    return {'in_wishlist': created}
