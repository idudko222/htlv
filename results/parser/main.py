from results.parser.parser import DataParser
from selenium_driver import SeleniumDriver
from config import config
import django
import os
import time
from data_class import MatchDetails

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hltv.settings')
django.setup()

from results.models import Match, MatchMap, PlayerStats, Map, Player, Team

BASE_URL = 'https://www.hltv.org/results'


def parse_match_results():
    base_url = BASE_URL
    selenium_driver = SeleniumDriver()
    driver = selenium_driver.driver
    try:
        data_parser = DataParser()
        max_matches = 100  # Максимальное количество матчей для парсинга
        matches_per_page = 100  # Количество матчей на странице
        match_urls = []

        for page in range(0, max_matches, matches_per_page):
            current_url = f"{base_url}?offset={page}"
            html = data_parser.get_html(driver, current_url)
            if html:
                parsed_data = data_parser.parse(html, base_url)

                if parsed_data:
                    for match_data in parsed_data:
                        try:
                            Match.objects.create(
                                team_won=match_data.team_won,
                                team_lost=match_data.team_lost,
                                score_lost=match_data.score_lost,
                                score_won=match_data.score_won,
                                date=match_data.date,
                                time=match_data.time,
                                match_format=match_data.match_format,
                                hltv_id=match_data.match_id,
                                event=match_data.event_name,
                            )
                            print(
                                f"Сохранен матч: {match_data.team_won} {match_data.score_won}:"
                                f"{match_data.score_lost} {match_data.team_lost}"
                            )

                            if match_data.match_url:
                                match_urls.append(match_data.match_url)


                        except Exception as e:
                            print(f'Ошибка сохранения: {e}')

        for url in match_urls:
            try:
                time.sleep(1)  # Задержка между запросами
                html = data_parser.get_html(driver, url)
                if not html:
                    continue

                match_details = data_parser.parse_match_details(driver, url)
                if not match_details:
                    continue

                save_match_details(match_details)

            except Exception as e:
                print(f'Ошибка парсинга детальной страницы {url}: {e}')
                continue

    except Exception as e:
        print(f'Ошибка в парсинге: {e}')
    finally:
        driver.quit()


def save_match_details(details: MatchDetails):
    try:
        print(f"[DEBUG] Проверка данных для матча ID {details.match_link}:")
        print(f"Количество карт: {len(details.maps)}")
        print(f"Количество игроков: {len(details.players_stats)}")

        try:
            match = Match.objects.get(hltv_id=details.match_link)
            print(f"[DEBUG] Матч найден в БД: ID {details.match_link}")
        except Match.DoesNotExist:
            print(f"[ОШИБКА] Матч с HLTV ID {details.match_link} не найден в таблице Match.")
            return

        if not details.maps:
            print("[ОШИБКА] Нет данных о картах для сохранения.")
            return  # Прекращаем выполнение, если карт нет

        match = Match.objects.get(hltv_id=details.match_link)
        for map_data in details.maps:
            map_obj, _ = Map.objects.get_or_create(name=map_data.map_name)
            winning_team, _ = Team.objects.get_or_create(name=map_data.winner)
            match_map = MatchMap.objects.create(
                match=match,
                map=map_obj,
                score_team1=map_data.score_team1,
                score_team2=map_data.score_team2,
                winner=winning_team
            )

            for player_stats in details.players_stats:
                player, _ = Player.objects.get_or_create(
                    nickname=player_stats.nickname,
                    defaults={
                        'country': player_stats.country if player_stats.country else ''
                    }
                )
                player_team, _ = Team.objects.get_or_create(name=player_stats.team)


                # Создание статистики игрока
                PlayerStats.objects.create(
                    match=match_map,
                    player=player,
                    team=player_team,
                    kills=player_stats.kills,
                    deaths=player_stats.deaths,
                    adr=player_stats.adr,
                    kast=player_stats.kast,
                    rating=player_stats.rating
                )

        print(f"Сохранены детали матча ID {details.match_link}")

    except Exception as e:
        print(f'Ошибка сохранения деталей матча: {e}')


if __name__ == '__main__':
    parse_match_results()
