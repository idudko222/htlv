from results.models import Match, Team, Player, PlayerStats, Map, MatchMap
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    Сериализатор с динамическим выбором полей
    """

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.get('context', {}).get('exclude_fields', [])
        super().__init__(*args, **kwargs)

        if exclude_fields:
            for field in exclude_fields:
                self.fields.pop(field, None)


class TeamSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'


class PlayerStatsSerializer(DynamicFieldsModelSerializer):
    player = serializers.CharField(source='player.nickname')
    team = serializers.CharField(source='team.name')

    class Meta:
        model = PlayerStats
        fields = ['player', 'team', 'kills', 'deaths', 'adr', 'kast', 'rating']


class MatchMapSerializer(DynamicFieldsModelSerializer):
    map = serializers.CharField(source='map.name')
    winner = serializers.CharField(source='winner.name')

    class Meta:
        model = MatchMap
        fields = ['map', 'score_team1', 'score_team2', 'winner']


class MatchFullSerializer(DynamicFieldsModelSerializer):
    maps = MatchMapSerializer(many=True, source='matchmap_set')
    players_stats = serializers.SerializerMethodField()
    team_won = serializers.CharField()
    team_lost = serializers.CharField()

    def __init__(self, *args, **kwargs):
        self.exclude_stats_fields = kwargs.get('context', {}).get('exclude_stats_fields', [])
        super().__init__(*args, **kwargs)

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
        """
        Метод сериализатора, который проводит фильтрацию по командам входящим в контекст запроса
        """
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


class PlayerSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'nickname']


class PlayerStatsSimpleSerializer(DynamicFieldsModelSerializer):
    nickname = serializers.CharField(source='player.nickname')
    country = serializers.CharField(source='player.country')

    class Meta:
        model = PlayerStats
        fields = ['player','country' , 'nickname', 'team', 'rating']
