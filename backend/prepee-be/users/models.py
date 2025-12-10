from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    country = models.CharField(max_length=100, blank=False, null=True)
    city = models.CharField(max_length=100, blank=False, null=True)
    elo = models.IntegerField(default=1000)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
# Create your models here.
