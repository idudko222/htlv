import os
from typing import Dict, Any


class Config:
    """Singleton-класс для хранения всех настроек проекта."""

    _instance = None

    DEFAULT_SETTINGS = {
        # Настройки Selenium WebDriver
        "selenium": {
            "headless": False,  # Режим без графического интерфейса (True/False)
            "user_agent": "Mozilla/5.0...",  # Заголовок User-Agent для имитации браузера
            "page_load_timeout": 20,  # Макс. время загрузки страницы (сек)
            "implicitly_wait": 7,  # Неявное ожидание элементов (сек)
            "proxy": {
            "enabled": False,
            "proxies": [
                "socks5://oVxHPd:VDkX9P@45.11.126.101:9443",
                #"http://W7MAY4:3A0V4D@45.11.124.80:9525",
                #"http://AQGX5j:svsaBX@181.177.85.163:9454",
            ],
            "ssl_verify": False
            }
        },

        # Настройки парсинга
        "scraping": {
            "max_retries": 2,  # Кол-во попыток перезагрузки страницы при ошибке
            "delay_between_attempts": (0.5, 1.5),  # Случайная задержка между попытками (мин, макс)
        },

        # Пути к файлам
        "files": {
            "input_csv": "csv/in/properties_urls.csv",  # Файл с исходными ссылками
            "output_csv": "csv/out/test.csv",  # Файл для сохранения результатов
        },

        # Настройки эмуляции пользователя
        "emulation": {
            # Настройки прокрутки
            "scroll": {
                "pause_time_range": (0.1, 0.5),  # Задержка между прокрутками (сек)
                "count_range": (1, 3),  # Диапазон количества прокруток
                "scroll_back_chance": 0.3,  # Вероятность обратной прокрутки (30%)
                "scroll_back_pixels": 100,  # Пиксели для обратной прокрутки
                "scroll_back_delay": 0.2,  # Задержка после обратной прокрутки (сек)
            },
            # Настройки движения мыши
            "mouse": {
                "move_count_range": (0, 1),  # Диапазон количества движений
                "offset_range": (30, 150),  # Диапазон смещения курсора (пиксели)
                "pause_time_range": (0.1, 0.5),  # Задержка между движениями (сек)
                "click_chance": 0.2,  # Вероятность клика (30%)
                "click_delay_range": (0.1, 1),  # Задержка после клика (сек)
            },
            # Настройки задержек
            "delay": {
                "min": 0.5,  # Минимальная задержка (сек)
                "max": 1.5,  # Максимальная задержка (сек)
            }
        },
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.settings = cls.DEFAULT_SETTINGS.copy()
        return cls._instance

    def get(self, key: str, default=None) -> Any:
        """Получает значение настройки по ключу (например, 'selenium.headless')."""
        keys = key.split(".")
        value = self.settings
        for k in keys:
            value = value.get(k, {})
            if not value:
                return default
        return value or default

    def update(self, new_settings: Dict) -> None:
        """Обновляет настройки (сливает с текущими)."""
        self._merge_dicts(self.settings, new_settings)

    @staticmethod
    def _merge_dicts(original: Dict, new: Dict) -> None:
        """Рекурсивно обновляет словарь."""
        for key, value in new.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                Config._merge_dicts(original[key], value)
            else:
                original[key] = value


# Создаём глобальный экземпляр конфига
config = Config()
