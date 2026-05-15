from django.urls import path
from .views import find_match, clear_matchmaking_queues, process_quiz_submission, cancel_matchmaking

urlpatterns = [
    path("find/", find_match, name="find_match"),
    path("clear/", clear_matchmaking_queues, name="clear_queues"),
    path("cancel/", cancel_matchmaking, name="cancel_matchmaking"),
    path("<int:match_id>/submit-answer/", process_quiz_submission, name="submit_answer"),
]

