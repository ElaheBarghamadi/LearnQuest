from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (ActiveBoost, Transaction, Season, SeasonLevel,
                     UserSeasonPass, UserPet, PetSpecies)
from .services import (get_wallet, claim_daily_login, get_active_season,
                       claim_season_reward, grant_xp, audit, spend, InsufficientFunds)


@login_required
def wallet_view(request):
    wallet = get_wallet(request.user)
    txs = (Transaction.objects.filter(user=request.user)
           .values('currency', 'amount', 'balance_after', 'type', 'source', 'created_at')
           .order_by('-created_at'))
    page = Paginator(txs, 20).get_page(request.GET.get('page', 1))
    boosts = ActiveBoost.objects.filter(user=request.user, expires_at__gt=timezone.now())
    return render(request, 'economy/wallet.html', {
        'title': 'کیف پول من', 'wallet': wallet, 'page': page, 'boosts': boosts,
    })


@login_required
def leaderboard_view(request):
    from .services import get_leaderboard
    period = request.GET.get('type', 'global')
    if period not in ('global', 'weekly', 'season'):
        period = 'global'
    rows = list(get_leaderboard(period, 50))
    my_xp = request.user.xp
    # رتبهٔ کاربر در همین بازه
    my_rank = None
    for i, r in enumerate(rows, start=1):
        if r.get('username') == request.user.username:
            my_rank = i
            break
    return render(request, 'economy/leaderboard.html', {
        'title': 'جدول امتیازات 🏆', 'rows': rows, 'period': period,
        'my_xp': my_xp, 'my_rank': my_rank,
    })


@login_required
def season_view(request):
    season = get_active_season()
    usp = None
    claimed_free, claimed_prem = [], []
    pass_product = None
    if season:
        usp, _ = UserSeasonPass.objects.get_or_create(user=request.user, season=season)
        claimed_free, claimed_prem = usp.claimed_free, usp.claimed_premium
        from shop.models import Product
        pass_product = Product.objects.filter(effect_type='season_pass', is_active=True).first()
    return render(request, 'economy/season.html', {
        'title': 'فصل و سیزن‌پس', 'season': season, 'usp': usp,
        'claimed_free': claimed_free, 'claimed_premium': claimed_prem,
        'pass_product': pass_product,
    })


@login_required
@require_http_methods(['POST'])
def season_pass_buy(request):
    season = get_active_season()
    UserSeasonPass.objects.get_or_create(user=request.user, season=season) if season else None
    if not season:
        messages.error(request, 'فصل فعالی وجود ندارد.')
        return redirect('economy:season')
    if UserSeasonPass.objects.filter(user=request.user, season=season, has_pass=True).exists():
        messages.info(request, 'سیزن‌پس را از قبل داری! 👑')
        return redirect('economy:season')

    from shop.models import Product
    from shop.services import purchase_product, PurchaseError
    product = Product.objects.filter(effect_type='season_pass', is_active=True).first()
    if not product:
        messages.error(request, 'محصول سیزن‌پس در فروشگاه تعریف نشده است.')
        return redirect('economy:season')
    try:
        purchase_product(request.user, product.id)
        messages.success(request, '👑 سیزن‌پس فعال شد! حالا جوایز ویژهٔ هر پله را هم می‌گیری.')
    except InsufficientFunds as e:
        messages.error(request, f'💎 الماس کافی نداری! ({e.have} از {e.need}) — از جایزه‌های روزانه جمع کن.')
    except PurchaseError as e:
        messages.error(request, e.fa)
    return redirect('economy:season')


@login_required
@require_http_methods(['POST'])
def season_claim_view(request, level_number: int, track: str):
    if track not in ('free', 'premium'):
        return JsonResponse({'ok': False, 'error': 'invalid_track'}, status=400)
    result = claim_season_reward(request.user, level_number, track)
    audit('season_claim', user=request.user, actor=None,
          details={'level': level_number, 'track': track, 'result': result.get('ok')})
    return JsonResponse(result)


@login_required
def pet_view(request):
    pets = request.user.pets.select_related('species').order_by('-is_active', '-level')
    active = next((p for p in pets if p.is_active), None)
    return render(request, 'economy/pet.html', {
        'title': 'پت‌های من 🐾', 'pets': pets, 'active_pet': active,
        'free_feed_hours': UserPet.FREE_FEED_HOURS, 'feed_cost': UserPet.FEED_COST,
    })


@login_required
@require_http_methods(['POST'])
def pet_feed_view(request, pet_id: int):
    pet = get_object_or_404(UserPet, pk=pet_id, user=request.user)
    if pet.can_free_feed():
        used_coins = False
    else:
        try:
            spend(request.user, 'coin', UserPet.FEED_COST, source='pet_feed', source_id=pet.id,
                  idempotency_key=f'feed:{request.user.pk}:{pet.id}:{timezone.now().timestamp()}')
            used_coins = True
        except InsufficientFunds as e:
            return JsonResponse({'ok': False, 'error': f'سکه کافی نداری! ({e.have}/{e.need})'}, status=402)
    result = pet.feed()
    audit('pet_feed', user=request.user, details={'pet': pet.name, 'paid': used_coins})
    from django.contrib import messages as dj_messages
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'paid_coins': used_coins, 'hunger': pet.hunger(), **result})
    dj_messages.success(request, f'🍖 {pet.name} رو غذا دادی! سطح {pet.level}')
    return redirect('economy:pet')


@login_required
@require_http_methods(['POST'])
def pet_activate_view(request, pet_id: int):
    pet = get_object_or_404(UserPet, pk=pet_id, user=request.user)
    UserPet.objects.filter(user=request.user).update(is_active=False)
    pet.is_active = True
    pet.save(update_fields=['is_active'])
    return redirect('economy:pet')


@login_required
@require_http_methods(['POST'])
def pet_rename_view(request, pet_id: int):
    pet = get_object_or_404(UserPet, pk=pet_id, user=request.user)
    name = (request.POST.get('name') or '').strip()[:40]
    if name:
        pet.name = name
        pet.save(update_fields=['name'])
    return redirect('economy:pet')


@login_required
@require_http_methods(['POST'])
def use_hint_ticket(request):
    from shop.services import consume_item_by_effect
    from language_academy.models import QuizSession, QuestionChoice
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = request.POST
    session_key = data.get('session_key')
    question_id = data.get('question_id')
    session = get_object_or_404(QuizSession, session_key=session_key, user=request.user, is_completed=False)

    r = consume_item_by_effect(request.user, 'hint_ticket', source={'quiz_session': session_key})
    if not r.get('ok'):
        return JsonResponse({'ok': False, 'error': r.get('error', 'بلیط راهنما نداری!')}, status=402)

    wrongs = list(QuestionChoice.objects
                  .filter(question_id=question_id, is_correct=False)
                  .values_list('id', flat=True)[:2])
    return JsonResponse({'ok': True, 'hide_choices': wrongs, 'remaining': r.get('remaining_quantity')})


@login_required
@require_http_methods(['POST'])
def use_time_card(request):
    from shop.services import consume_item_by_effect
    from language_academy.models import QuizSession
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = request.POST
    session_key = data.get('session_key')
    session = get_object_or_404(QuizSession, session_key=session_key, user=request.user, is_completed=False)

    r = consume_item_by_effect(request.user, 'time_extension', source={'quiz_session': session_key})
    if not r.get('ok'):
        return JsonResponse({'ok': False, 'error': r.get('error', 'کارت زمان نداری!')}, status=402)

    bonus_sec = int((r.get('payload') or {}).get('minutes', 5) or 5) * 60
    session.time_spent = max(0, session.time_spent - bonus_sec)
    session.save(update_fields=['time_spent'])
    extended = session.quiz.time_limit_minutes * 60 - session.time_spent
    return JsonResponse({'ok': True, 'remaining_seconds': extended,
                         'remaining': r.get('remaining_quantity')})


@login_required
def retry_ticket_status(request, quiz_id: int):
    from shop.services import user_has_effect_item
    return JsonResponse({'has_retry': user_has_effect_item(request.user, 'retry_ticket')})
