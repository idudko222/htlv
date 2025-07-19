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
        self.exclude_stats_fields = kwargs.get('context', {}).get('exclude_stats_fields', [])
        super().__init__(*args, **kwargs)

        for field_name in exclude_fields:
            if field_name in self.fields:
                self.fields.pop(field_name)

    def get_queryset_stats(self, obj):
        """Получаем QuerySet со статистикой игроков"""
        player_ids = set()
        stats = []
        for stat in PlayerStats.objects.filter(match__match=obj).select_related('player', 'team'):
            if stat.player_id not in player_ids:
                stats.append(stat)
                player_ids.add(stat.player_id)
        return stats

    def get_players_stats_data(self, queryset):
        """Преобразуем QuerySet в данные статистики"""
        stats_data = PlayerStatsSerializer(queryset, many=True).data
        return self.filter_stats_fields(stats_data)

    def get_players_stats(self, obj):
        if 'players_stats' in self.fields:
            stats_queryset = self.get_queryset_stats(obj)
            return self.get_players_stats_data(stats_queryset)
        return None

    def filter_stats_fields(self, stats_data):
        """Фильтруем поля статистики игроков согласно exclude_stats_fields"""
        if not self.exclude_stats_fields:
            return stats_data

        filtered_stats = []
        for stat in stats_data:
            filtered_stat = {}
            for field, value in stat.items():
                if field not in self.exclude_stats_fields:
                    filtered_stat[field] = value
            filtered_stats.append(filtered_stat)
        return filtered_stats

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request:
            return data

        team_names_param = request.query_params.get('team_names', '')
        if not team_names_param:
            return data

        team_names = [name.strip() for name in team_names_param.split(',') if name.strip()]

        if (data['team_won'] not in team_names) and (data['team_lost'] not in team_names):
            return None
        return data

    class Meta:
        model = Match
        fields = ['hltv_id', 'team_won', 'team_lost', 'date',
                  'time', 'event', 'match_format', 'maps', 'players_stats']
