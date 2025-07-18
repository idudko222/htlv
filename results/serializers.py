from results.models import Match, Team, Player, PlayerStats, Map, MatchMap
from rest_framework import serializers

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'

