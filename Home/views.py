from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone as _tz

from blog.models import Article
from user.models import UserActivity

from .jalali import jalali_date, jalali_date_long, jalali_human


@login_required
def index(request):
    from economy.services import get_active_season
    from economy.models import UserSeasonPass, UserPet, LeaderboardEntry, DailyRewardClaim

    recent_articles = Article.objects.filter(is_featured=True)[:3]
    if recent_articles.count() < 3:
        recent_articles = Article.objects.all()[:3]

    user = request.user
    user.update_level()

    current_level = user.level or 1
    current_xp = user.xp or 0
    xp_per_level = 200
    max_level = 20

    current_level_start_xp = (current_level - 1) * xp_per_level
    xp_earned_in_level = current_xp - current_level_start_xp
    if xp_earned_in_level < 0:
        xp_earned_in_level = 0

    if current_level >= max_level:
        xp_needed = 0
        progress_percentage = 100
    else:
        xp_needed = xp_per_level - xp_earned_in_level
        if xp_needed <= 0:
            xp_needed = 0
            progress_percentage = 100
        else:
            progress_percentage = int((xp_earned_in_level / xp_per_level) * 100)
            progress_percentage = max(0, min(100, progress_percentage))

    ring_pct = progress_percentage / 100 * 314.16

    season = get_active_season()
    season_info = None
    if season:
        usp, _ = UserSeasonPass.objects.get_or_create(user=user, season=season)
        levels = list(season.levels.order_by('level_number'))
        cur = usp.current_level()
        nxt = next((l for l in levels if usp.season_xp < l.xp_required), None)
        prev_req = 0
        for l in levels:
            if l.level_number <= cur:
                prev_req = l.xp_required
            else:
                break
        if nxt and nxt.xp_required > prev_req:
            spct = int((usp.season_xp - prev_req) / (nxt.xp_required - prev_req) * 100)
            spct = max(0, min(100, spct))
            snext = nxt.xp_required - usp.season_xp
        else:
            spct = 100 if cur and not nxt else 0
            snext = 0
        season_info = {
            'season': season, 'level': cur, 'xp': usp.season_xp, 'has_pass': usp.has_pass,
            'pct': spct, 'next_xp': snext, 'max_level': levels[-1].level_number if levels else 0,
        }

    pet = UserPet.objects.filter(user=user, is_active=True).select_related('species').first()
    if pet:
        pet.hunger_val = pet.hunger()
        pet.can_feed = pet.can_free_feed()

    lb = LeaderboardEntry.objects.filter(user=user, period='global').first()
    claimed_today = DailyRewardClaim.objects.filter(user=user, claim_date=_tz.localdate()).exists()
    hour = _tz.localtime().hour
    if hour < 6:
        daypart = ('🌙', 'شب بخیر')
    elif hour < 12:
        daypart = ('🌤️', 'صبح بخیر')
    elif hour < 17:
        daypart = ('☀️', 'ظهر بخیر')
    else:
        daypart = ('🌆', 'عصر بخیر')

    activities = user.activities.all()[:6]

    return render(request, 'index.html', {
        'recent_articles': recent_articles,
        'xp_needed': xp_needed,
        'progress_percentage': progress_percentage,
        'ring_pct': ring_pct,
        'season_info': season_info,
        'pet': pet,
        'lb_rank': lb.rank if lb and lb.rank else None,
        'claimed_today': claimed_today,
        'daypart': daypart,
        'now': _tz.now(),
        'activities': activities,
    })


def games(request):
    return render(request, 'games.html')


@login_required
def add_test_activity(request):
    UserActivity.objects.create(
        user=request.user,
        title='فعالیت تستی',
        description='این یک فعالیت آزمایشی است که به صورت دستی اضافه شد',
        icon='flask'
    )
    return JsonResponse({'success': True, 'message': 'فعالیت تستی اضافه شد'})


@login_required
def profile_view(request):
    user = request.user


    try:
        progress_percentage = user.get_level_progress()
    except Exception:
        progress_percentage = 0


    user.jalali_joined = jalali_date_long(user.date_joined) or 'نامشخص'
    user.jalali_last_login = jalali_human(user.last_login) or 'امروز'


    try:
        from Game.models import UserAchievement
        achievements = UserAchievement.objects.filter(user=user)[:6]
        for ach in achievements:
            ach.jalali_date = jalali_date(ach.earned_at)
    except Exception:
        achievements = []


    try:
        from user.models import UserActivity
        activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:10]
        for act in activities:
            act.jalali_created = jalali_human(act.created_at)
    except Exception:
        activities = []


    try:
        active_pet = user.pets.select_related('species').filter(is_active=True).first()
    except Exception:
        active_pet = None

    context = {
        'user': user,
        'progress_percentage': progress_percentage,
        'achievements': achievements,
        'activities': activities,
        'active_pet': active_pet,
    }
    return render(request, 'profile.html', context)


@login_required
def edit_profile_view(request):
    user = request.user

    if request.method == 'POST':

        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        avatar = request.FILES.get('avatar')


        if not username or not email:
            messages.error(request, 'نام کاربری و ایمیل الزامی هستند')
            return redirect('edit_profile')


        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email
        user.phone = phone

        if avatar:
            user.avatar = avatar


        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password:
            if not user.check_password(current_password):
                messages.error(request, 'رمز عبور فعلی اشتباه است')
                return redirect('edit_profile')

            if new_password != confirm_password:
                messages.error(request, 'رمز عبور جدید و تکرار آن مطابقت ندارند')
                return redirect('edit_profile')

            if len(new_password) < 6:
                messages.error(request, 'رمز عبور جدید باید حداقل ۶ کاراکتر باشد')
                return redirect('edit_profile')

            user.set_password(new_password)
            user.save()


            from django.contrib.auth import login
            login(request, user)
            messages.success(request, 'رمز عبور با موفقیت تغییر کرد')
            return redirect('edit_profile')

        user.save()
        messages.success(request, 'اطلاعات شما با موفقیت به‌روزرسانی شد')
        return redirect('edit_profile')

    return render(request, 'profile-edit.html', {'user': user})


@login_required
def remove_avatar(request):
    if request.method == 'POST':
        try:
            user = request.user
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'هیچ عکسی وجود ندارد'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'متد مجاز نیست'}, status=405)

def guide(request):
    if request.GET.get('partial'):
        return render(request, 'guide_body.html')
    return render(request, 'guide.html')
