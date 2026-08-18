from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
from .models import CustomUser , PasswordResetOTP
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    PasswordResetRequestForm,
    OTPVerificationForm,
    NewPasswordForm
)


def _safe_next(request):
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    nxt = nxt.strip()
    if nxt.startswith('/') and not nxt.startswith('//') and '\\' not in nxt and len(nxt) <= 500:
        return nxt
    return ''


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('index')
    from blog.models import Article
    from language_academy.models import World, Lesson, Vocabulary
    articles = list(Article.objects.filter(published_at__lte=timezone.now(), is_featured=True)
                    .select_related('category')[:3])
    if len(articles) < 3:
        ids = [a.id for a in articles]
        articles += list(Article.objects.filter(published_at__lte=timezone.now())
                         .exclude(id__in=ids).select_related('category')[:3 - len(articles)])
    from django.db.models import Count, Q
    worlds = list(World.objects.filter(is_published=True).order_by('order').annotate(
        chapters_cnt=Count('chapters', filter=Q(chapters__is_published=True), distinct=True),
        lessons_cnt=Count('chapters__lessons',
                          filter=Q(chapters__is_published=True, chapters__lessons__is_published=True),
                          distinct=True))[:3])
    return render(request, 'landing.html', {
        'articles': articles,
        'worlds': worlds,
        'stat_users': CustomUser.objects.filter(is_active=True).count(),
        'stat_articles': Article.objects.filter(published_at__lte=timezone.now()).count(),
        'stat_words': Vocabulary.objects.filter(is_active=True).count(),
        'stat_lessons': Lesson.objects.filter(is_published=True, chapter__is_published=True).count(),
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()


            verification_code = str(random.randint(100000, 999999))
            user.verification_code = verification_code
            user.code_expiration = timezone.now() + timedelta(hours=24)
            user.save()

            messages.success(request, 'ثبت‌نام با موفقیت انجام شد! حالا می‌توانید وارد شوید.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form, 'next': _safe_next(request)})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'خوش آمدید {user.username}!')
                return redirect(_safe_next(request) or 'index')
            else:
                messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
        else:
            messages.error(request, 'لطفاً اطلاعات را به درستی وارد کنید.')
    else:
        form = CustomAuthenticationForm()
    from user.models import UserActivity


    return render(request, 'login.html', {'form': form, 'next': _safe_next(request)})


def logout_view(request):
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('login')


def password_reset_request_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)


                otp_code = str(random.randint(100000, 999999))


                PasswordResetOTP.objects.filter(email=email).delete()


                otp = PasswordResetOTP.objects.create(
                    user=user,
                    email=email,
                    otp_code=otp_code
                )
                print("=" * 50)
                print(f"🎯 کد OTP برای تست:")
                print(f"📧 ایمیل: {email}")
                print(f"🔑 کد: {otp_code}")
                print(f"⏰ انقضا: {otp.expires_at}")
                print("=" * 50)


                try:
                    send_mail(
                        'کد بازیابی رمز عبور - لرن کویست',
                        f'''
                        کد بازیابی رمز عبور شما:

                        {otp_code}

                        این کد تا ۱۰ دقیقه اعتبار دارد.

                        لرن کویست
                        ''',
                        'elahehimo8990@gmail.com',
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, f'کد بازیابی به ایمیل {email} ارسال شد.')
                    request.session['reset_email'] = email
                    request.session['reset_user_id'] = user.id
                    return redirect('otp_verify')

                except Exception as e:
                    messages.error(request, 'خطا در ارسال ایمیل. لطفاً مجدداً تلاش کنید.')
                    print(f"خطای ارسال ایمیل: {e}")

            except CustomUser.DoesNotExist:
                messages.error(request, 'کاربری با این ایمیل یافت نشد.')

    else:
        form = PasswordResetRequestForm()

    return render(request, 'password_reset_request.html', {'form': form})


def otp_verify_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    email = request.session.get('reset_email')
    user_id = request.session.get('reset_user_id')

    if not email or not user_id:
        messages.error(request, 'لطفاً ابتدا درخواست بازیابی رمز دهید.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']

            try:
                otp = PasswordResetOTP.objects.get(
                    email=email,
                    otp_code=otp_code,
                    is_used=False
                )

                if otp.is_valid():

                    otp.is_used = True
                    otp.save()


                    user = CustomUser.objects.get(id=user_id)
                    user.set_password('')
                    user.save()

                    request.session['verified_otp'] = True
                    messages.success(request, 'کد با موفقیت تأیید شد. لطفاً رمز عبور جدید وارد کنید.')
                    return redirect('password_reset')
                else:
                    messages.error(request, 'کد منقضی شده است. لطفاً مجدداً درخواست کنید.')
                    return redirect('password_reset_request')

            except PasswordResetOTP.DoesNotExist:
                messages.error(request, 'کد وارد شده صحیح نیست.')

    else:
        form = OTPVerificationForm()

    return render(request, 'otp_verify.html', {
        'form': form,
        'email': email
    })


def new_password_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if not request.session.get('verified_otp'):
        messages.error(request, 'لطفاً ابتدا کد OTP را تأیید کنید.')
        return redirect('password_reset_request')

    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'خطا در شناسایی کاربر. لطفاً مجدداً تلاش کنید.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = NewPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = CustomUser.objects.get(id=user_id)
                new_password = form.cleaned_data['new_password1']


                user.set_password(new_password)
                user.save()


                request.session.pop('reset_email', None)
                request.session.pop('reset_user_id', None)
                request.session.pop('verified_otp', None)

                messages.success(request, 'رمز عبور شما با موفقیت تغییر کرد. حالا می‌توانید وارد شوید.')
                return redirect('login')

            except CustomUser.DoesNotExist:
                messages.error(request, 'خطا در تغییر رمز عبور. لطفاً مجدداً تلاش کنید.')

    else:
        form = NewPasswordForm()

    return render(request, 'new_password.html', {'form': form})


def _collect_profile_card(request, target):
    from django.core.cache import cache

    global_rank = None
    try:
        from economy.models import LeaderboardEntry
        row = LeaderboardEntry.objects.filter(user=target, period='global').first()
        if row and row.rank:
            global_rank = row.rank
    except Exception:
        pass
    if global_rank is None:
        global_rank = CustomUser.objects.filter(xp__gt=target.xp).count() + 1

    cosmetics = {}
    try:
        from shop.services import get_equipped_cosmetics
        cosmetics = get_equipped_cosmetics(target, cached=True)
    except Exception:
        pass

    active_pet = None
    try:
        active_pet = target.pets.select_related('species').filter(is_active=True).first()
    except Exception:
        pass

    blocked_by_me = blocked_between = False
    try:
        from Messenger.models import BlockedUser
        blocked_by_me = BlockedUser.objects.filter(
            blocker=request.user, blocked=target).exists()
        blocked_between = BlockedUser.is_blocked_between(request.user, target)
    except Exception:
        pass

    last_seen = cache.get(f'user_last_seen_{target.pk}')
    online = bool(last_seen and (timezone.now() - last_seen).total_seconds() < 5 * 60)

    try:
        level_progress = target.get_level_progress()
    except Exception:
        level_progress = 0

    return {
        'cosm': cosmetics,
        'global_rank': global_rank,
        'active_pet': active_pet,
        'online': online,
        'blocked_by_me': blocked_by_me,
        'blocked_between': blocked_between,
        'level_progress': level_progress,
    }


def _profile_card_json(request, target):
    from Home.jalali import jalali_date_long

    card = _collect_profile_card(request, target)
    cosm = card['cosm'] or {}

    def slot_css(slot):
        items = cosm.get(slot) or []
        return items[0].get('css_class') or '' if items else ''

    def slot_label(slot):
        items = cosm.get(slot) or []
        if not items:
            return ''
        return items[0].get('label') or items[0].get('name') or ''

    pet = card['active_pet']
    pet_json = None
    if pet is not None:
        pet_json = {
            'emoji': getattr(pet.species, 'emoji', '') or '🐾',
            'name': pet.name,
            'level': pet.level,
        }

    avatar_url = ''
    try:
        if target.avatar:
            avatar_url = target.avatar.url
    except Exception:
        avatar_url = ''

    is_self = request.user.is_authenticated and request.user.pk == target.pk
    blocked_between = card['blocked_between'] and not card['blocked_by_me']

    return {
        'id': target.pk,
        'username': target.username,
        'display_name': target.get_full_name() or target.username,
        'initial': (target.username or '👤')[:1],
        'avatar_url': avatar_url,
        'is_self': is_self,
        'is_staff': bool(target.is_staff),
        'level': target.level,
        'xp': target.xp,
        'points': target.points,
        'streak': target.streak,
        'global_rank': card['global_rank'],
        'level_progress': card['level_progress'],
        'joined_jalali': jalali_date_long(target.date_joined),
        'online': card['online'],
        'title_label': slot_label('title'),
        'username_color_css': slot_css('username_color'),
        'frame_css': slot_css('frame'),
        'profile_effect_css': slot_css('profile_effect'),
        'badges': [
            {'label': b.get('label') or b.get('name') or '', 'css_class': b.get('css_class') or ''}
            for b in (cosm.get('badge') or [])[:6]
        ],
        'pet': pet_json,
        'blocked_by_me': card['blocked_by_me'],
        'blocked_between': card['blocked_between'],
        'can_message': (not is_self) and (not blocked_between),
        'message_url': f'/messenger/?u={target.pk}',
    }


@login_required
def profile_card_api(request, username):
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404

    target = get_object_or_404(CustomUser, username=username)
    return JsonResponse({'success': True, 'profile': _profile_card_json(request, target)})


@login_required
def public_profile(request, username):
    from django.shortcuts import get_object_or_404

    if username == request.user.username:
        return redirect('profile')

    target = get_object_or_404(CustomUser, username=username)


    card = _collect_profile_card(request, target)

    context = {
        't': target,
        'cosm': card['cosm'],
        'global_rank': card['global_rank'],
        'active_pet': card['active_pet'],
        'online': card['online'],
        'blocked_by_me': card['blocked_by_me'],
        'blocked_between': card['blocked_between'],
        'level_progress': card['level_progress'],
        'title': f'پروفایل {target.username}',
    }
    return render(request, 'public_profile.html', context)
