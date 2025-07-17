import re
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup, Tag

from src.config import GOLD_APPLE_PERFUMERY_URL
from src.scraper import GoldAppleScraper


def test_gold_apple_scraper_init(gold_apple_scraper_instance: GoldAppleScraper) -> None:
    """ Тест инициализации объекта класса `GoldAppleScraper` """
    expected_url = 'https://goldapple.ru/parfjumerija'
    expected_page_number = 1
    expected_data = {'link': [], 'name': [], 'price': [], 'rating': [],
                     'description': [], 'how_to_use': [], 'country_of_origin': []}
    assert gold_apple_scraper_instance._url == expected_url
    assert gold_apple_scraper_instance._page_number == expected_page_number
    assert gold_apple_scraper_instance._data == expected_data


def test_gold_apple_scraper_get_page_number(gold_apple_scraper_instance: GoldAppleScraper) -> None:
    """ Тест получения числа количества страниц для скрапинга """
    expected_page_number = 1
    assert gold_apple_scraper_instance.page_number == expected_page_number


def test_gold_apple_scraper_set_page_number(gold_apple_scraper_instance: GoldAppleScraper) -> None:
    """ Тест установки числа количества страниц для скрапинга """
    set_page_number = 9
    gold_apple_scraper_instance.page_number = set_page_number
    assert gold_apple_scraper_instance.page_number == set_page_number


def test_gold_apple_scraper_get_data(gold_apple_scraper_instance: GoldAppleScraper,
                                     scraped_data: dict[str, list[str]]) -> None:
    """ Тест получения извлеченной информации """
    gold_apple_scraper_instance._data = scraped_data
    assert gold_apple_scraper_instance.get_data() == scraped_data


def test_gold_apple_scraper_extract_articles(gold_apple_scraper_instance: GoldAppleScraper,
                                             main_page_sp: BeautifulSoup) -> None:
    """ Тест нахождения карточек с товарами на главной странице """
    expected = main_page_sp.find_all('article')
    result = gold_apple_scraper_instance._extract_articles(main_page_sp)
    assert result == expected


def test_gold_apple_scraper_extract_product_path(gold_apple_scraper_instance: GoldAppleScraper,
                                                 products_elements: list[Tag],
                                                 scraped_data: dict[str, list[str]]) -> None:
    """ Тест получения пути к продукту  """
    for i, product_elements in enumerate(products_elements):
        product_url = scraped_data['link'][i]
        expected = re.search(r'(?<=\.ru)/[-\w]+', product_url).group()
        result = gold_apple_scraper_instance._extract_product_path(product_elements)
        assert result == expected


def test_gold_apple_scraper_extract_name(gold_apple_scraper_instance: GoldAppleScraper,
                                         product_pages_sp: list[BeautifulSoup],
                                         scraped_data: dict[str, list[str]]) -> None:
    """ Тест получения названия продукта """
    for i, product_name in enumerate(scraped_data['name']):
        expected = product_name
        result = gold_apple_scraper_instance._extract_name(product_pages_sp[i])
        assert result == expected


def test_gold_apple_scraper_extract_price(gold_apple_scraper_instance: GoldAppleScraper,
                                          product_pages_sp: list[BeautifulSoup],
                                          scraped_data: dict[str, list[str]]) -> None:
    """ Тест получения цены продукта """
    for i, product_price in enumerate(scraped_data['price']):
        expected = product_price
        result = gold_apple_scraper_instance._extract_price(product_pages_sp[i])
        assert result == expected


def test_gold_apple_scraper_extract_rating(gold_apple_scraper_instance: GoldAppleScraper,
                                           product_pages_sp: list[BeautifulSoup],
                                           scraped_data: dict[str, list[str]]) -> None:
    """ Тест получения рейтинга продукта """
    for i, product_rating in enumerate(scraped_data['rating']):
        expected = product_rating
        result = gold_apple_scraper_instance._extract_rating(product_pages_sp[i])
        assert result == expected


def test_gold_apple_scraper_extract_description(gold_apple_scraper_instance: GoldAppleScraper,
                                                product_pages_sp: list[BeautifulSoup],
                                                scraped_data: dict[str, list[str]]) -> None:
    """ Тест получения описания продукта """
    for i, product_description in enumerate(scraped_data['description']):
        expected = product_description
        result = gold_apple_scraper_instance._extract_description(product_pages_sp[i])
        assert result == expected


def test_gold_apple_scraper_extract_how_to_use(gold_apple_scraper_instance: GoldAppleScraper,
                                               product_pages_sp: list[BeautifulSoup],
                                               scraped_data: dict[str, list[str]]) -> None:
    """ Тест получения инструкции по применению продукта """
    for i, how_to_use_product in enumerate(scraped_data['how_to_use']):
        expected = how_to_use_product
        result = gold_apple_scraper_instance._extract_how_to_use(product_pages_sp[i])
        assert result == expected


def test_gold_apple_scraper_extract_country_of_origin(gold_apple_scraper_instance: GoldAppleScraper,
                                                      product_pages_sp: list[BeautifulSoup],
                                                      scraped_data: dict[str, list[str]]) -> None:
    """ Тест получения страны-производителя продукта """
    for i, country_of_origin_product in enumerate(scraped_data['country_of_origin']):
        expected = country_of_origin_product
        result = gold_apple_scraper_instance._extract_country_of_origin(product_pages_sp[i])
        assert result == expected


def test_get_main_page_source(gold_apple_scraper_instance: GoldAppleScraper) -> None:
    """ Тест получения HTML главной страницы """
    mock_webdriver = Mock()
    expected_source = '<html>test_page_source</html>'
    mock_webdriver.page_source = expected_source
    gold_apple_scraper_instance._webdriver = mock_webdriver
    with patch.object(gold_apple_scraper_instance, '_scrolldown_main_page') as mock_scroll:
        result = gold_apple_scraper_instance._get_main_page_source()
        mock_webdriver.get.assert_called_once_with(f'{GOLD_APPLE_PERFUMERY_URL}?p=1')
        mock_scroll.assert_called_once()
        assert result == expected_source


def test_get_product_page_source(gold_apple_scraper_instance: GoldAppleScraper) -> None:
    """ Тест получения HTML страницы продукта """
    mock_webdriver = Mock()
    expected_source = "<html>product_page</html>"
    mock_webdriver.page_source = expected_source
    test_url = f"{GOLD_APPLE_PERFUMERY_URL}/product-123"
    gold_apple_scraper_instance._webdriver = mock_webdriver
    with patch.object(gold_apple_scraper_instance, '_scroll_page_to_bottom') as mock_scroll:
        result = gold_apple_scraper_instance._get_product_page_source(test_url)
        mock_webdriver.get.assert_called_once_with(test_url)
        mock_scroll.assert_called_once()
        assert result == expected_source
