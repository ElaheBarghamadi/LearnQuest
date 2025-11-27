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
    CustomAuthenticationForm,  # این خط اضافه شده
    PasswordResetRequestForm,  # تغییر این خط
    OTPVerificationForm,       # تغییر این خط
    NewPasswordForm
)


def home_redirect(request):
    """هدایت به صفحه اصلی یا لاگین"""
    if request.user.is_authenticated:
        return redirect('index')
    else:
        return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # تولید کد تأیید
            verification_code = str(random.randint(100000, 999999))
            user.verification_code = verification_code
            user.code_expiration = timezone.now() + timedelta(hours=24)
            user.save()

            messages.success(request, 'ثبت‌نام با موفقیت انجام شد! حالا می‌توانید وارد شوید.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)  # حالا این کار می‌کند
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'خوش آمدید {user.username}!')
                return redirect('index')
            else:
                messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
        else:
            messages.error(request, 'لطفاً اطلاعات را به درستی وارد کنید.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('login')


def password_reset_request_view(request):
    """درخواست بازیابی رمز با ارسال OTP"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)

                # تولید کد OTP
                otp_code = str(random.randint(100000, 999999))

                # حذف OTP‌های قبلی برای این کاربر
                PasswordResetOTP.objects.filter(email=email).delete()

                # ایجاد OTP جدید
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

                # ارسال ایمیل
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
    """تأیید کد OTP"""
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
                    # علامت‌گذاری OTP به عنوان استفاده شده
                    otp.is_used = True
                    otp.save()

                    # پاک کردن رمز عبور قبلی از دیتابیس
                    user = CustomUser.objects.get(id=user_id)
                    user.set_password('')  # رمز رو خالی می‌کنیم
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
    """تعیین رمز عبور جدید"""
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

                # تنظیم رمز عبور جدید
                user.set_password(new_password)
                user.save()

                # پاک کردن session
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


# ویوهای index و guest_message بدون تغییر می‌مونن...

# def password_reset_view(request):
#     if request.user.is_authenticated:
#         return redirect('index')
#
#     if request.method == 'POST':
#         form = PasswordResetForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             try:
#                 user = CustomUser.objects.get(email=email)
#
#                 # ایجاد توکن بازنشانی
#                 reset_token = PasswordResetToken.objects.create(user=user)
#
#                 messages.success(request, 'لینک بازنشانی رمز عبور به ایمیل شما ارسال شد.')
#                 return redirect('login')
#             except CustomUser.DoesNotExist:
#                 messages.error(request, 'کاربری با این ایمیل یافت نشد.')
#     else:
#         form = PasswordResetForm()
#
#     return render(request, 'password_reset.html', {'form': form})
#

# def password_reset_confirm_view(request, token):
#     if request.user.is_authenticated:
#         return redirect('index')
#
#     try:
#         reset_token = PasswordResetToken.objects.get(token=token)
#         if not reset_token.is_valid():
#             messages.error(request, 'لینک بازنشانی منقضی شده است.')
#             return redirect('password_reset')
#     except PasswordResetToken.DoesNotExist:
#         messages.error(request, 'لینک بازنشانی نامعتبر است.')
#         return redirect('password_reset')
#
#     if request.method == 'POST':
#         form = PasswordResetConfirmForm(request.POST)
#         if form.is_valid():
#             new_password = form.cleaned_data['new_password1']
#             user = reset_token.user
#             user.set_password(new_password)
#             user.save()
#
#             reset_token.is_used = True
#             reset_token.save()
#
#             messages.success(request, 'رمز عبور شما با موفقیت تغییر کرد.')
#             return redirect('login')
#     else:
#         form = PasswordResetConfirmForm()
#
#     return render(request, 'password_reset_confirm.html', {
#         'form': form,
#         'token': token
#     })


@login_required
def index(request):
    """صفحه اصلی بعد از لاگین"""
    return render(request, 'index.html')


def guest_message(request):
    """صفحه نمایش برای کاربران مهمان"""
    return render(request, 'guest_message.html')
