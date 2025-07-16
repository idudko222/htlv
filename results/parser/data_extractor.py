from bs4 import BeautifulSoup
import re
from datetime import datetime
from data_class import MatchScore, PlayerStats, MatchDetails, MapData, Team
from typing import Optional, List, Dict, Tuple


class ScoreParser:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def parse(self, match_element=None) -> Optional[MatchScore]:
        try:
            score_element = match_element or self.soup.find('div', class_='result-con')
            if not score_element:
                return None

            match_link = score_element.find('a', class_='a-reset')
            match_url = None
            match_id = None

            if match_link and 'href' in match_link.attrs:
                match_url = match_link['href']
                match_id_match = re.search(r'/matches/(\d+)', match_url)
                if match_id_match:
                    match_id = int(match_id_match.group(1))
                    match_url = f"https://www.hltv.org{match_url}"

            match_format = None
            map_text_elem = score_element.find('div', class_='map-text')
            if map_text_elem:
                match_format = map_text_elem.get_text(strip=True).lower()
                if match_format == 'bo3':
                    match_format = 3
                elif match_format == 'bo5':
                    match_format = 5
                else:
                    match_format = 1

            team1_elem = score_element.find('div', class_='team1').find('div', class_='team')
            team2_elem = score_element.find('div', class_='team2').find('div', class_='team')
            score_won_elem = score_element.find('span', class_='score-won')
            score_lost_elem = score_element.find('span', class_='score-lost')
            event_elem = score_element.find('span', class_='event-name')
            if event_elem:
                event_name = event_elem.get_text(strip=True)

            unix_timestamp = score_element.get('data-zonedgrouping-entry-unix')

            formatted_date = self._convert_unix_to_date(unix_timestamp) if unix_timestamp else None
            time = self._convert_unix_to_time(unix_timestamp) if unix_timestamp else None

            winner, loser = self._determine_winner(team1_elem, team2_elem)

            if all([score_won_elem, score_lost_elem, winner, loser]):
                return MatchScore(
                    team_won=winner,
                    team_lost=loser,
                    score_won=score_won_elem.get_text(strip=True),
                    score_lost=score_lost_elem.get_text(strip=True),
                    date=formatted_date,
                    time=time,
                    match_id=match_id,
                    match_url=match_url,
                    match_format=match_format,
                    event_name=event_name,
                )
            return None

        except Exception as e:
            print(f'Score parsing error: {e}')
            return None

    def _determine_winner(self, team1_elem, team2_elem) -> Tuple[Optional[str], Optional[str]]:
        if team2_elem and 'team-won' in team2_elem.get('class', []):
            return (
                team2_elem.get_text(strip=True) if team2_elem else None,
                team1_elem.get_text(strip=True) if team1_elem else None
            )
        return (
            team1_elem.get_text(strip=True) if team1_elem else None,
            team2_elem.get_text(strip=True) if team2_elem else None
        )

    @staticmethod
    def _convert_unix_to_date(unix_timestamp: str) -> Optional[str]:
        try:
            timestamp_seconds = int(unix_timestamp) // 1000
            return datetime.fromtimestamp(timestamp_seconds).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _convert_unix_to_time(unix_timestamp: str) -> Optional[str]:
        try:
            timestamp_seconds = int(unix_timestamp) // 1000
            return datetime.fromtimestamp(timestamp_seconds).strftime("%H:%M:%S")
        except (ValueError, TypeError):
            return None


class MatchDetailsParser:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def parse(self) -> MatchDetails:
        maps_data = self._parse_maps()
        players_stats = self._parse_players()
        match_link = self._parse_match_link()
        team_id = self._parse_team_id()

        return MatchDetails(
            match_link=match_link,
            maps=maps_data,
            players_stats=players_stats
        ) and Team(team_id=team_id)

    def _parse_maps(self) -> List[MapData]:
        maps_data = []
        try:
            for map_elem in self.soup.select('.mapholder'):
                map_name = map_elem.select_one('.mapname').text.strip()
                score_team1, score_team2, winner = self._parse_map_scores(map_elem)
                print([score_team1, score_team2, winner, map_name])

                if all([score_team1, score_team2, winner, map_name]):
                    maps_data.append(
                        MapData(
                            map_name=map_name,
                            score_team1=score_team1,
                            score_team2=score_team2,
                            winner=winner
                        )
                    )
        except Exception as e:
            print(f'Map parsing error: {e}')
        return maps_data

    def _parse_map_scores(self, map_elem) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        score_team1 = None
        score_team2 = None
        winner = None

        # Ищем левую команду
        left_team = map_elem.select_one('.results-left')
        # Ищем правую команду
        right_team = map_elem.select_one('.results-right')

        # Проверяем, какая команда победила
        if left_team and 'won' in left_team.get('class', []):
            winner = left_team.select_one('.results-teamname').text.strip()
            score_team1 = left_team.select_one('.results-team-score').text.strip()
            score_team2 = right_team.select_one('.results-team-score').text.strip()
        elif right_team and 'won' in right_team.get('class', []):
            winner = right_team.select_one('.results-teamname').text.strip()
            score_team1 = right_team.select_one('.results-team-score').text.strip()
            score_team2 = left_team.select_one('.results-team-score').text.strip()

        # Пропускаем несыгранные карты (где счёт "-")
        if score_team1 == '-' or score_team2 == '-':
            return None, None, None

        return score_team1, score_team2, winner

    def _parse_players(self) -> List[PlayerStats]:
        players_stats = []

        # Находим ТОЛЬКО блок с общей статистикой (All maps)
        all_maps_content = self.soup.select_one('#all-content')
        if not all_maps_content:
            raise ValueError("Could not find 'All maps' stats section")

        for row in all_maps_content.select('.totalstats:not(.hidden) tr:not(.header-row)'):
            try:
                player = self._parse_player_row(row)
                if player:
                    players_stats.append(player)
            except Exception as e:
                print(f"Player parsing error: {e}")
                continue

        return players_stats

    def _parse_player_row(self, row) -> PlayerStats:
        if 'hidden' in row.get('class', []):
            return None

        country = row.find('img', class_='flag')['title'].strip()
        nickname = row.select_one('.player-nick').text.strip()

        kd = row.select_one('.kd').text.strip()
        kills, deaths = map(int, kd.split('-'))

        adr = float(row.select_one('.adr').text.strip())
        kast = float(row.select_one('.kast').text.strip().replace('%', ''))
        rating = float(row.select_one('.rating').text.strip())
        team = self.soup.select_one('.teamName.team').text.strip()

        player_link = row.select_one('td.players a[href^="/player/"]')['href']
        hltv_id = re.search(r'/player/(\d+)/', player_link)
        print([nickname, country, kd, adr, kast, rating, team, player_link])

        return PlayerStats(
            nickname=nickname,
            country=country,
            kills=kills,
            deaths=deaths,
            adr=adr,
            kast=kast,
            rating=rating,
            team=team,
            hltv_id=hltv_id
        )

    def _parse_match_link(self) -> Optional[int]:
        match_link = self.soup.find('link', {'rel': 'canonical'})['href']
        match_id_match = re.search(r'/matches/(\d+)/', match_link)
        if match_id_match:
            return int(match_id_match.group(1))
        return None

    def _parse_team_id(self) -> Optional[int]:
        team_link = self.soup.select_one('.team a[href^="/team/"]')['href']
        team_id = team_link.split('/')[2]
        if team_id:
            return int(team_id)
        return None


class DataExtractor:
    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, 'html.parser')

    def get_score(self, match_element=None) -> Optional[MatchScore]:
        return ScoreParser(self.soup).parse(match_element)

    def get_match_details(self) -> MatchDetails:
        return MatchDetailsParser(self.soup).parse()
