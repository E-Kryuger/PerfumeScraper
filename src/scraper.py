import logging
import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from src.base import BaseScraper
from src.config import GOLD_APPLE_PERFUMERY_URL, LOG_DIR
from src.utils import OSUtils
from src.utils import ResponseChecker
from src.validators import PageNumberValidator

# Настройка логирования
filename = OSUtils.generate_filename('scraping-process', 'log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_path = os.path.join(LOG_DIR, filename)
file_handler = logging.FileHandler(file_path, encoding='utf-8')
file_formater = logging.Formatter('%(asctime)s – %(name)s – %(levelname)s: %(message)s')
file_handler.setFormatter(file_formater)
logger.addHandler(file_handler)


class GoldAppleScraper(BaseScraper):
    """ Класс для сбора данных о парфюмерии с сайта Gold Apple """

    def __init__(self, url: str = GOLD_APPLE_PERFUMERY_URL, page_number: int = 3) -> None:
        """ Инициализация экземпляра класса """
        super().__init__(url)
        self._page_number = PageNumberValidator.validate(page_number)

    def _get_webdriver(self) -> WebDriver:
        """ Создание и настройка веб-драйвера для работы с динамической страницей """
        # Настройки запуска Selenium
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")  # фоновый режим без окна браузера
        # Отключение автоматического добавления флага navigator.webdriver = true,
        # который указывает сайтам, что браузер запущен через Selenium
        options.add_argument("--disable-blink-features=AutomationControlled")

        return webdriver.Chrome(options=options)

    def _get_data_structure(self) -> dict:
        """ Структура собираемых данных """
        return {
            'link': [],
            'name': [],
            'price': [],
            'rating': [],
            'description': [],
            'how_to_use': [],
            'country_of_origin': [],
        }

    @staticmethod
    def _extract_articles(soup: BeautifulSoup) -> list[Tag]:
        """ Парсинг карточек с продуктами """
        return soup.find_all('article')

    @staticmethod
    def _extract_product_path(article: Tag) -> str:
        """ Парсинг URL пути на продукт """
        return article.find('a').get('href')

    @staticmethod
    def _extract_name(soup: BeautifulSoup) -> str:
        """ Парсинг названия продукта """
        description_div = soup.find('div', {'value': 'Description_0', 'text': re.compile('Описание', re.IGNORECASE)})
        name = description_div.next_element.next_element.get_text(strip=True)
        return name

    @staticmethod
    def _extract_price(soup: BeautifulSoup) -> str:
        """ Парсинг цены продукта """
        offers_div = soup.find('div', itemprop='offers')
        price = re.search(r'\d[\d\s]*₽', offers_div.get_text(strip=True)).group() if offers_div else 'нет информации'
        return price

    @staticmethod
    def _extract_rating(soup: BeautifulSoup) -> str:
        """ Парсинг рейтинга продукта """
        rating = soup.find('meta', itemprop='ratingValue').get('content')
        return rating

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> str:
        """ Парсинг описания продукта """
        description = soup.find('div', itemprop='description')
        description = re.sub(r'\n|\s{2,}', ' ', description.get_text(strip=True)) if description else 'нет информации'
        return description

    @staticmethod
    def _extract_how_to_use(soup: BeautifulSoup) -> str:
        """ Парсинг инструкции по применению продукта """
        how_to_use_div = soup.find('div', {'value': 'Text_1', 'text': re.compile('применение', re.IGNORECASE)})
        how_to_use = re.sub(r'\n', ' ', how_to_use_div.get_text(strip=True)) if how_to_use_div else 'нет информации'
        return how_to_use

    @staticmethod
    def _extract_country_of_origin(soup: BeautifulSoup) -> str:
        """ Парсинг страны-производителя продукта """
        text_pattern = re.compile('дополнительная информация', re.IGNORECASE)
        additionally_div = None
        for tab_number in range(2, 6):
            additionally_div = soup.find('div', {'value': f'Text_{tab_number}', 'text': text_pattern})
            if additionally_div:
                break

        if additionally_div:
            additional_info = str(additionally_div.find_next('div'))
            country_of_origin = re.findall(r'(?<=страна происхождения<br/>)([А-Яа-я]+)(?=<br)', additional_info)
            country_of_origin = country_of_origin[0] if country_of_origin else 'нет информации'
        else:
            country_of_origin = 'нет информации'
        return country_of_origin

    @property
    def page_number(self) -> int:
        """ Геттер количества страниц для скрапинга """
        return self._page_number

    @page_number.setter
    def page_number(self, value: int) -> None:
        """ Сеттер количества страниц для скрапинга """
        self._page_number = PageNumberValidator.validate(value)

    def _scrape_data(self) -> None:
        """ Извлечение и сохранение данных """
        logger.info(f'➤➤➤ Начало скрапинга: {self._url} '
                    f'| Будет обработано страниц: {self._page_number}')
        start_scraping_time = time.time()
        ResponseChecker.check(requests.get(self._url))  # проверка HTTP-статуса ответа
        main_page_html = self._get_main_page_source()
        end_time_getting_html = time.time()
        msg = (f'✅ html страницы получен: {self._url} '
               f'| Время: {round((end_time_getting_html - start_scraping_time) / 60, 2)} мин.')
        logger.info(msg)

        soup = BeautifulSoup(main_page_html, 'lxml')
        articles = self._extract_articles(soup)
        for article in articles:
            # Получение URL продукта
            gold_apple_url = re.search(r'[a-z/:.]+(?=/parfjumerija)', self._url).group()
            product_path = self._extract_product_path(article)
            product_url = urljoin(gold_apple_url, product_path)
            # Начало скрапинга данных продукта
            st = time.time()  # время начала
            product_html = self._get_product_page_source(product_url)
            sp = BeautifulSoup(product_html, 'lxml')
            try:  # извлечение данных
                name = self._extract_name(sp)
                price = self._extract_price(sp)
                rating = self._extract_rating(sp)
                description = self._extract_description(sp)
                how_to_use = self._extract_how_to_use(sp)
                country_of_origin = self._extract_country_of_origin(sp)
            except AttributeError as exc_info:
                msg = f'❌ Ошибка: {product_url} | Исключение: {exc_info}'
                logger.warning(msg)
                continue
            else:  # сохранение данных
                self._data['link'].append(product_url)
                self._data['name'].append(name)
                self._data['price'].append(price)
                self._data['rating'].append(rating)
                self._data['description'].append(description)
                self._data['how_to_use'].append(how_to_use)
                self._data['country_of_origin'].append(country_of_origin)
                et = time.time()  # время завершения скрапинга данных продукта
                pt = round(et - st, 2)  # время процесса получения данных продукта
                logger.info(f'✅ Успешно: {product_url} | Время: {pt} сек.')
        end_scraping_time = time.time()
        processing_time = round((end_scraping_time - start_scraping_time) / 60, 2)
        scraped_items = len(self._data['link'])
        logger.info(f'🏁🏁🏁 Скрапинг завершён: {self._url} '
                    f'| Спарсено товаров: {scraped_items} | Время: {processing_time} мин.')

    def _get_main_page_source(self) -> str:
        """ Получение HTML-кода основной страницы с продуктами """
        self._webdriver.get(f'{self._url}?p=1')
        self._scrolldown_main_page()
        return self._webdriver.page_source

    def _get_product_page_source(self, product_url) -> str:
        """ Получение HTML-кода страницы продукта """
        self._webdriver.get(product_url)
        self._scroll_page_to_bottom()
        return self._webdriver.page_source

    def _scrolldown_main_page(self) -> None:
        """ Прокрутка страницы с карточками товаров """
        scrape_pages_list = [str(page) for page in range(1, self._page_number + 1)]
        scroll_step = 300  # количество пикселей для прокрутки за раз
        scroll_pause = 0.7  # задержка между прокруткой
        # i = 0
        while True:
            self._webdriver.execute_script(f'window.scrollBy(0, {scroll_step});')
            time.sleep(scroll_pause)

            current_url = self._webdriver.current_url
            if not current_url:
                break

            match = re.search(r'(?<=p=)\d+', current_url)
            if not match:
                continue  # пропуск получения номера страницы у URL без параметра p

            current_page = match.group()
            if current_page not in scrape_pages_list:
                break

    def _scroll_page_to_bottom(self) -> None:
        """ Прокрутка страницы до самого низа с ожиданием загрузки нового контента """
        wait = WebDriverWait(self._webdriver, 5)  # время ожидания
        last_height = self._webdriver.execute_script('return document.body.scrollHeight')

        while True:
            self._webdriver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            try:
                wait.until(lambda driver: driver.execute_script("return document.body.scrollHeight") > last_height)
            except TimeoutException:
                break
            new_height = self._webdriver.execute_script("return document.body.scrollHeight")  # следующая высота
            if new_height == last_height:
                break

            last_height = new_height
