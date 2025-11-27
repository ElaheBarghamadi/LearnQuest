from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
import os
from datetime import datetime, timedelta
from django.utils import timezone


# Create your views here.
def index(request):
    return render(request, 'index.html')


def english(request):
    return render(request, 'english.html')


def games(request):
    return render(request, 'games.html')


def blog(request):
    return render(request, 'blog.html')




@login_required
def profile(request):
    """پروفایل اصلی - فقط نمایش"""
    user = request.user

    # محاسبه درصد پیشرفت سطح
    xp_needed_for_next_level = user.level * 1000
    progress_percentage = min(100, (user.xp / xp_needed_for_next_level) * 100) if xp_needed_for_next_level > 0 else 0

    # داده‌های نمونه برای دستاوردها
    achievements = [
        {'name': 'شروع کننده', 'icon': 'award', 'date': '۱۴۰۲/۰۵/۱۰', 'locked': False},
        {'name': '۵ روز متوالی', 'icon': 'fire', 'date': '۱۴۰۲/۰۵/۱۵', 'locked': False},
        {'name': 'هوش برتر', 'icon': 'brain', 'date': '۱۴۰۲/۰۵/۱۸', 'locked': False},
        {'name': 'استاد', 'icon': 'crown', 'date': 'قفل شده', 'locked': True},
        {'name': 'سریع', 'icon': 'rocket', 'date': 'قفل شده', 'locked': True},
        {'name': 'کامل کننده', 'icon': 'gem', 'date': 'قفل شده', 'locked': True},
    ]

    # تاریخچه فعالیت‌های نمونه
    activities = [
        {'title': 'سودوکو سطح متوسط', 'description': '+۵۰ XP کسب کردید', 'icon': 'gamepad', 'time': '۲ ساعت پیش'},
        {'title': 'یادگیری زبان', 'description': '۲۰ کلمه جدید یاد گرفتید', 'icon': 'language', 'time': '۵ ساعت پیش'},
        {'title': 'پازل عددی', 'description': 'رکورد شخصی شکسته شد', 'icon': 'puzzle-piece', 'time': '۱ روز پیش'},
        {'title': 'سوالات هوش', 'description': '۸۰% پاسخ صحیح', 'icon': 'brain', 'time': '۲ روز پیش'},
    ]

    context = {
        'user': user,
        'progress_percentage': progress_percentage,
        'achievements': achievements,
        'activities': activities,
    }

    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    """صفحه ویرایش پروفایل"""
    user = request.user

    if request.method == 'POST':
        # پردازش فرم ویرایش
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        # بروزرسانی اطلاعات کاربر
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if username and username != user.username:
            # بررسی یکتایی نام کاربری
            from django.contrib.auth.models import User
            if not User.objects.filter(username=username).exclude(id=user.id).exists():
                user.username = username
            else:
                messages.error(request, 'این نام کاربری قبلاً ثبت شده است.')

        if email and email != user.email:
            # بررسی یکتایی ایمیل
            if not User.objects.filter(email=email).exclude(id=user.id).exists():
                user.email = email
            else:
                messages.error(request, 'این ایمیل قبلاً ثبت شده است.')

        if phone:
            user.phone = phone

        # پردازش آپلود عکس
        if 'avatar' in request.FILES:
            avatar = request.FILES['avatar']
            # بررسی حجم فایل
            if avatar.size > 2 * 1024 * 1024:  # 2MB
                messages.error(request, 'حجم فایل باید کمتر از ۲ مگابایت باشد.')
            else:
                # ذخیره فایل
                fs = FileSystemStorage()
                filename = fs.save(f'avatars/{user.username}_{avatar.name}', avatar)
                user.avatar = filename
                messages.success(request, 'عکس پروفایل با موفقیت آپلود شد.')

        # تغییر رمز عبور
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'رمز عبور جدید و تکرار آن مطابقت ندارند.')
            elif not user.check_password(current_password):
                messages.error(request, 'رمز عبور فعلی اشتباه است.')
            else:
                user.set_password(new_password)
                messages.success(request, 'رمز عبور با موفقیت تغییر کرد.')
                # لاگین مجدد کاربر بعد از تغییر رمز
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)

        user.save()
        messages.success(request, 'تغییرات با موفقیت ذخیره شد.')
        return redirect('profile')

    # برای GET request
    context = {
        'user': user
    }
    return render(request, 'profile-edit.html', context)
