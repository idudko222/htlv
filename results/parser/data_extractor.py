from bs4 import BeautifulSoup
import re
from datetime import datetime
from data_class import MatchScore, PlayerStats, MatchDetails, MapData
from typing import Optional, List, Dict, Tuple

class ScoreParser:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def parse(self, match_element=None) -> Optional[MatchScore]:
        try:
            score_element = match_element or self.soup.find('div', class_='result-con')
            if not score_element:
                return None

            team1_elem = score_element.find('div', class_='team1').find('div', class_='team')
            team2_elem = score_element.find('div', class_='team2').find('div', class_='team')
            score_won_elem = score_element.find('span', class_='score-won')
            score_lost_elem = score_element.find('span', class_='score-lost')

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

        return MatchDetails(
            match_link=match_link,
            maps=maps_data,
            players_stats=players_stats
        )

    def _parse_maps(self) -> List[MapData]:
        maps_data = []
        try:
            for map_elem in self.soup.select('.mapholder'):
                map_name = map_elem.select_one('.mapname').text.strip()
                score_team1, score_team2, winner = self._parse_map_scores(map_elem)

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

        for score_elem in map_elem.select('.score'):
            for team_score in score_elem.select('.won'):
                score_team1 = team_score.select_one('.results-team-score').text.strip()
                winner = team_score.select_one('.results-teamname').text.strip()
            if score_team1 and winner:
                for team_score in score_elem.select('.lost'):
                    score_team2 = team_score.select_one('.results-team-score').text.strip()
        return score_team1, score_team2, winner

    def _parse_players(self) -> List[PlayerStats]:
        players_stats = []
        for row in self.soup.select('.totalstats tr:not(.header-row)'):
            try:
                player = self._parse_player_row(row)
                players_stats.append(player)
            except Exception as e:
                print(f"Player parsing error: {e}")
                continue
        return players_stats

    def _parse_player_row(self, row) -> PlayerStats:
        nickname = row.select_one('.player-nick').text.strip()
        full_name_elem = row.select_one('.gtSmartphone-only .statsPlayerName') or \
                         row.select_one('.smartphone-only .statsPlayerName')
        full_name = full_name_elem.text.strip() if full_name_elem else None
        country = row.find('img', class_='flag')['title'].strip()

        kd = row.select_one('.kd').text.strip()
        kills, deaths = map(int, kd.split('-'))

        adr = float(row.select_one('.adr').text.strip())
        kast = float(row.select_one('.kast').text.strip().replace('%', ''))
        rating = float(row.select_one('.rating').text.strip())
        team = self.soup.select_one('.teamName.team').text.strip()

        player_link = row.select_one('.player-nick').find_parent('a')['href']
        hltv_id = int(re.search(r'/player/(\d+)/', player_link).group(1))

        return PlayerStats(
            nickname=nickname,
            full_name=full_name,
            country=country,
            kills=kills,
            deaths=deaths,
            adr=adr,
            kast=kast,
            rating=rating,
            team=team,
            hltv_id=hltv_id
        )

    def _parse_match_link(self) -> int:
        match_link = self.soup.find('link', {'rel': 'canonical'})['href']
        return int(re.search(r'match/(\d+)', match_link).group(1))


class DataExtractor:
    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, 'html.parser')

    def get_score(self, match_element=None) -> Optional[MatchScore]:
        return ScoreParser(self.soup).parse(match_element)

    def get_match_details(self) -> MatchDetails:
        return MatchDetailsParser(self.soup).parse()