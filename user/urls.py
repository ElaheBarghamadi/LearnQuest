from django.urls import path
from . import views

urlpatterns = [

    path('', views.home_redirect, name='home'),


    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),


    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('new-password/', views.new_password_view, name='password_reset'),


    path('u/<str:username>/', views.public_profile, name='public_profile'),
    path('api/profile/<str:username>/', views.profile_card_api, name='profile_card_api'),


]
