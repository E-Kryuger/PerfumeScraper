import datetime
from unittest.mock import patch, Mock

import pandas as pd
import pytest
import requests

from src.utils import OSUtils, ResponseChecker, CSVUtils


def test_os_utils_generate_filename() -> None:
    """ Тест генерации имени файла """
    const_datetime = datetime.datetime(2025, 3, 29, 12, 0, 0)
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = const_datetime
        res = OSUtils.generate_filename()
        expected_res = 'scraped-product-details_2025-03-29_12-00-00.csv'
        assert res == expected_res


@patch('os.scandir')
def test_os_utils_get_files(mock_scandir: Mock) -> None:
    """ Тест получения файлов из указанной директории """
    mock_file = Mock()
    mock_file.is_file.return_value = True
    mock_dir = Mock()
    mock_dir.is_file.return_value = False
    mock_scandir.return_value = [mock_file, mock_dir]
    res = OSUtils.get_files('scanned_dir')
    assert res == [mock_file]


def test_os_utils_is_directory_empty_when_is_empty() -> None:
    """ Тест проверки наличия файлов в директории, когда она пустая """
    with patch('os.scandir', return_value=iter([])):
        assert OSUtils.is_directory_empty('scanned_dir') is True


def test_os_utils_is_directory_empty_when_is_not_empty() -> None:
    """ Тест проверки наличия файлов в директории, когда она не является пустой """
    mock_file = Mock()
    with patch('os.scandir', return_value=iter([mock_file])):
        assert OSUtils.is_directory_empty('scanned_dir') is False


def test_os_utils_is_there_file_exists() -> None:
    """ Тест проверки существования файла в указанной директории """
    mock_file = Mock()
    mock_file.name = 'file.csv'
    with patch('os.scandir', return_value=[mock_file]):
        assert OSUtils.is_there_file('file.csv', 'scanned_dir') is True


def test_os_utils_is_there_file_not_exists() -> None:
    """ Тест проверки существования файла в указанной директории """
    mock_file = Mock()
    mock_file.name = 'file.csv'
    with patch('os.scandir', return_value=[mock_file]):
        assert OSUtils.is_there_file('other_file.csv', 'scanned_dir') is False


# ==== Тесты для ResponseChecker ====

def test_response_checker_raises_http_error() -> None:
    """ Тест выбрасывания HTTPError при 403 статусе и проверки сообщения """
    mock_response = Mock(spec=requests.Response)
    mock_response.status_code = 403
    with pytest.raises(requests.HTTPError) as exc_info:
        ResponseChecker.check(mock_response)
    expected_msg = '403 Forbidden – Access denied! Возможно, проблема связана с настройками VPN или сети'
    assert str(exc_info.value) == expected_msg


def test_response_checker_calls_raise_for_status() -> None:
    """ Тест успешного вызова `response.raise_for_status()` """
    mock_response = Mock(spec=requests.Response)
    mock_response.status_code = 200
    ResponseChecker.check(mock_response)
    mock_response.raise_for_status.assert_called_once()


# === Тесты для CSVUtils ===

def test_csv_utils_init(csv_utils_instance: CSVUtils, test_df: pd.DataFrame) -> None:
    """ Тест инициализации объекта класса `CSVUtils` """
    instance = csv_utils_instance
    pd.testing.assert_frame_equal(instance.df, test_df)
    assert instance.top_n is None


def test_get_headers_with_data(csv_utils_instance: CSVUtils, test_df: pd.DataFrame) -> None:
    """ Тест получения данных и заголовков данных в виде картежа списков """
    expected_headers = test_df.columns.tolist()
    expected_data = test_df.to_numpy().tolist()
    headers, data = csv_utils_instance.get_headers_with_data()
    assert headers == expected_headers
    assert data == expected_data


def test_get_top_n_by_price(csv_utils_instance: CSVUtils, test_df: pd.DataFrame) -> None:
    """ Тест получения заголовков с выборкой по цене """
    column, n = 'price', 1
    expected_df = test_df.copy()
    expected_df['price_int'] = expected_df[column].replace(r'\D+', '', regex=True).astype(int)
    expected_df = expected_df.sort_values(by='price_int', ascending=False).head(n)
    expected_df.drop(columns=['price_int'], inplace=True)
    expected_headers = expected_df.columns.tolist()
    expected_data = expected_df.to_numpy().tolist()
    headers, data = csv_utils_instance.get_top_n_by_column(n, column)
    assert headers == expected_headers
    assert data == expected_data


def test_get_top_n_by_rating(csv_utils_instance: CSVUtils, test_df: pd.DataFrame) -> None:
    """ Тест получения заголовков с выборкой по рейтингу """
    column, n = 'rating', 1
    expected_df = test_df.copy()
    expected_df = expected_df.sort_values(by=column, ascending=False).head(n)
    expected_headers = expected_df.columns.tolist()
    expected_data = expected_df.to_numpy().tolist()
    headers, data = csv_utils_instance.get_top_n_by_column(n, column)
    assert headers == expected_headers
    assert data == expected_data
