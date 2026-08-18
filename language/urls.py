from django.urls import path
from . import views

app_name = 'language'

urlpatterns = [
    path('', views.language_home, name='home'),


    path('drag-drop/', views.drag_drop_game, name='drag_drop_game'),
    path('check-match/', views.check_match, name='check_match'),
    path('get-new-words/', views.get_new_words, name='get_new_words'),
    path('save-game-score/', views.save_game_score, name='save_game_score'),
    path('word-guessing/', views.word_guessing_game, name='word_guessing'),
    path('word-scramble/', views.word_scramble_game, name='word_scramble'),
    path('save-guessing-score/', views.save_guessing_score, name='save_guessing_score'),
    path('save-scramble-score/', views.save_scramble_score, name='save_scramble_score'),

    path('dictation/', views.dictation_game, name='dictation'),
    path('save-dictation-score/', views.save_dictation_score, name='save_dictation_score'),
    path('word-sprint/', views.word_sprint_game, name='word_sprint'),
    path('save-sprint-score/', views.save_sprint_score, name='save_sprint_score'),
]
