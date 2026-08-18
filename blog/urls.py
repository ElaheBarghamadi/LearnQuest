from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.blog_home, name='blog_home'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),

    path('get-article/<int:article_id>/', views.legacy_article_redirect),
    path('add-comment/', views.add_comment, name='add_comment'),
    path('like/<int:article_id>/', views.like_article, name='like_article'),
    path('like-comment/<int:comment_id>/', views.like_comment, name='like_comment'),
]
