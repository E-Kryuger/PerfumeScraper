import os
import logging

import pandas as pd
from pandas import DataFrame

from src.base import BaseFileManager
from src.utils import OSUtils
from src.validators import GoldAppleDataValidator

logger = logging.getLogger('src.data_manager')


class CSVFileManager(BaseFileManager[DataFrame]):
    """ Менеджер для работы с CSV-файлами """

    def save_data(self, scraped_data: dict, filename: str = '') -> None:
        """ Сохранение данных в CSV-файле """
        data = GoldAppleDataValidator.validate(scraped_data)
        filename = OSUtils.generate_filename() if filename == '' else filename
        file_path = self._get_file_path(filename)
        df = pd.DataFrame(data)
        df.to_csv(file_path, encoding='utf-8')
        logger.info(f'✅ Данные сохранены в CSV-файл: {filename}')

    def load_data(self, filename: str) -> DataFrame:
        """ Выгрузка данных из CSV-файла """
        file_path = self._get_file_path(filename)
        logger.info(f'✅ Выполнена выгрузка данных из CSV-файла: {filename}')
        return pd.read_csv(file_path, index_col=0)

    def delete_data(self, filename: str = '') -> None:
        """ Удаление всех файлов или одного конкретного """
        if OSUtils.is_directory_empty(self._dir_path):
            logger.error(f"❌ Директория '{self._dir_path}' уже пуста")
            raise FileNotFoundError(f"Директория '{self._dir_path}' уже пуста")
        if filename and not OSUtils.is_there_file(filename, self._dir_path):
            logger.error(f"❌ Файл '{filename}' не найден в директории '{self._dir_path}'")
            raise FileNotFoundError(f"Файл '{filename}' не найден в директории '{self._dir_path}'")

        file_paths = [self._get_file_path(filename)] if filename else [file.path for file in os.scandir(self._dir_path)]
        for path in file_paths:
            os.remove(path)

    def _get_file_path(self, filename: str) -> str:
        """ Получение пути к файлу """
        logger.info(f'✅ Успешно получен путь к файлу {filename}')
        return os.path.join(self._dir_path, filename)
