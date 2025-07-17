from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from selenium.webdriver.chrome.webdriver import WebDriver

from src.config import CSV_FILES_DIR

T = TypeVar('T')  # определение дженерик-типа, который будет определять тип данных при чтении файла


class BaseScraper(ABC):
    """ Базовый класс для веб-скрапинга """

    def __init__(self, url: str) -> None:
        """ Инициализация объекта """
        self._url = url
        self._data = self._get_data_structure()
        self._webdriver = self._get_webdriver()

    @abstractmethod
    def _get_webdriver(self) -> WebDriver:
        """ Абстрактный класс для получения настроенного веб драйвера """
        pass

    @abstractmethod
    def _get_data_structure(self) -> dict:
        """ Абстрактный метод для задания структуры собираемых данных """
        pass


    @abstractmethod
    def _scrape_data(self) -> None:
        """ Абстрактный метод для извлечения данных со страницы """
        pass

    def scrape(self) -> None:
        """ Запуск процесса сбора данных с очисткой предыдущего результата """
        self._data = self._get_data_structure()
        self._scrape_data()

    def get_data(self) -> dict:
        """ Получение данных в виде словаря """
        return self._data


class BaseFileManager(ABC, Generic[T]):
    """ Базовый класс для работы с данными """

    def __init__(self, dir_path: str = CSV_FILES_DIR) -> None:
        """ Инициализация объекта """
        self._dir_path = dir_path

    @abstractmethod
    def save_data(self, scraped_data: dict, filename: str = '') -> None:
        """ Абстрактный метод для записи данных в файл """
        pass

    @abstractmethod
    def load_data(self, filename: str) -> T:
        """ Абстрактный класс для выгрузки данных из файла """
        pass

    @abstractmethod
    def delete_data(self, filename: str = '') -> None:
        """ Абстрактный класс для удаления данных """
        pass


class BaseValidator(ABC, Generic[T]):
    """ Базовый класс для валидации """

    @staticmethod
    @abstractmethod
    def validate(value: T) -> T:
        """ Абстрактно-статический метод для валидации значения """
        pass
