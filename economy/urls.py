from django.urls import path

from . import views

app_name = 'economy'

urlpatterns = [
    path('wallet/', views.wallet_view, name='wallet'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('season/', views.season_view, name='season'),
    path('season/buy-pass/', views.season_pass_buy, name='season_pass_buy'),
    path('season/claim/<int:level_number>/<str:track>/', views.season_claim_view, name='season_claim'),
    path('pet/', views.pet_view, name='pet'),
    path('pet/<int:pet_id>/feed/', views.pet_feed_view, name='pet_feed'),
    path('pet/<int:pet_id>/activate/', views.pet_activate_view, name='pet_activate'),
    path('pet/<int:pet_id>/rename/', views.pet_rename_view, name='pet_rename'),
    path('use-hint/', views.use_hint_ticket, name='use_hint'),
    path('use-time-card/', views.use_time_card, name='use_time_card'),
    path('retry-status/<int:quiz_id>/', views.retry_ticket_status, name='retry_status'),
]
