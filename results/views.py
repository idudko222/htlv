from datetime import timedelta, datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from results.models import Match, Team, PlayerStats, MatchMap, Player
from results.serializers import TeamSerializer, MatchFullSerializer, PlayerStatsSimpleSerializer
from results.filters import MatchFilter, PlayerStatsFilter
from rest_framework import permissions
from rest_framework import status, viewsets
from django.db.models import Prefetch, Avg, Count
from rest_framework.decorators import action
from django.http import StreamingHttpResponse
from rest_framework.permissions import AllowAny
import csv
from io import StringIO


class BaseViewSet(viewsets.ReadOnlyModelViewSet ):
    def handle_exceptions(self, exc):
        if isinstance(exc, NotFound):
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exceptions(exc)

    def list(self, request, *args, **kwargs):
        """
           Переопределение стандартного метода ViewSet.
           Добавляет проверку на пустой queryset и кастомные сообщения об ошибках.
        """
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


class TeamViewSet(BaseViewSet):
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
        """Потоковая выгрузка матчей в новом формате CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        def generate_rows():
            buffer = StringIO()
            writer = csv.writer(buffer)

            headers = [
                'team1', 'team1_roster', 'team2', 'team2_roster',
                'bo', 'match_score',
                'map1', 'map1_score', 'map2', 'map2_score',
                'map3', 'map3_score', 'map4', 'map4_score',
                'map5', 'map5_score', 'winner', 'hltv_id'
            ]
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            for match in data:
                team1 = match['team_won']
                team2 = match['team_lost']
                bo = match.get('match_format', '')
                winner = match['team_won']
                hltv_id = match['hltv_id']

                # Получаем составы команд
                team_rosters = {}
                for player in match.get('players_stats', []):
                    team_name = player['team']
                    if team_name not in team_rosters:
                        team_rosters[team_name] = []
                    team_rosters[team_name].append(player['player'])

                # Обрабатываем карты
                maps_data = match.get('maps', [])
                map_fields = []
                team1_wins = 0
                team2_wins = 0

                for i in range(5):
                    if i < len(maps_data):
                        map_data = maps_data[i]
                        # Определяем победителя на карте по winner.name (или winner.id, если он есть в сериализованных данных)
                        if 'winner' in map_data and map_data['winner'] == team1:
                            team1_wins += 1
                            score = f"{map_data['score_team1']}-{map_data['score_team2']}"
                        else:
                            team2_wins += 1
                            score = f"{map_data['score_team2']}-{map_data['score_team1']}"
                        map_fields.extend([map_data['map'], score])
                    else:
                        map_fields.extend(['', ''])

                # Формируем счет матча
                match_score = f"{team1_wins}-{team2_wins}"

                # Создаем строку для CSV
                row = [
                    team1,
                    ', '.join(team_rosters.get(team1, [])),
                    team2,
                    ', '.join(team_rosters.get(team2, [])),
                    bo,
                    match_score,
                    *map_fields,
                    winner,
                    hltv_id
                ]
                writer.writerow(row)
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        response = StreamingHttpResponse(
            generate_rows(),
            content_type='text/csv; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="matches_single_row.csv"'
        return response


class PlayerStatsViewSet(BaseViewSet):
    queryset = PlayerStats.objects.select_related('player', 'team')
    serializer_class = PlayerStatsSimpleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlayerStatsFilter
    pagination_class = PageNumberPagination

    def get_queryset(self):
        months = int(self.request.query_params.get('months', 1))
        last_month = datetime.now() - timedelta(days=30 * months)

        # Создаем базовый QuerySet с агрегацией
        queryset = (
            PlayerStats.objects
            .filter(match__match__date__gte=last_month)
            .select_related('player', 'team')
            .values('player_id', 'team_id')
            .annotate(
                avg_rating=Avg('rating'),
                avg_kills=Avg('kills'),
                avg_deaths=Avg('deaths'),
                avg_adr=Avg('adr'),
                avg_kast=Avg('kast'),
                matches_played=Count('match__match_id', distinct=True)
            )
        )

        return queryset

    def list(self, request, *args, **kwargs):
        # Получаем отфильтрованный и агрегированный QuerySet
        queryset = self.filter_queryset(self.get_queryset())

        # Получаем связанные объекты Player и Team
        player_stats = PlayerStats.objects.filter(
            player_id__in=[stat['player_id'] for stat in queryset]
        ).select_related('player', 'team')

        # Собираем результаты
        results = []
        for stat in queryset:
            ps = next(ps for ps in player_stats if ps.player_id == stat['player_id'])
            results.append({
                'player': ps.player,
                'team': ps.team,
                'avg_rating': round(stat['avg_rating'], 2),
                'avg_kills': round(stat['avg_kills'], 2),
                'avg_deaths': round(stat['avg_deaths'], 2),
                'avg_adr': round(stat['avg_adr'], 2),
                'avg_kast': round(stat['avg_kast'], 2),
                'matches_played': stat['matches_played']
            })

        # Применяем пагинацию к результатам
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)
