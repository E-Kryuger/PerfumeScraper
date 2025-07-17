import os
from pathlib import Path
from typing import Callable
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from bs4 import BeautifulSoup, Tag

from src.config import LOG_DIR
from src.data_manager import CSVFileManager
from src.gui import GUI
from src.scraper import GoldAppleScraper
from src.utils import CSVUtils

TEST_SCRAPED_DATA = {
            'link': ['https://goldapple.ru/19000383938-confidence', 'https://goldapple.ru/26375300002-lost-cherry'],
            'name': ['HERE TO FEEL Confidence', 'TOM FORD Lost Cherry'],
            'price': ['1 832₽', '54 550₽'],
            'rating': ['4.9', '4.5'],
            'description': [
                'Аромат-напоминание о той  силе и уверенности, что кроется внутри каждого из нас ...',
                'Сладость. Соблазн.  Неутолимое желание. Lost Cherry — насыщенный аромат, ...',
            ],
            'how_to_use': [
                'Перед каждым использованием свечи, кроме первого зажигания, подрезайте фитиль до 5 мм ...',
                'нет информации',
            ],
            'country_of_origin': ['Россия', 'США'],
        }
DF = pd.DataFrame(TEST_SCRAPED_DATA)
FIXTURE_NAMES = (
    'parfjumerija.html',
    'product1.html',
    'product2.html',
)


@pytest.fixture(autouse=True)
def clean_empty_logs() -> None:
    """ Удаление пустых логов после выполнения тестов """
    yield  # выполнение теста
    if not os.path.exists(LOG_DIR):  # проверка наличия директории с логами
        return
    for item in os.scandir(LOG_DIR):
        if item.is_file() and os.path.getsize(item.path) == 0:
            os.remove(item.path)  # удаление пустого лог-файла


@pytest.fixture
def load_html_code() -> Callable[[str], str]:
    """ Фикстура для получения HTML-кода """
    def _load_html(filename: str) -> str:
        """ Загрузка HTML-кода страницы из файлов """
        file_path = Path('tests/fixtures') / filename
        return file_path.read_text(encoding='utf-8')
    return _load_html


@pytest.fixture
def temp_dir(tmp_path: Path) -> str:
    """ Фикстура для временной директории """
    return str(tmp_path)


@pytest.fixture
def gold_apple_scraper_instance() -> GoldAppleScraper:
    """ Фикстура, создающая экземпляр класса GoldAppleScraper """
    return GoldAppleScraper(page_number=1)


@pytest.fixture
def csv_manager_instance(temp_dir: Path) -> CSVFileManager:
    """ Фикстура, создающая экземпляр класса CSVFileManager """
    return CSVFileManager(str(temp_dir))


@pytest.fixture
def csv_utils_instance() -> CSVUtils:
    """ Фикстура, создающая экземпляр класса CSVUtils """
    return CSVUtils(DF)


@pytest.fixture
def scraped_data() -> dict[str, list[str]]:
    """ Фикстура, содержащая извлеченные данные """
    return TEST_SCRAPED_DATA


@pytest.fixture
def test_df() -> pd.DataFrame:
    """ Фикстура, содержащая DataFrame с извлеченными данными """
    return DF


@pytest.fixture
def fixture_names() -> tuple[str, str, str]:
    """ Фикстура, содержащая названия тестовых файлов с HTML-кодом страниц """
    return FIXTURE_NAMES


@pytest.fixture
def main_page_sp(load_html_code: Callable) -> BeautifulSoup:
    """ Фикстура, содержащая объект BeautifulSoup основной страницы с продуктами """
    html = load_html_code(FIXTURE_NAMES[0])
    return BeautifulSoup(html, 'lxml')


@pytest.fixture
def products_elements(main_page_sp: BeautifulSoup) -> list[Tag]:
    """ Фикстура, содержащая список элементов продуктов """
    return main_page_sp.find_all('article')


@pytest.fixture
def product_pages_sp(load_html_code: Callable) -> list[BeautifulSoup]:
    """ Фикстура, содержащая список объектов BeautifulSoup страниц продуктов """
    return [BeautifulSoup(load_html_code(filename), 'lxml') for filename in FIXTURE_NAMES[1:]]


@pytest.fixture
def mock_scraper() -> Mock:
    """ Фикстура, содержащая замоканный объект срапера """
    scraper = Mock()
    scraper.get_data.return_value = [
        {'link': 'https://example.com/1', 'name': 'Product 1', 'price': '1 000₽', 'rating': '4.5'},
        {'link': 'https://example.com/2', 'name': 'Product 2', 'price': '2 000₽', 'rating': '4.8'},
    ]
    return scraper


@pytest.fixture
def mock_file_manager() -> Mock:
    """ Фикстура, содержащая замоканный объект менеджера файлов """
    file_manager = Mock()
    file_manager.load_data.return_value = pd.DataFrame([
        {'link': 'https://example.com/3', 'name': 'Product 3', 'price': '3 000₽', 'rating': '4.2'},
    ])
    return file_manager


@pytest.fixture
def mock_os_utils() -> None:
    """Фикстура для мока методов OSUtils
    - `OSUtils.is_directory_empty` всегда возвращает `True`
    - `OSUtils.get_files` всегда возвращает пустой список
    """
    with patch('src.utils.OSUtils.is_directory_empty', return_value=True), \
         patch('src.utils.OSUtils.get_files', return_value=[]):
        yield


@pytest.fixture
def gui(gold_apple_scraper_instance: GoldAppleScraper, csv_manager_instance: CSVFileManager) -> GUI:
    """ Фикстура, содержащая экземпляр класса `GUI` """
    return GUI(gold_apple_scraper_instance, csv_manager_instance)
