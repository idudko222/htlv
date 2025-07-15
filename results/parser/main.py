from results.parser.parser import DataParser
from selenium_driver import SeleniumDriver
from config import config
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hltv.settings')
django.setup()

from results.models import Match

BASE_URL = 'https://www.hltv.org/results'


def parse_match_results():
    base_url = BASE_URL
    selenium_driver = SeleniumDriver()
    driver = selenium_driver.driver
    try:
        data_parser = DataParser()
        max_matches = 50000  # Максимальное количество матчей для парсинга
        matches_per_page = 100  # Количество матчей на странице

        for page in range(0, max_matches, matches_per_page):
            current_url = f"{base_url}?offset={page}"
            html = data_parser.get_html(driver, current_url)
            if html:
                parsed_data = data_parser.parse(html, base_url)

                if parsed_data:
                    for match_data in parsed_data:
                        try:
                            Match.objects.create(
                                team_won=match_data['team_won'],
                                team_lost=match_data['team_lost'],
                                score_lost=match_data['score_lost'],
                                score_won=match_data['score_won'],
                                date=match_data['date'],
                                time=match_data['time'],
                            )
                            print(
                                f"Сохранен матч: {match_data['team_won']} {match_data['score_won']}:"
                                f"{match_data['score_lost']} {match_data['team_lost']}"
                            )
                        except Exception as e:
                            print(f'Ошибка сохранения: {e}')

    except Exception as e:
        print(f'Ошибка в парсинге: {e}')

    finally:
        driver.quit()


if __name__ == '__main__':
    parse_match_results()
