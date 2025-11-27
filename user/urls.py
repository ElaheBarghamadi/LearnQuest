from django.urls import path
from . import views

urlpatterns = [
    # صفحه اصلی
    path('', views.home_redirect, name='home'),

    # احراز هویت
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # بازنشانی رمز عبور
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('new-password/', views.new_password_view, name='password_reset'),

    # صفحات اصلی بعد از لاگین
    path('dashboard/', views.index, name='index'),
    path('english/', views.guest_message, name='english'),
    path('games/', views.guest_message, name='games'),
    path('blog/', views.guest_message, name='blog'),
    path('profile/', views.guest_message, name='profile'),

    # پیام مهمان
    path('guest-message/', views.guest_message, name='guest_message'),
]
