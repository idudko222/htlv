from results.models import Match, Team, Player, PlayerStats, Map, MatchMap
from rest_framework import serializers


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'


class PlayerStatsSerializer(serializers.ModelSerializer):
    player = serializers.CharField(source='player.nickname')
    team = serializers.CharField(source='team.name')

    class Meta:
        model = PlayerStats
        fields = ['player', 'team', 'kills', 'deaths', 'adr', 'kast', 'rating']


class MatchMapSerializer(serializers.ModelSerializer):
    map = serializers.CharField(source='map.name')
    winner = serializers.CharField(source='winner.name')

    class Meta:
        model = MatchMap
        fields = ['map', 'score_team1', 'score_team2', 'winner']


class MatchFullSerializer(serializers.ModelSerializer):
    maps = MatchMapSerializer(many=True, source='matchmap_set')
    players_stats = serializers.SerializerMethodField()
    team_won = serializers.CharField()
    team_lost = serializers.CharField()

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.get('context', {}).get('exclude_fields', [])
        super().__init__(*args, **kwargs)

        for field_name in exclude_fields:
            if field_name in self.fields:
                self.fields.pop(field_name)


    def get_players_stats(self, obj):
        if 'players_stats' in self.fields:
            match_maps = obj.matchmap_set.all()
            stats = PlayerStats.objects.filter(
                match__in=match_maps
            ).select_related('player', 'team')
            return PlayerStatsSerializer(stats, many=True).data
        return None

    class Meta:
        model = Match
        fields = ['hltv_id', 'team_won', 'team_lost', 'date',
                  'time', 'event', 'match_format', 'maps', 'players_stats']
