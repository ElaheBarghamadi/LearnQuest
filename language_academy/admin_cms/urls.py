from django.urls import path
from . import views

app_name = 'admin_cms'

urlpatterns = [

    path('', views.cms_dashboard, name='dashboard'),


    path('worlds/', views.world_list, name='world_list'),
    path('worlds/create/', views.world_create, name='world_create'),
    path('worlds/<int:world_id>/edit/', views.world_edit, name='world_edit'),
    path('worlds/<int:world_id>/delete/', views.world_delete, name='world_delete'),
    path('worlds/<int:world_id>/toggle-publish/', views.world_toggle_publish, name='world_toggle_publish'),
    path('worlds/<int:world_id>/move/<str:direction>/', views.world_move, name='world_move'),


    path('chapters/create/<int:world_id>/', views.chapter_create, name='chapter_create'),
    path('chapters/<int:chapter_id>/edit/', views.chapter_edit, name='chapter_edit'),
    path('chapters/<int:chapter_id>/delete/', views.chapter_delete, name='chapter_delete'),
    path('chapters/<int:chapter_id>/toggle-publish/', views.chapter_toggle_publish,
         name='chapter_toggle_publish'),


    path('lessons/create/<int:chapter_id>/', views.lesson_create, name='lesson_create'),
    path('lessons/<int:lesson_id>/edit/', views.lesson_edit, name='lesson_edit'),
    path('lessons/<int:lesson_id>/delete/', views.lesson_delete, name='lesson_delete'),
    path('lessons/<int:lesson_id>/toggle-publish/', views.lesson_toggle_publish,
         name='lesson_toggle_publish'),
    path('lessons/<int:lesson_id>/visual-save/', views.lesson_visual_save, name='lesson_visual_save'),
    path('visual-save/', views.academy_visual_save, name='academy_visual_save'),
    path('lessons/<int:lesson_id>/visual-upload/', views.lesson_visual_upload, name='lesson_visual_upload'),


    path('vocabulary/', views.vocabulary_list, name='vocabulary_list'),
    path('vocabulary/create/', views.vocabulary_create, name='vocabulary_create'),
    path('vocabulary/<int:vocab_id>/edit/', views.vocabulary_edit, name='vocabulary_edit'),
    path('vocabulary/<int:vocab_id>/toggle-active/', views.vocabulary_toggle_active,
         name='vocabulary_toggle_active'),
    path('vocabulary/<int:vocab_id>/delete/', views.vocabulary_delete, name='vocabulary_delete'),
    path('vocabulary/categories/', views.vocabulary_categories, name='vocabulary_categories'),
    path('exams/<int:exam_id>/delete/', views.exam_delete, name='exam_delete'),


    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/create/', views.quiz_create, name='quiz_create'),
    path('quizzes/<int:quiz_id>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quizzes/<int:quiz_id>/delete/', views.quiz_delete, name='quiz_delete'),


    path('quizzes/<int:quiz_id>/questions/', views.question_list, name='question_list'),
    path('quizzes/<int:quiz_id>/questions/create/', views.question_create, name='question_create'),
    path('questions/<int:question_id>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:question_id>/delete/', views.question_delete, name='question_delete'),


    path('exams/', views.exam_list, name='exam_list'),
    path('exams/create/', views.exam_create, name='exam_create'),
    path('exams/<int:exam_id>/edit/', views.exam_edit, name='exam_edit'),


    path('badges/', views.badge_list, name='badge_list'),
    path('badges/create/', views.badge_create, name='badge_create'),


    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/progress/', views.user_progress, name='user_progress'),


    path('analytics/', views.analytics_dashboard, name='analytics'),


    path('settings/', views.cms_settings, name='settings'),

    path('exams/<int:exam_id>/questions/', views.exam_question_list, name='exam_question_list'),
    path('exams/<int:exam_id>/questions/create/', views.exam_question_create, name='exam_question_create'),
    path('exam-questions/<int:question_id>/edit/', views.exam_question_edit, name='exam_question_edit'),
    path('exam-questions/<int:question_id>/delete/', views.exam_question_delete, name='exam_question_delete'),
]


urlpatterns += [
    path('shop/products/', views.shop_product_list, name='shop_product_list'),
    path('shop/products/create/', views.shop_product_create, name='shop_product_create'),
    path('shop/products/<int:product_id>/edit/', views.shop_product_edit, name='shop_product_edit'),
    path('shop/products/<int:product_id>/toggle/', views.shop_product_toggle, name='shop_product_toggle'),
    path('shop/products/<int:product_id>/delete/', views.shop_product_delete, name='shop_product_delete'),
    path('certificates/', views.certificate_manage, name='certificate_manage'),
]

urlpatterns += [
    path('blog/articles/', views.blog_article_list, name='blog_article_list'),
    path('blog/articles/create/', views.blog_article_create, name='blog_article_create'),
    path('blog/articles/<int:article_id>/edit/', views.blog_article_edit, name='blog_article_edit'),
    path('blog/articles/<int:article_id>/delete/', views.blog_article_delete, name='blog_article_delete'),
    path('blog/categories/quick-create/', views.blog_category_quick_create, name='blog_category_quick_create'),
]
