from selenium.webdriver.support.ui import WebDriverWait
from results.parser.data_extractor import DataExtractor, MatchScore
from selenium.webdriver.common.by import By
from typing import Optional, List
from data_class import MatchDetails


class DataParser:
    def get_html(self, driver, url: str) -> Optional[str]:
        try:
            driver.get(url)
            WebDriverWait(driver, 5).until(
                lambda x: x.find_element(By.XPATH, "//h1 | //div[@data-marker='item-view/item']")
            )
            return driver.page_source
        except Exception as e:
            print(f'Ошибка загрузки страницы {url}: {e}')
            return None

    def parse(self, html: str, url: str) -> Optional[List[MatchScore]]:
        try:
            if not html:
                return None

            extractor = DataExtractor(html)
            matches_data = []

            for match_element in extractor.soup.select('.result-con')[:100]:
                match_data = extractor.get_score(match_element)
                if match_data:
                    matches_data.append(match_data)

            return matches_data if matches_data else None

        except Exception as e:
            print(f'Ошибка парсинга {url}: {e}')
            return None

    def parse_match_details(self, driver, match_url: str) -> Optional[MatchDetails]:
        try:
            html = self.get_html(driver, match_url)
            if not html:
                return None

            extractor = DataExtractor(html)
            return extractor.get_match_details()
        except Exception as e:
            print(f'Ошибка парсинга детальной страницы {match_url}: {e}')
            return None