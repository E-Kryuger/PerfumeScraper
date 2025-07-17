import logging

import pandas as pd
import requests
from tabulate import tabulate

from src.config import MENU_WIDTH
from src.utils import CSVUtils, OSUtils
from src.scraper import GoldAppleScraper
from src.data_manager import CSVFileManager

logger = logging.getLogger('src.gui')


class GUI:
    """ Класс для взаимодействия с пользователем через консольное меню """

    def __init__(self, scraper: GoldAppleScraper, file_manager: CSVFileManager) -> None:
        """ Инициализация экземпляра класса """
        self._bottom_border = '-' * MENU_WIDTH
        self._table_format = 'fancy_grid'
        self._scraper = scraper
        self._file_manager = file_manager
        self._csv_utils = None
        self._user_choice = None
        self._df = None

    def start(self) -> None:
        """ Точка входа """
        self._user_choice = '1'
        if not OSUtils.is_directory_empty():
            self._start_menu()  # запуск стартового меню, если скрапинг уже проводился

        if self._user_choice == '1':  # запуск процесса извлечения данных из веб-страницы
            print('Извлечение данных из веб-страницы запущено..')
            try:
                self._run_scraping()
            except requests.HTTPError as e:
                logger.error(f'❌ Ошибка при скрапинге: {e}')
                print(f'Ошибка при скрапинге: {e}')
                return
        else:  # выбор данных из уже имеющихся
            self._df = self._get_data_by_date()
        # Инициализация экземпляра класса с CSV утилитами для вывода данных
        self._csv_utils = CSVUtils(df=self._df)

        while True:
            self._main_menu()  # запуск меню для просмотра результата
            if self._user_choice == '5':
                return

    def _run_scraping(self) -> None:
        """ Запуск скрапинга и сохранение данных """
        self._scraper.scrape()
        scraped_data = self._scraper.get_data()

        self._file_manager.save_data(scraped_data)
        self._df = pd.DataFrame(scraped_data)

    def _get_data_by_date(self) -> pd.DataFrame:
        """ Получение DataFrame из предыдущего извлечения данных """
        file_names = {}
        files = OSUtils.get_files()
        files_count = len(files)

        print('\n' + f"{' Доступны данные за следующие даты ':-^{MENU_WIDTH}}")
        for num, file in enumerate(files):
            file_names.update({str(num + 1): file.name})
            print(f'{num + 1}. {file.name}')
        print('-' * MENU_WIDTH)
        user_choice = self._get_user_choice(files_count)

        file_path = file_names[user_choice]
        df = self._file_manager.load_data(file_path)
        if self._csv_utils is not None:
            self._csv_utils.df = df

        return df

    def _start_menu(self) -> None:
        """ Отображение стартового меню с сохранением выбора пользователя """
        self._display_menu(' Стартовое меню ', [
            '1. Начать новый скрапинг и сохранить результат в SCV-файл',
            '2. Показать предыдущие результаты',
        ])

    def _main_menu(self) -> None:
        """ Отображение основного меню с сохранением выбора пользователя """
        records_count = self._df.shape[0] if self._df is not None else 0
        print(f'\nВсего записей: {records_count}')

        self._display_menu(' Основное меню ', [
            '1. Показать результат в консоли',
            '2. Показать топ-N товаров по цене',
            '3. Показать топ-N товаров по рейтингу',
            '4. Вернуться к выбору файлов по дате',
            '5. Выйти',
        ])

        self._handle_main_menu_choice()

    def _handle_main_menu_choice(self) -> None:
        """ Обработка выбора пользователя """
        if self._user_choice in {str(d) for d in range(1, 4)}:
            self._display_result()
        elif self._user_choice == '4':
            self._df = self._get_data_by_date()

    def _display_menu(self, title: str, options: list) -> None:
        """ Вспомогательная функция для отображения меню """
        print(f'{title:=^{MENU_WIDTH}}')
        print(*options, sep='\n')
        print('=' * MENU_WIDTH)
        self._user_choice = self._get_user_choice(options_count=len(options))

    def _display_result(self) -> None:
        """ Выбор способа отображения результата """
        if self._user_choice == '1':
            print('\n' + f"{' Результат ':-^{MENU_WIDTH}}")
            try:
                self._print_table(*self._csv_utils.get_headers_with_data())
            except IndexError:
                print('Данные отсутствуют')
            self._finish_program()
        elif self._user_choice in {'2', '3'}:
            try:
                n = int(input('Сколько записей хотите увидеть? '))
                if self._user_choice == '2':
                    column = 'price'
                    by_what = 'цене'
                else:
                    column = 'rating'
                    by_what = 'рейтингу'
                title = f' Топ-{n} по {by_what} '
                print('\n' + f'{title:-^{MENU_WIDTH}}')
                self._print_table(*self._csv_utils.get_top_n_by_column(n, column))
            except (ValueError, KeyError):
                print('Некорректный ввод или данные отсутствуют')
            self._finish_program()

    def _print_table(self, headers: list, tabular_data: list) -> None:
        """ Вывод данных в виде таблицы в консоль """
        print(tabulate(tabular_data, headers, self._table_format, maxcolwidths=30))

    @staticmethod
    def _get_user_choice(options_count: int) -> str:
        """ Вспомогательная функция для получения корректного ввода выбора от пользователя """
        input_message = f'Выберите пункт меню (1-{options_count}): '

        options = [str(d + 1) for d in range(options_count)]

        while True:
            user_choice = input(input_message).strip().replace('.', '')
            if user_choice in options:
                return user_choice

    @staticmethod
    def _finish_program() -> None:
        """ Завершение программы """
        print('\n')
        exit(0)
