from django_filters import rest_framework as filters
from rest_framework.exceptions import NotFound


class StrictFilterSet(filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        always_allowed_params = ['page', 'page_size', 'exclude_fields', 'exclude_stats_fields', 'team_names']

        allowed_params = list(self.filters.keys()) + always_allowed_params
        for param in self.request.GET.keys():
            if param not in allowed_params:
                raise NotFound(f"Invalid parameter: '{param}'")
