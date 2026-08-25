from django.urls import path
from . import views

app_name = 'messenger'

urlpatterns = [

    path('', views.messenger_page, name='chat'),


    path('join/<str:token>/', views.join_group, name='join_group'),


    path('conversations/', views.get_conversations, name='conversations'),
    path('conversation/<int:user_id>/', views.get_or_create_conversation, name='conversation'),
    path('messages/<int:conversation_id>/', views.get_messages, name='messages'),
    path('send/', views.send_message, name='send_message'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),


    path('search/', views.search_users, name='search_users'),
    path('online-status/<int:user_id>/', views.online_status, name='online_status'),


    path('create-group/', views.create_group, name='create_group'),
    path('group/<int:conversation_id>/leave/', views.leave_group, name='leave_group'),
    path('group/<int:conversation_id>/regenerate-invite/', views.regenerate_invite, name='regenerate_invite'),
    path('group/<int:conversation_id>/add-members/', views.group_add_members, name='group_add_members'),
    path('group/<int:conversation_id>/remove-member/<int:user_id>/', views.group_remove_member, name='group_remove_member'),


    path('block/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('blocked/', views.blocked_list, name='blocked_list'),
]
