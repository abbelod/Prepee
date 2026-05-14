from django.db import models

# Create your models here.

class Subject(models.Model):
    name = models.CharField(max_length=30)


class Questions(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    text = models.TextField()
    explanation = models.TextField(blank=True)

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_option = models.CharField(
        max_length=1,
          choices=[('A', 'A'), ('B','B'), ('C', 'C'), ('D', 'D')]
        )
    
