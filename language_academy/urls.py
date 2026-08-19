from django.urls import path
from . import views

app_name = 'language_academy'

urlpatterns = [

    path('', views.world_map, name='world_map'),
    path('world/<int:world_id>/', views.world_detail, name='world_detail'),
    path('chapter/<int:chapter_id>/', views.chapter_detail, name='chapter_detail'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),


    path('dashboard/', views.learner_dashboard, name='learner_dashboard'),


    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),


    path('exam/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('exam/result/<int:attempt_id>/', views.exam_result, name='exam_result'),


    path('dialogue/<int:dialogue_id>/', views.start_dialogue, name='start_dialogue'),


    path('vocabulary/', views.vocabulary_list, name='vocabulary_list'),
    path('vocabulary/review/', views.vocabulary_review, name='vocabulary_review'),


    path('certificates/', views.my_certificates, name='my_certificates'),
    path('certificate/<int:certificate_id>/', views.certificate_detail, name='certificate_detail'),
    path('certificate/verify/', views.certificate_verify, name='certificate_verify'),
    path('certificate/verify/<str:code>/', views.certificate_verify, name='certificate_verify'),


    path('writing/', views.writing_practice, name='writing_practice'),
    path('writing/<int:lesson_id>/', views.writing_practice, name='writing_practice_with_lesson'),
    path('writing/evaluate/', views.evaluate_writing, name='evaluate_writing'),


    path('api/update-progress/<int:lesson_id>/', views.update_lesson_progress, name='update_lesson_progress'),

    path('exam/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('exam/save-answer/', views.save_exam_answer, name='save_exam_answer'),
    path('exam/save-time/', views.save_exam_time, name='save_exam_time'),
    path('exam/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),

    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/save-answer/', views.save_quiz_answer, name='save_quiz_answer'),
    path('quiz/save-time/', views.save_quiz_time, name='save_quiz_time'),
    path('quiz/submit/<int:quiz_id>/', views.submit_quiz, name='submit_quiz'),
    path('quiz/submit-auto/<str:session_key>/', views.submit_quiz_auto, name='submit_quiz_auto'),
    path('quiz/result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('vocabulary/hub/', views.vocabulary_learning_hub, name='vocabulary_hub'),
    path('vocabulary/flashcards/', views.vocabulary_flashcards, name='vocabulary_flashcards'),
    path('vocabulary/flashcard-action/', views.vocabulary_flashcard_action, name='vocabulary_flashcard_action'),
    path('vocabulary/matching/', views.vocabulary_matching_game, name='vocabulary_matching_game'),
    path('vocabulary/matching-result/', views.vocabulary_matching_result, name='vocabulary_matching_result'),
    path('vocabulary/sentence-builder/', views.vocabulary_sentence_builder, name='vocabulary_sentence_builder'),
    path('vocabulary/spaced-repetition/', views.vocabulary_spaced_repetition, name='vocabulary_spaced_repetition'),
    path('vocabulary/spaced-repetition-action/', views.vocabulary_spaced_repetition_action,
         name='vocabulary_spaced_repetition_action'),
    path('vocabulary/stats/', views.vocabulary_stats, name='vocabulary_stats'),
    path('vocabulary/mark-learned/<int:word_id>/', views.vocabulary_mark_learned, name='vocabulary_mark_learned'),
    path('vocabulary/add-to-practice/<int:word_id>/', views.vocabulary_add_to_practice,
         name='vocabulary_add_to_practice'),
    path('vocabulary/add-to-review/<int:word_id>/', views.vocabulary_add_to_review, name='vocabulary_add_to_review'),

    path('grammar/', views.grammar_hub, name='grammar_hub'),
    path('idioms/', views.idioms_hub, name='idioms_hub'),
    path('idioms/placement/', views.idioms_placement, name='idioms_placement'),
    path('idioms/placement/quiz/<int:attempt_id>/', views.idioms_placement_quiz, name='idioms_placement_quiz'),
    path('idioms/placement/submit/<int:attempt_id>/', views.idioms_placement_submit, name='idioms_placement_submit'),
    path('idioms/placement/result/<int:attempt_id>/', views.idioms_placement_result, name='idioms_placement_result'),
    path('idioms/learn/', views.idiom_learn, name='idiom_learn'),
    path('idioms/mark/', views.idiom_mark_learned, name='idiom_mark_learned'),
    path('idioms/flashcards/', views.idiom_flashcards, name='idiom_flashcards'),
    path('idioms/review/', views.idiom_review, name='idiom_review'),
    path('ai/chat/', views.ai_chat_send, name='ai_chat_send'),
    path('ai/chat/history/', views.ai_chat_history, name='ai_chat_history'),
    path('ai/challenge/new/', views.ai_challenge_new, name='ai_challenge_new'),
    path('ai/challenge/answer/', views.ai_challenge_answer, name='ai_challenge_answer'),
]
