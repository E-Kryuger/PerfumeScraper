import os

import pandas as pd
import pytest

from src.data_manager import CSVFileManager


def test_csv_file_manager_save_data(csv_manager_instance: CSVFileManager, scraped_data: dict[str, list[str]]) -> None:
    """ Тест сохранения данных в CSV-файл """
    filename = 'test.csv'
    csv_manager_instance.save_data(scraped_data, filename)
    file_path = os.path.join(csv_manager_instance._dir_path, filename)
    assert os.path.exists(file_path) is True


def test_csv_file_manager_load_data(csv_manager_instance: CSVFileManager, scraped_data: dict[str, list[str]],
                                    test_df: pd.DataFrame) -> None:
    """ Тест загрузки данных из файла """
    filename = 'test.csv'
    csv_manager_instance.save_data(scraped_data, filename)
    df = csv_manager_instance.load_data(filename)
    test_df = test_df.copy()
    test_df['rating'] = test_df['rating'].astype(float)
    pd.testing.assert_frame_equal(df, test_df)


def test_csv_file_manager_delete_single_file(csv_manager_instance: CSVFileManager,
                                             scraped_data: dict[str, list[str]]) -> None:
    """ Тест удаления конкретного файлов """
    filename = 'test.csv'
    file_path = os.path.join(csv_manager_instance._dir_path, filename)
    csv_manager_instance.save_data(scraped_data, filename)
    assert os.path.exists(file_path) is True
    csv_manager_instance.delete_data(filename)
    assert os.path.exists(file_path) is False


def test_csv_file_manager_delete_not_found_file(csv_manager_instance: CSVFileManager,
                                                scraped_data: dict[str, list[str]]) -> None:
    """ Тест удаления файла, который не удалось найти """
    filename = 'not-exists-file.csv'
    csv_manager_instance.save_data(scraped_data, 'test.csv')
    with pytest.raises(FileNotFoundError) as exc_info:
        csv_manager_instance.delete_data(filename)
    expected_msg = f"Файл '{filename}' не найден в директории '{csv_manager_instance._dir_path}'"
    assert str(exc_info.value) == expected_msg


def test_csv_file_manager_delete_all_files(csv_manager_instance: CSVFileManager,
                                           scraped_data: dict[str, list[str]]) -> None:
    """ Тест удаления всех файлов """
    filename = 'test.csv'
    file_path = os.path.join(csv_manager_instance._dir_path, filename)
    csv_manager_instance.save_data(scraped_data, filename)
    assert os.path.exists(file_path) is True
    csv_manager_instance.delete_data()
    assert os.listdir(csv_manager_instance._dir_path) == []


def test_csv_file_manager_delete_data_in_empty_dir(csv_manager_instance: CSVFileManager) -> None:
    """ Тест удаления данных в директории, которая уже пустая """
    with pytest.raises(FileNotFoundError) as exc_info:
        csv_manager_instance.delete_data()
    expected_msg = f"Директория '{csv_manager_instance._dir_path}' уже пуста"
    assert str(exc_info.value) == expected_msg
