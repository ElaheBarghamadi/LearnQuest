from django.core.cache import cache

from .services import get_wallet


def economy_context(request):
    ctx = {'lq_wallet': None, 'lq_cosmetics': {}, 'lq_daily_reward_toast': None, 'lq_pet': None}
    user = getattr(request, 'user', None)
    if not (user and user.is_authenticated):
        return ctx

    wallet = cache.get(f'wallet:{user.pk}')
    if wallet is None:
        wallet = get_wallet(user)
        cache.set(f'wallet:{user.pk}', wallet, 60)
    ctx['lq_wallet'] = wallet
    ctx['lq_gems'] = wallet.gems

    try:
        from shop.services import get_equipped_cosmetics
        ctx['lq_cosmetics'] = get_equipped_cosmetics(user, cached=True)
    except Exception:
        pass

    # پت فعال کاربر — برای ویجت شناور در همهٔ صفحات
    try:
        from economy.models import UserPet
        pet = UserPet.objects.filter(user=user, is_active=True).select_related('species').first()
        if pet:
            ctx['lq_pet'] = {
                'id': pet.pk,
                'emoji': pet.species.emoji,
                'name': pet.name,
                'level': pet.level,
                'hunger': pet.hunger(),
                'can_free_feed': pet.can_free_feed(),
            }
    except Exception:
        pass

    toast = request.session.pop('lq_daily_reward_toast', None)
    if toast:
        ctx['lq_daily_reward_toast'] = toast
    return ctx


def invalidate_wallet_cache(user):
    cache.delete(f'wallet:{user.pk}')
    try:
        from shop.services import invalidate_cosmetics_cache
        invalidate_cosmetics_cache(user)
    except Exception:
        pass
