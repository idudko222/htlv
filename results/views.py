from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from results.models import Match, Team, PlayerStats, MatchMap
from results.serializers import TeamSerializer, MatchFullSerializer
from results.filters import MatchFilter
from rest_framework import permissions
from rest_framework import status, viewsets
from django.db.models import Prefetch
from rest_framework.decorators import action
from django.http import StreamingHttpResponse
from rest_framework.permissions import AllowAny
import csv
import json
from io import StringIO


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
                filtered_data = [item for item in serializer.data if item is not None]
                return self.get_paginated_response(filtered_data)

            serializer = self.get_serializer(queryset, many=True)
            filtered_data = [item for item in serializer.data if item is not None]
            return Response(filtered_data)

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

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def export_csv(self, request):
        """Потоковая выгрузка матчей в CSV с сохранением структуры JSON"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        def generate_rows():
            # Буфер для построчной записи
            buffer = StringIO()
            writer = csv.writer(buffer)

            # Заголовки CSV (основные поля + поля для maps и players_stats)
            headers = [
                'hltv_id', 'team_won', 'team_lost', 'date', 'time', 'event', 'match_format',
                'maps_count', 'maps_json',  # Для вложенных карт
                'players_count', 'players_stats_json'  # Для статистики игроков
            ]
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            # Данные
            for match in data:
                # Основные поля
                row = [
                    match['hltv_id'],
                    match['team_won'],
                    match['team_lost'],
                    match['date'],
                    match.get('time', ''),
                    match.get('event', ''),
                    match.get('match_format', ''),
                ]

                # Обработка maps
                maps_data = match.get('maps', [])
                row.append(len(maps_data))  # Количество карт
                row.append(json.dumps(maps_data, ensure_ascii=False))  # JSON строкой

                # Обработка players_stats
                players_data = match.get('players_stats', [])
                row.append(len(players_data))  # Количество игроков
                row.append(json.dumps(players_data, ensure_ascii=False))  # JSON строкой

                writer.writerow(row)
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        response = StreamingHttpResponse(
            generate_rows(),
            content_type='text/csv; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="matches_structured.csv"'
        return response
