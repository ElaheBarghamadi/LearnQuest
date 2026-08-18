from django.urls import path

from . import views

app_name = 'panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users_list, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/grant/', views.grant, name='grant'),
    path('users/<int:user_id>/item/', views.grant_item, name='grant_item'),
    path('users/<int:user_id>/toggle-active/', views.toggle_active, name='toggle_active'),
]
