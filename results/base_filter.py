from django_filters import rest_framework as filters
from rest_framework.exceptions import NotFound
from django.db.models import Q


class StrictFilterSet(filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        always_allowed_params = ['page', 'page_size', 'exclude_fields', 'exclude_stats_fields', 'team_names', 'months', 'nickname']
        allowed_params = list(self.filters.keys()) + always_allowed_params
        for param in self.request.GET.keys():
            if param not in allowed_params:
                raise NotFound(f"Invalid parameter: '{param}'")

    def filter_by_teams(self, queryset, name, value):
        teams = [t.strip() for t in value.split(',') if t.strip()]
        return queryset.filter(
            Q(team_won__in=teams) | Q(team_lost__in=teams)
        )