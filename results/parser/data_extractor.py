from attr.setters import convert
from bs4 import BeautifulSoup
import re
from datetime import datetime

class DataExtractor:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, 'html.parser')

    def get_score(self, match_element=None):
        try:
            score_element = match_element or self.soup.find('div', class_='result-con')

            if not score_element:
                return None

            team1_elem = score_element.find('div', class_='team1').find('div', class_='team')
            team2_elem = score_element.find('div', class_='team2').find('div', class_='team')
            score_won_elem = score_element.find('span', class_='score-won')
            score_lost_elem = score_element.find('span', class_='score-lost')

            unix_timestamp = score_element.get('data-zonedgrouping-entry-unix')
            if unix_timestamp:
                formatted_date = self.convert_unix_to_date(unix_timestamp)
                time = self.convert_unix_to_time(unix_timestamp)
            else:
                formatted_date = None
                time = None

            # Определяем победителя по классу team-won
            if team2_elem and 'team-won' in team2_elem.get('class', []):
                winner = team2_elem.get_text(strip=True)
                loser = team1_elem.get_text(strip=True) if team1_elem else None
            else:
                winner = team1_elem.get_text(strip=True) if team1_elem else None
                loser = team2_elem.get_text(strip=True) if team2_elem else None

            if all([score_won_elem, score_lost_elem, winner, loser]):
                return {
                    'team_won': winner,
                    'team_lost': loser,
                    'score_won': score_won_elem.get_text(strip=True),
                    'score_lost': score_lost_elem.get_text(strip=True),
                    'date': formatted_date,
                    'time': time,
                }
            return None

        except Exception as e:
            print(f'Ошибка парсинга: {e}')
            return None

    def get_match_details(self):
        """Парсинг детальной страницы матча"""
        score_team1 = None
        score_team2 = None
        winner = None
        map_name = None
        maps_data = []
        match_link = int(re.search(r'match/(\d+)', self.soup.find('link', {'rel': 'canonical'})['href']).group(1))

        try:
            for map_elem in self.soup.select('.mapholder'):
                map_name = map_elem.select_one('.mapname').text.strip()
                for score_elem in map_elem.select('.score'):
                    for team_score in score_elem.select('.won'):
                        score_team1 = team_score.select_one('.results-team-score').text.strip()
                        winner = team_score.select_one('.results-teamname').text.strip()
                    if score_team1 and winner:
                        for team_score in score_elem.select('.lost'):
                            score_team2 = team_score.select_one('.results-team-score').text.strip()

            if score_team1 and score_team2 and winner and map_name:
                maps_data.append({
                    'map_name': map_name,
                    'score_team1': score_team1,
                    'score_team2': score_team2,
                    'winner': winner,
                })

        except Exception as e:
            print(f'Ошибка при сборе данных о картах: {e}')

        players_stats = []

        for row in self.soup.select('.totalstats tr:not(.header-row)'):
            try:
                nickname = row.select_one('.player-nick').text.strip()
                full_name_elem = row.select_one('.gtSmartphone-only .statsPlayerName') or row.select_one(
                    '.smartphone-only .statsPlayerName'
                    )
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


                player_data = {
                    'full_name': full_name,
                    'country': country,
                    'kills': kills,
                    'deaths': deaths,
                    'adr': adr,
                    'kast': kast,
                    'rating': rating,
                    'team': team,
                    'hltv_id': hltv_id,
                }

                players_stats.append((nickname,player_data))

            except Exception as e:
                print(f"Ошибка при парсинге данных игрока: {e}")
                continue

        return {
            'match_link': match_link,
            'maps': maps_data,
            'players_stats': players_stats
        }

    @classmethod
    def convert_unix_to_date(cls, unix_timestamp):
        try:
            timestamp_seconds = int(unix_timestamp) // 1000
            date_obj = datetime.fromtimestamp(timestamp_seconds)
            return date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    @classmethod
    def convert_unix_to_time(cls, unix_timestamp):
        try:
            timestamp_seconds = int(unix_timestamp) // 1000
            time_obj = datetime.fromtimestamp(timestamp_seconds)
            return time_obj.strftime("%H:%M:%S")
        except (ValueError, TypeError):
            return None
