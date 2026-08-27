from __future__ import annotations

import uuid
from datetime import date

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F, Max
from django.utils import timezone

from .models import (
    Wallet, Transaction, RewardRule, RewardGrant, ActiveBoost, AuditLog,
    DailyRewardDay, DailyRewardClaim, Season, SeasonLevel, UserSeasonPass, LeaderboardEntry,
)


class InsufficientFunds(Exception):
    def __init__(self, currency: str, have: int, need: int):
        self.currency, self.have, self.need = currency, have, need
        super().__init__(f'موجودی {currency} کافی نیست: {have} < {need}')


class RewardCapReached(Exception):
    pass


def get_or_create_safe(queryset, **kwargs):
    """get_or_create that is safe under concurrency.

    Two simultaneous requests can both see 'no row' and both INSERT;
    the second one then hits the UNIQUE constraint (IntegrityError).
    The losing request simply reads the row the winner just created.
    """
    try:
        return queryset.get_or_create(**kwargs)
    except IntegrityError:
        lookup = {k: v for k, v in kwargs.items() if k != 'defaults'}
        return queryset.get(**lookup), False


def _idem_key(*parts) -> str:
    return ':'.join(str(p) for p in parts if p is not None)[:100] or uuid.uuid4().hex[:32]


def get_wallet(user) -> Wallet:
    wallet, _ = get_or_create_safe(Wallet.objects, user=user)
    return wallet


def _active_multiplier(user, currency: str) -> float:
    if currency not in ('xp', 'coin'):
        return 1.0
    btype = 'xp' if currency == 'xp' else 'coin'
    cache_key = f'boost:{user.pk}:{btype}'
    mult = cache.get(cache_key)
    if mult is None:
        now = timezone.now()
        mult = 1.0
        for b in ActiveBoost.objects.filter(user=user, boost_type=btype, expires_at__gt=now):
            mult = max(mult, b.multiplier)
        cache.set(cache_key, mult, 60)
    return mult


def invalidate_boost_cache(user):
    cache.delete_many([f'boost:{user.pk}:xp', f'boost:{user.pk}:coin'])


def audit(action: str, user=None, actor=None, details: dict | None = None, ip: str | None = None):
    AuditLog.objects.create(action=action, user=user, actor=actor, details=details or {}, ip=ip)


def _sync_user_mirrors(user, wallet: Wallet | None = None):
    changed = []
    if wallet is not None and user.coins != wallet.coins:
        user.coins = wallet.coins
        changed.append('coins')
    if changed:
        user.save(update_fields=changed)


def grant(user, currency: str, amount: int, *, source: str, source_id=None,
          rule_code: str | None = None, tx_type: str = 'reward',
          idempotency_key: str | None = None, apply_boost: bool = True,
          period_key: str | None = None, metadata: dict | None = None,
          actor=None) -> dict:
    if amount <= 0:
        return {'ok': False, 'granted': 0, 'error': 'amount<=0'}

    idem = idempotency_key or _idem_key(user.pk, currency, source, source_id, rule_code, period_key, uuid.uuid4().hex)

    with transaction.atomic():

        if rule_code:
            rule = RewardRule.objects.filter(code=rule_code, is_active=True).first()
            if rule and rule.daily_limit:
                today = timezone.localdate().isoformat()
                counter, _ = get_or_create_safe(RewardGrant.objects,
                    user=user, rule_code=rule_code, period_key=today)
                bumped = (RewardGrant.objects
                          .filter(pk=counter.pk, times_used__lt=rule.daily_limit)
                          .update(times_used=F('times_used') + 1))
                if not bumped:
                    return {'ok': False, 'granted': 0, 'capped': True}

        if period_key and rule_code:
            try:
                RewardGrant.objects.create(user=user, rule_code=f'{rule_code}', period_key=period_key)
            except IntegrityError:
                return {'ok': False, 'granted': 0, 'already': True}

        wallet = Wallet.objects.select_for_update().get(pk=get_wallet(user).pk)

        boosted_by = 1.0
        final_amount = amount
        if apply_boost:
            boosted_by = _active_multiplier(user, currency)
            final_amount = int(round(amount * boosted_by))

        meta = {'base_amount': amount, 'boost_multiplier': boosted_by}
        if metadata:
            meta.update(metadata)


        if currency == 'gem':
            balance_after = wallet.gems + final_amount
            wallet.gems = F('gems') + final_amount
        elif currency == 'coin':
            balance_after = wallet.coins + final_amount
            wallet.coins = F('coins') + final_amount
        else:
            balance_after = user.xp + final_amount
        if currency != 'xp':
            wallet.save(update_fields=['gems' if currency == 'gem' else 'coins'])

        tx = Transaction(
            user=user, currency=currency, amount=final_amount, balance_after=balance_after,
            type=tx_type, source=source, source_id=str(source_id or ''),
            idempotency_key=idem, metadata=meta, actor=actor,
        )
        try:
            tx.save(force_insert=True)
        except IntegrityError:
            return {'ok': False, 'granted': 0, 'duplicate': True}

        if currency == 'xp':
            user.xp = F('xp') + final_amount
            user.save(update_fields=['xp'])
            user.refresh_from_db(fields=['xp'])
            user.update_level()
            user.save(update_fields=['level'])
            _add_season_xp(user, final_amount)

        wallet.refresh_from_db()
        _sync_user_mirrors(user, wallet)

    return {'ok': True, 'granted': final_amount, 'balance': balance_after,
            'boosted_by': boosted_by, 'transaction_id': tx.pk}


def grant_xp(user, amount: int, *, source: str, source_id=None, rule_code=None,
             period_key=None, idempotency_key=None, metadata=None) -> dict:
    return grant(user, 'xp', amount, source=source, source_id=source_id, rule_code=rule_code,
                 period_key=period_key, idempotency_key=idempotency_key, metadata=metadata)


def grant_coins(user, amount: int, *, source: str, source_id=None, rule_code=None,
                period_key=None, idempotency_key=None, metadata=None) -> dict:
    return grant(user, 'coin', amount, source=source, source_id=source_id, rule_code=rule_code,
                 period_key=period_key, idempotency_key=idempotency_key, metadata=metadata)


def grant_gems(user, amount: int, *, source: str, source_id=None, period_key=None,
               idempotency_key=None, metadata=None, actor=None) -> dict:
    return grant(user, 'gem', amount, source=source, source_id=source_id, period_key=period_key,
                 rule_code=None, idempotency_key=idempotency_key, metadata=metadata, actor=actor,
                 apply_boost=False)


def spend(user, currency: str, amount: int, *, source: str, source_id=None,
          idempotency_key: str, tx_type: str = 'spend', metadata=None, actor=None) -> dict:
    if currency not in ('coin', 'gem'):
        raise ValueError('فقط coin/gem قابل خرج است')
    if amount <= 0:
        amount = 0
    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(pk=get_wallet(user).pk)
        current = wallet.coins if currency == 'coin' else wallet.gems
        if current < amount:
            raise InsufficientFunds(currency, current, amount)
        if currency == 'coin':
            wallet.coins = F('coins') - amount
        else:
            wallet.gems = F('gems') - amount
        wallet.save(update_fields=['coins' if currency == 'coin' else 'gems'])
        wallet.refresh_from_db()
        balance_after = wallet.coins if currency == 'coin' else wallet.gems
        tx = Transaction(
            user=user, currency=currency, amount=-amount, balance_after=balance_after,
            type=tx_type, source=source, source_id=str(source_id or ''),
            idempotency_key=idempotency_key, metadata=metadata or {}, actor=actor,
        )
        try:
            tx.save(force_insert=True)
        except IntegrityError:
            return {'ok': False, 'paid': 0, 'duplicate': True, 'balance': balance_after}
        _sync_user_mirrors(user, wallet)
    return {'ok': True, 'paid': amount, 'balance': balance_after, 'transaction_id': tx.pk}


def refund(user, currency: str, amount: int, *, source: str, source_id=None, idempotency_key: str,
           actor=None, metadata=None) -> dict:
    return grant(user, currency, amount, source=source, source_id=source_id, tx_type='refund',
                 idempotency_key=idempotency_key, apply_boost=False, metadata=metadata, actor=actor)


def admin_adjust(user, currency: str, amount: int, *, actor, idempotency_key: str,
                 reason: str = '', metadata: dict | None = None) -> dict:
    if amount == 0:
        return {'ok': False, 'error': 'amount=0'}
    meta = {'reason': reason}
    if metadata:
        meta.update(metadata)
    if amount > 0:
        return grant(user, currency, amount, source='admin_panel', tx_type='admin_adjust',
                     idempotency_key=idempotency_key, apply_boost=False, metadata=meta, actor=actor)
    if currency in ('coin', 'gem'):
        try:
            return spend(user, currency, -amount, source='admin_panel', tx_type='admin_adjust',
                         idempotency_key=idempotency_key, metadata=meta, actor=actor)
        except InsufficientFunds as e:
            return {'ok': False, 'error': 'insufficient', 'have': e.have, 'need': e.need}
    if currency != 'xp':
        return {'ok': False, 'error': 'bad_currency'}
    with transaction.atomic():
        locked = type(user).objects.select_for_update().get(pk=user.pk)
        new_xp = max(0, locked.xp + amount)
        delta = new_xp - locked.xp
        if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
            return {'ok': False, 'duplicate': True, 'balance': locked.xp}
        locked.xp = new_xp
        locked.save(update_fields=['xp'])
        tx = Transaction(
            user=locked, currency='xp', amount=delta, balance_after=new_xp,
            type='admin_adjust', source='admin_panel', source_id='',
            idempotency_key=idempotency_key, metadata=meta, actor=actor,
        )
        try:
            with transaction.atomic():
                tx.save(force_insert=True)
        except IntegrityError:
            return {'ok': False, 'duplicate': True, 'balance': new_xp}
        if locked.update_level():
            locked.save(update_fields=['level'])
        user.xp = new_xp
        user.level = locked.level
    return {'ok': True, 'balance': new_xp, 'transaction_id': tx.pk}


def claim_daily_login(user) -> dict:
    today = timezone.localdate()
    yesterday = date.fromordinal(today.toordinal() - 1)

    with transaction.atomic():
        last_claim = (DailyRewardClaim.objects.select_for_update()
                      .filter(user=user).order_by('-claim_date').first())
        streak = 1
        if last_claim and last_claim.claim_date == yesterday:
            streak = last_claim.streak + 1

        cycle_len = DailyRewardDay.objects.aggregate(m=Max('day'))['m'] or 7
        cycle_len = max(cycle_len, 1)
        day_index = ((streak - 1) % cycle_len) + 1

        claim = DailyRewardClaim(user=user, claim_date=today, day_index=day_index, streak=streak)
        try:
            claim.save(force_insert=True)
        except IntegrityError:
            return {'ok': False, 'already': True}

        if (user.streak or 0) < streak:
            user.streak = streak
            user.save(update_fields=['streak'])

        reward = DailyRewardDay.objects.filter(day=day_index).first()
        coins = (reward.coins if reward else 10) + _pet_login_bonus(user)
        xp = reward.xp if reward else 5
        gems = reward.gems if reward else 0

        out = {'ok': True, 'already': False, 'streak': streak, 'day_index': day_index,
               'coins': coins, 'xp': xp, 'gems': gems}
        if coins:
            grant_coins(user, coins, source='daily_login', source_id=today.isoformat(),
                        idempotency_key=_idem_key(user.pk, 'daily', today, 'coin'))
        if xp:
            grant_xp(user, xp, source='daily_login', source_id=today.isoformat(),
                     idempotency_key=_idem_key(user.pk, 'daily', today, 'xp'))
        if gems:
            grant_gems(user, gems, source='daily_login', source_id=today.isoformat(),
                       idempotency_key=_idem_key(user.pk, 'daily', today, 'gem'))
        out['pet_bonus_coins'] = _pet_login_bonus(user)
        return out


def _pet_login_bonus(user) -> int:
    active = user.pets.filter(is_active=True).first()
    if active and active.hunger() >= 50:
        return 2
    return 0


def get_active_season() -> Season | None:
    s = cache.get('season:active')
    if s is None:
        s = Season.objects.filter(is_active=True, starts_at__lte=timezone.now(),
                                  ends_at__gte=timezone.now()).first()
        cache.set('season:active', s if s else False, 300)
        s = s if s else None
    return s


def _add_season_xp(user, xp_amount: int):
    season = get_active_season()
    if not season or xp_amount <= 0:
        return
    UserSeasonPass.objects.filter(user=user, season=season).update(season_xp=F('season_xp') + xp_amount)
    if not UserSeasonPass.objects.filter(user=user, season=season).exists():
        UserSeasonPass.objects.create(user=user, season=season, season_xp=xp_amount)


def claim_season_reward(user, level_number: int, track: str) -> dict:
    season = get_active_season()
    if not season:
        return {'ok': False, 'error': 'no_active_season'}
    sl = SeasonLevel.objects.filter(season=season, level_number=level_number).first()
    if not sl:
        return {'ok': False, 'error': 'no_such_level'}
    with transaction.atomic():
        usp = UserSeasonPass.objects.select_for_update().filter(user=user, season=season).first()
        if not usp:
            return {'ok': False, 'error': 'not_in_season'}
        if usp.current_level() < level_number:
            return {'ok': False, 'error': 'level_not_reached'}
        claimed = usp.claimed_premium if track == 'premium' else usp.claimed_free
        if level_number in claimed:
            return {'ok': False, 'error': 'already_claimed'}
        if track == 'premium' and not usp.has_pass:
            return {'ok': False, 'error': 'needs_pass'}
        reward = sl.premium_reward if track == 'premium' else sl.free_reward
        (usp.claimed_premium if track == 'premium' else usp.claimed_free).append(level_number)
        usp.save(update_fields=['claimed_premium' if track == 'premium' else 'claimed_free'])

    granted = _grant_reward_payload(user, reward, source=f'season:{season.id}:level:{level_number}:{track}')
    return {'ok': True, 'granted': granted, 'reward': reward}


def _grant_reward_payload(user, payload: dict, source: str) -> dict:
    out = {}
    if payload.get('coins'):
        out['coins'] = grant_coins(user, int(payload['coins']), source=source,
                                   idempotency_key=_idem_key(user.pk, source, 'coin')).get('granted')
    if payload.get('gems'):
        out['gems'] = grant_gems(user, int(payload['gems']), source=source,
                                 idempotency_key=_idem_key(user.pk, source, 'gem')).get('granted')
    if payload.get('xp'):
        out['xp'] = grant_xp(user, int(payload['xp']), source=source,
                             idempotency_key=_idem_key(user.pk, source, 'xp')).get('granted')
    if payload.get('product_slug'):
        from shop.services import grant_product_item
        out['item'] = grant_product_item(user, payload['product_slug'], source=source)
    return out


def get_leaderboard(period: str = 'global', limit: int = 50):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if period == 'global':
        return (User.objects.filter(is_active=True).order_by('-xp')
                .values('id', 'username', 'avatar', 'xp', 'level')[:limit])
    from django.db.models import Sum
    if period == 'weekly':
        start = timezone.now() - timezone.timedelta(days=7)
    else:
        season = get_active_season()
        start = season.starts_at if season else timezone.now() - timezone.timedelta(days=30)
    rows = (Transaction.objects.filter(currency='xp', amount__gt=0, created_at__gte=start)
            .values('user_id', 'user__username', 'user__avatar', 'user__level')
            .annotate(xp=Sum('amount')).order_by('-xp')[:limit])
    return rows
