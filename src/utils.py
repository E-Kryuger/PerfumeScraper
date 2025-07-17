from src.config import CSV_FILES_DIR
import datetime
import os

import pandas as pd
import requests


class ResponseChecker:
    """ Класс для проверки HTTP-статуса ответа """

    @staticmethod
    def check(response: requests.Response) -> None:
        """ Проверяет HTTP-статус ответа и выбрасывает исключение в случае ошибки """
        if response.status_code == 403:
            http_error_msg = '403 Forbidden – Access denied! Возможно, проблема связана с настройками VPN или сети'
            raise requests.HTTPError(http_error_msg)

        response.raise_for_status()


class OSUtils:
    """ Класс для работы с файлами и директориями """

    @staticmethod
    def generate_filename(main_name: str = 'scraped-product-details', file_extension: str = 'csv') -> str:
        """ Генерация имени файла, хранящего извлеченные данные """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f'{main_name}_{timestamp}.{file_extension}'

    @staticmethod
    def get_files(dir_path: str = CSV_FILES_DIR) -> list:
        """ Получение файлов из указанной директории """
        return [file for file in os.scandir(dir_path) if file.is_file()]

    @staticmethod
    def is_directory_empty(dir_path: str = CSV_FILES_DIR) -> bool:
        """ Проверка на наличие файлов в указанной директории """
        file = next(os.scandir(dir_path), None)
        return False if file else True

    @staticmethod
    def is_there_file(filename: str, dir_path: str) -> bool:
        """ Проверка существования указанного файла """
        return filename in [file.name for file in os.scandir(dir_path)]


class CSVUtils:
    def __init__(self, df: pd.DataFrame) -> None:
        """ Инициализация объекта """
        self.df = df
        self.top_n = None

    def get_headers_with_data(self, from_copy=False) -> tuple:
        """ Получение заголовков с данными """
        df = self.top_n if from_copy else self.df
        headers = df.columns.tolist()
        data = df.to_numpy().tolist()

        return headers, data

    def get_top_n_by_column(self, n: int, column: str) -> tuple:
        """ Получение заголовков с выборкой данных """
        df = self.df.copy()  # работа с копией DataFrame
        if column == 'price':
            column = 'price_int'  # создание столбца для сортировки, который будет содержать значения типа int
            df[column] = df['price'].replace(r'\D+', '', regex=True).astype(int)
        self.top_n = df.sort_values(by=column, ascending=False).head(n)
        if column == 'price_int':  # удаление столбца со значениями типа int
            self.top_n.drop(columns=[column], inplace=True)

        return self.get_headers_with_data(from_copy=True)
