from attr.setters import convert
from bs4 import BeautifulSoup
import re
from datetime import datetime

class DataExtractor:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, 'html.parser')

    def get_score(self):
        try:
            score_element = self.soup.find('div', class_='result-con')

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
