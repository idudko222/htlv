from django_filters import rest_framework as filters
from results.models import Match, Team, PlayerStats
from .base_filter import StrictFilterSet


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


class PlayerStatsFilter(StrictFilterSet):
    nickname = filters.CharFilter(field_name='player__nickname', lookup_expr='icontains')
    country = filters.CharFilter(field_name='player__country', lookup_expr='iexact')
    team = filters.CharFilter(field_name='team__name', lookup_expr='iexact')
    months = filters.NumberFilter(method='filter_by_months')

    class Meta:
        model = PlayerStats
        fields = ['nickname', 'country', 'team', 'rating']

    def filter_by_months(self, queryset, name, value):
        from django.utils import timezone
        from datetime import timedelta
        period_ago = timezone.now() - timedelta(days=30*int(value))
        return queryset.filter(match__match__date__gte=period_ago)
