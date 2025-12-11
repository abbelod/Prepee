from django.urls import path
from .views import leaderboard_api

urlpatterns = [
    path("leaderboards/", leaderboard_api, name="leaderboards"),
]

