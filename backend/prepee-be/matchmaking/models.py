from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
class Match(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    questions = models.JSONField(null=True, blank=True)
    category = models.CharField(max_length=50, default="general")
    time_control = models.IntegerField(default=60)

class MatchPlayer(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    time_taken = models.FloatField(default=0)
    submitted = models.BooleanField(default=False)
    is_winner = models.BooleanField(default=False)
    submission = models.JSONField(null=True, blank=True)

    
