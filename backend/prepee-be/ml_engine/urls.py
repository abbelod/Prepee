from django.urls import path
from . import views

urlpatterns = [
    # Difficulty prediction
    path('difficulty/<int:question_id>/', views.get_question_difficulty, name='question-difficulty'),
    path('difficulty/analyze/', views.analyze_difficulty, name='analyze-difficulty'),

    # Recommendation engine
    path('recommend/', views.get_recommendations, name='get-recommendations'),
    path('recommend/practice/', views.get_practice_set, name='get-practice-set'),

    # Student profile
    path('profile/', views.get_student_profile, name='student-profile'),

    # Cheating detection (admin)
    path('cheating/flags/', views.list_cheating_flags, name='cheating-flags'),
    path('cheating/flags/<int:user_id>/', views.user_cheating_flags, name='user-cheating-flags'),

    # Evaluation report (admin)
    path('evaluation/report/', views.evaluation_report, name='evaluation-report'),
]
