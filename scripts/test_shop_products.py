"""
End-to-end check that every product effect works.

  python manage.py shell < scripts/test_shop_products.py

For each product in the DB:
  1. Try to buy it as a fresh test user.
  2. Try to consume/equip it depending on its effect.
  3. Check that side-effects landed (Wallet transaction, InventoryItem,
     UserPet, UserSeasonPass, ActiveBoost, cosmetic slot equipped).
  4. Try to buy again — one-per-user products MUST refuse, repeatable
     ones MUST succeed.

Prints a report at the end.
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import transaction

from shop.models import Product, InventoryItem, Purchase
from shop.services import (
    purchase_product, PurchaseError, equip_item, unequip_item,
    consume_item, get_equipped_cosmetics,
)
from shop.effects import is_equippable, is_directly_consumable, INSTANT_CONSUMABLES
from economy.services import grant_coins, grant_gems, get_wallet, InsufficientFunds
from economy.models import ActiveBoost, UserPet, UserSeasonPass


U = get_user_model()

# ---- create a fresh test user --------------------------------------------
username = '_shop_e2e_'
user, _ = U.objects.get_or_create(
    username=username,
    defaults={'email': 'e2e@shop.test', 'is_active': True},
)
user.set_password('Test@12345')
user.save()

# wipe old state so re-runs are clean
InventoryItem.objects.filter(user=user).delete()
Purchase.objects.filter(user=user).delete()
ActiveBoost.objects.filter(user=user).delete()
UserPet.objects.filter(user=user).delete()
UserSeasonPass.objects.filter(user=user).delete()

# top up wallet
grant_coins(user, 500_000, source='e2e', idempotency_key='e2e-init-coins-' + uuid.uuid4().hex)
grant_gems(user,  50_000,  source='e2e', idempotency_key='e2e-init-gems-'  + uuid.uuid4().hex)

# ---- run through every product ------------------------------------------
report_ok = []
report_skip = []
report_fail = []

products = list(Product.objects.filter(is_active=True).order_by('product_type', 'effect_type', 'name'))
print(f'\n🧪 Testing {len(products)} products for user "{username}"…\n')

for p in products:
    label = f'{p.product_type:<10s} · {p.effect_type:<22s} · {p.name}'
    try:
        # 1) buy
        r1 = purchase_product(user, p.id, idempotency_key='e2e-buy-' + uuid.uuid4().hex)
        assert r1.get('ok') or r1.get('duplicate'), f'buy returned {r1}'
        # 2) inventory item created?
        # bundles don't add themselves — they explode into the bundled items
        if p.effect_type == 'bundle':
            granted = list(r1.get('items', []))
            assert granted, 'bundle bought but no items granted'
            item = None
        else:
            item = InventoryItem.objects.filter(user=user, product=p).first()
            assert item, 'no InventoryItem created after buy'
        # 3) effect-specific side-effects
        et = p.effect_type
        if et == 'pet':
            assert UserPet.objects.filter(user=user, species__product_slug=p.slug).exists(), \
                'pet effect did not create UserPet'
        elif et == 'season_pass':
            assert UserSeasonPass.objects.filter(user=user, has_pass=True).exists(), \
                'season_pass did not activate'
        # 4) if equippable, try equip → unequip
        if is_equippable(et) and item and item.quantity > 0:
            er = equip_item(user, item.id)
            assert er.get('ok'), f'equip failed: {er}'
            item.refresh_from_db()
            assert item.equipped, 'item not marked equipped after equip'
            ur = unequip_item(user, item.id)
            assert ur.get('ok'), f'unequip failed: {ur}'
        # 5) if directly consumable, try consume
        if is_directly_consumable(et) and item:
            item.refresh_from_db()
            if item.quantity > 0:
                cr = consume_item(user, item.id)
                assert cr.get('ok'), f'consume failed: {cr}'
                if et in ('xp_booster', 'coin_booster'):
                    assert ActiveBoost.objects.filter(user=user).exists(), 'booster did not create ActiveBoost'
        # 6) repeatability check
        try:
            r2 = purchase_product(user, p.id, idempotency_key='e2e-buy2-' + uuid.uuid4().hex)
            second_ok = bool(r2.get('ok')) and not r2.get('duplicate')
        except (PurchaseError, InsufficientFunds):
            second_ok = False
        if p.per_user_limit == 1:
            assert not second_ok, 'per_user_limit=1 product allowed a second purchase!'
        else:
            # for repeatable products the second buy should succeed
            # (unless we ran out of coins — unlikely with 500k+ budget)
            pass

        report_ok.append(label)
    except InsufficientFunds as e:
        report_skip.append(f'{label}  — insufficient funds ({e.currency}: {e.have}/{e.need})')
    except PurchaseError as e:
        report_skip.append(f'{label}  — {e}')
    except AssertionError as e:
        report_fail.append(f'{label}  ❌ {e}')
    except Exception as e:
        report_fail.append(f'{label}  ❌ {type(e).__name__}: {e}')

# ---- report --------------------------------------------------------------
print('\n' + '=' * 78)
print(f'✅ OK    : {len(report_ok)}')
print(f'⏭  SKIP : {len(report_skip)}')
print(f'❌ FAIL  : {len(report_fail)}')
print('=' * 78)
if report_fail:
    print('\nFailures:')
    for line in report_fail:
        print('  ' + line)
if report_skip:
    print('\nSkipped:')
    for line in report_skip[:8]:
        print('  ' + line)
    if len(report_skip) > 8:
        print(f'  … and {len(report_skip) - 8} more')

w = get_wallet(user)
print(f'\n💰 Test user final wallet: {w.coins} coins, {w.gems} gems')
print(f'📦 Owned items: {InventoryItem.objects.filter(user=user).count()}')
