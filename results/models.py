from django.db import models

class Match(models.Model):
    team_won = models.CharField(max_length=20)
    team_lost = models.CharField(max_length=20)
    score_won = models.IntegerField()
    score_lost = models.IntegerField()
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
