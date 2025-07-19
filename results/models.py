from django.db import models

class Match(models.Model):
    team_won = models.CharField(max_length=50)
    team_lost = models.CharField(max_length=50)
    score_won = models.IntegerField()
    score_lost = models.IntegerField()
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    event = models.CharField(max_length=100, null=True, blank=True)
    match_format = models.IntegerField(null=True, blank=True)
    hltv_id = models.IntegerField(unique=True, null=True, blank=True)

class Team(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hltv_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class Player(models.Model):
    nickname = models.CharField(max_length=50)
    #full_name = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    # hltv_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.nickname

class Map(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class MatchMap(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    score_team1 = models.IntegerField()
    score_team2 = models.IntegerField()
    winner = models.ForeignKey(Team, on_delete=models.CASCADE)

    def __str__(self):
        return self.map.name


class PlayerStats(models.Model):
    id = models.IntegerField(primary_key=True)
    match = models.ForeignKey(MatchMap, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    kills = models.IntegerField()
    deaths = models.IntegerField()
    adr = models.FloatField()
    kast = models.FloatField()
    rating = models.FloatField()

    def __str__(self):
        return f'Игрок {self.player} команды {self.team} сыграл c рейтингом {self.rating} '
