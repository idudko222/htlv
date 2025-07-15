from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config import config
import os


class SeleniumDriver:
    def __init__(self):
        options = Options()
        options.add_argument("--disable-javascript")  # Основное отключение
        options.add_experimental_option(
            "prefs", {
                "profile.managed_default_content_settings.javascript": 2,  # Отключение JS
                "profile.managed_default_content_settings.images": 2,  # Опционально: отключение картинок
                "profile.default_content_setting_values.javascript": 2  # Дополнительное отключение
            }
            )
        options.headless = config.get("selenium.headless")
        options.add_argument(f"user-agent={config.get('selenium.user_agent')}")


        self.driver = webdriver.Chrome(
            options=options,
        )
        self.driver.implicitly_wait(config.get("selenium.implicitly_wait"))
        self.driver.set_page_load_timeout(config.get("selenium.page_load_timeout"))
