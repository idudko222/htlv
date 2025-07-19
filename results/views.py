from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from results.models import Match, Team, PlayerStats, MatchMap
from results.serializers import TeamSerializer, MatchFullSerializer
from results.filters import MatchFilter
from rest_framework import permissions
from rest_framework import status, viewsets
from django.db.models import Prefetch


class BaseViewSet(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        """
           Переопределение стандартного метода ViewSet.
           Добавляет проверку на пустой queryset и кастомные сообщения об ошибках.
        """
        try:
            queryset = self.filter_queryset(self.get_queryset())

            if not queryset.exists():
                return Response(
                    {"detail": "No matches found with these filters"},
                    status=status.HTTP_404_NOT_FOUND
                )

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except NotFound as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all().order_by('id')
    serializer_class = TeamSerializer
    permission_classes = [permissions.AllowAny]


class MatchStatsViewSet(BaseViewSet):
    serializer_class = MatchFullSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = MatchFilter

    def get_queryset(self):
        """
           Полная замена стандартного get_queryset().
           Оптимизирует запросы через prefetch_related и select_related.
        """
        queryset = Match.objects.prefetch_related(
            Prefetch('matchmap_set', queryset=MatchMap.objects.select_related('map', 'winner'))
        ).order_by('-date')

        return queryset.prefetch_related(
            Prefetch(
                'matchmap_set__playerstats_set',
                queryset=PlayerStats.objects.select_related('player', 'team')
            )
        )

    def get_serializer_context(self):
        """
           Переопределение стандартного метода с целью добавления кастомных параметров в контекст сериализатора
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        exclude_fields = self.request.query_params.get('exclude_fields', '')
        exclude_stats_fields = self.request.query_params.get('exclude_stats_fields', '')
        context['exclude_fields'] = [f.strip() for f in exclude_fields.split(',') if f.strip()]
        context['exclude_stats_fields'] = [f.strip() for f in exclude_stats_fields.split(',') if f.strip()]
        if 'stats' in context['exclude_stats_fields']:
            context['exclude_stats_fields'] = 'kills,deaths,adr,kast,rating'
        return context
