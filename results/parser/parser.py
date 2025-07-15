from selenium.webdriver.support.ui import WebDriverWait
from results.parser.data_extractor import DataExtractor
from selenium.webdriver.common.by import By


class DataParser:
    def get_html(self, driver, url):
        try:
            driver.get(url)
            WebDriverWait(driver, 5).until(
                lambda x: x.find_element(By.XPATH, "//h1 | //div[@data-marker='item-view/item']")
            )
            return driver.page_source
        except Exception as e:
            print(f'Ошибка загрузки страницы {url}: {e}')

    def parse(self, html, url):
        try:
            if not html:
                return None

            extractor = DataExtractor(html)
            data = extractor.get_score() or {}

            if data:
                print('Успешно обработана')
            return data
        except Exception as e:
            print(f'Ошибка парсинга {url}: {e}')
            return None
