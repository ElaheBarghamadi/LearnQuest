from django.urls import path
from . import views

app_name = 'Games'

urlpatterns = [
    path('sudoku/', views.sudoku_view, name='sudoku'),
    path('save-sudoku-score/', views.save_sudoku_score, name='save_sudoku_score'),
    path('memory/', views.memory_game, name='memory'),
    path('number-puzzle/', views.number_puzzle, name='number_puzzle'),
    path('save-memory-score/', views.save_memory_score, name='save_memory_score'),
    path('save-puzzle-score/', views.save_puzzle_score, name='save_puzzle_score'),
    path('iq-test/', views.iq_test, name='iq_test'),
    path('save-iq-score/', views.save_iq_score, name='save_iq_score'),

    path('snake/', views.snake_game, name='snake'),
    path('save-snake-score/', views.save_snake_score, name='save_snake_score'),
    path('2048/', views.game_2048, name='game_2048'),
    path('save-2048-score/', views.save_2048_score, name='save_2048_score'),
    path('reaction/', views.reaction_game, name='reaction'),
    path('save-reaction-score/', views.save_reaction_score, name='save_reaction_score'),

    path('simon/', views.simon_game, name='simon'),
    path('save-simon-score/', views.save_simon_score, name='save_simon_score'),
    path('whack/', views.whack_game, name='whack'),
    path('save-whack-score/', views.save_whack_score, name='save_whack_score'),
    path('tictactoe/', views.tictactoe_game, name='tictactoe'),
    path('save-tictactoe-score/', views.save_tictactoe_score, name='save_tictactoe_score'),

    path('minesweeper/', views.minesweeper_game, name='minesweeper'),
    path('save-minesweeper-score/', views.save_minesweeper_score, name='save_minesweeper_score'),
    path('breakout/', views.breakout_game, name='breakout'),
    path('save-breakout-score/', views.save_breakout_score, name='save_breakout_score'),
]
