from django_filters import rest_framework as filters
from results.models import Match, Team, Player
from .base_filter import StrictFilterSet
from django.db.models import Q


class MatchFilter(StrictFilterSet):
    date_after = filters.DateFilter(field_name='date', lookup_expr='gte')
    date_before = filters.DateFilter(field_name='date', lookup_expr='lte')
    team_names = filters.CharFilter(method='filter_by_teams')

    class Meta:
        model = Match
        fields = {
            'date': ['exact'],  # Для точного совпадения даты
            'team_won': ['exact', 'icontains'],
            'team_lost': ['exact', 'icontains'],
            'event': ['exact', 'icontains'],
            'hltv_id': ['exact'],
        }


class TeamFilter(StrictFilterSet):
    class Meta:
        model = Team
        fields = {
            'name': ['exact', 'icontains'],
        }


class PlayerFilter(StrictFilterSet):
    class Meta:
        model = Player
        fields = {
            'nickname': ['exact'],
            'country': ['exact'],
        }
