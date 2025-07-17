from typing import Optional
from unittest.mock import patch, Mock

import pandas as pd
import pytest
from tabulate import tabulate

from src.config import MENU_WIDTH
from src.gui import GUI


def test_start_scraping(mock_scraper: Mock, mock_file_manager: Mock, mock_os_utils: None) -> None:
    """ Тест метода `GUI.start`, когда папка пуста

    Проверяет:
    - `_start_menu` не вызывается (нет файлов)
    - `_run_scraping` вызывается ровно один раз
    - `_main_menu` вызывается пару раз, затем выбрасывает `Exception('Stop')` для выхода из цикла
    """
    with (patch.object(GUI, '_start_menu') as mock_start_menu,
          patch.object(GUI, '_run_scraping') as mock_run_scraping,
          patch.object(GUI, '_main_menu', side_effect=[None, None, Exception('Stop')])):
        gui = GUI(mock_scraper, mock_file_manager)
        with patch('builtins.input', side_effect=['1']):  # 1 – начало сбора данных
            with pytest.raises(Exception, match='Stop'):
                gui.start()
        mock_start_menu.assert_not_called()  # вызова нет, т.к. папка пуста
        mock_run_scraping.assert_called_once()
        assert mock_run_scraping.call_count == 1


def test_run_scraping(mock_scraper: Mock, mock_file_manager: Mock):
    """ Тест метода `_run_scraping` класса `GUI`

    Проверяет:
    - Вызов `scrape()` у `mock_scraper` один раз
    - Вызов `get_data()` у `mock_scraper` один раз
    - Вызов `save_data()` у `mock_file_manager` с правильными данными
    - Корректное обновление `self._df`
    """
    gui = GUI(mock_scraper, mock_file_manager)
    gui._run_scraping()
    # Проверка вызовов методов
    mock_scraper.scrape.assert_called_once()
    mock_scraper.get_data.assert_called_once()
    mock_file_manager.save_data.assert_called_once_with(mock_scraper.get_data.return_value)
    # Проверка self._df на обновление DataFrame
    expected_df = pd.DataFrame(mock_scraper.get_data.return_value)
    pd.testing.assert_frame_equal(gui._df, expected_df)


def test_get_data_by_date(mock_file_manager: Mock) -> None:
    """ Тест метода `_get_data_by_date` класса `GUI`

    Проверяет:
    - Вызов `OSUtils.get_files()` для получения списка файлов
    - Корректный вызов `file_manager.load_data()` с выбранным файлом
    - Корректное обновление и возврат `self._df`
    """
    test_files = [Mock(), Mock()]  # тестовые файлы
    test_files[0].name = 'file1.csv'
    test_files[1].name = 'file2.csv'
    with (patch('src.utils.OSUtils.get_files', return_value=test_files) as mock_get_files,
          patch('builtins.input', return_value='1')):
        gui = GUI(None, mock_file_manager)
        df = gui._get_data_by_date()
        # Проверка вызовов методов
        mock_get_files.assert_called_once()
        mock_file_manager.load_data.assert_called_once_with('file1.csv')
        # Проверка self._df на обновление DataFrame
        expected_df = mock_file_manager.load_data.return_value
        pd.testing.assert_frame_equal(df, expected_df)


@pytest.mark.parametrize('user_choice, expected_method', [
    ('1', '_display_result'),
    ('2', '_display_result'),
    ('3', '_display_result'),
    ('4', '_get_data_by_date'),
])
def test_handle_main_menu_choice(mock_file_manager: Mock, user_choice: str, expected_method: str) -> None:
    """ Тест метода `_handle_main_menu_choice` класса `GUI`

    Проверяет, что в зависимости от выбора пользователя вызывается нужный метод:
    - Если `user_choice` = '1', '2' или '3', вызывается `_display_result()`
    - Если `user_choice` = '4', вызывается `_get_data_by_date()`
    """
    gui = GUI(None, mock_file_manager)
    gui._user_choice = user_choice
    with (patch.object(gui, '_display_result') as mock_display_result,
          patch.object(gui, '_get_data_by_date') as mock_get_data_by_date):
        gui._handle_main_menu_choice()
        if expected_method == '_display_result':
            mock_display_result.assert_called_once()
            mock_get_data_by_date.assert_not_called()
        elif expected_method == '_get_data_by_date':
            mock_get_data_by_date.assert_called_once()
            mock_display_result.assert_not_called()


def test_display_menu(mock_file_manager: Mock) -> None:
    """ Тест метода `_display_menu` класса `GUI`

    Проверяет:
    - Корректность вывода заголовка и опций меню
    - Корректный вызов метода `_get_user_choice()`
    - Обновление `_user_choice` на значение, возвращаемое `_get_user_choice()`
    """
    gui = GUI(None, mock_file_manager)
    title = 'Меню теста'
    options = ['1. Опция один', '2. Опция два', '3. Опция три']
    with patch('builtins.print') as mock_print, \
            patch.object(gui, '_get_user_choice', return_value='1') as mock_get_user_choice:
        gui._display_menu(title, options)
        # Проверка print на вызов с корректными аргументами
        mock_print.assert_any_call(f'{title:=^{MENU_WIDTH}}')
        mock_print.assert_any_call(*options, sep='\n')
        mock_print.assert_any_call('=' * MENU_WIDTH)
        mock_get_user_choice.assert_called_once_with(options_count=len(options))  # проверка вызова _get_user_choice
        assert gui._user_choice == '1'  # проверка обновления _user_choice


@pytest.mark.parametrize('user_choice, input_value, expected_prints, expected_csv_call', [
    ('1', None, [' Результат '], 'get_headers_with_data'),
    ('2', '5', [' Топ-5 по цене '], 'get_top_n_by_column'),
    ('3', '3', [' Топ-3 по рейтингу '], 'get_top_n_by_column'),
])
def test_display_result(mock_file_manager: Mock, user_choice: str, input_value: Optional[str],
                        expected_prints: list[str], expected_csv_call: str) -> None:
    """ Тест метода `_display_result` класса `GUI`

    Проверяет:
    - Корректный вызов методов `get_headers_with_data()` или `get_top_n_by_column()`
    - Корректный вывод заголовков
    - Завершение работы через `_finish_program()`
    """
    mock_csv_utils = Mock()
    gui = GUI(None, mock_file_manager)
    gui._csv_utils = mock_csv_utils
    gui._user_choice = user_choice
    mock_csv_utils.get_headers_with_data.return_value = ([], [])
    mock_csv_utils.get_top_n_by_column.return_value = (['header1', 'header2'], [['row1col1', 'row1col2']])
    with (patch('builtins.print') as mock_print,
          patch.object(gui, '_print_table') as mock_print_table,
          patch.object(gui, '_finish_program') as mock_finish_program,
          patch('builtins.input', return_value=input_value)):
        gui._display_result()
        printed_texts = [''.join(call.args) for call in mock_print.call_args_list]
        for expected in expected_prints:
            assert any(expected in printed for printed in printed_texts), \
                f"Ожидалось: '{expected}', но было: {printed_texts}"
        if expected_csv_call == 'get_headers_with_data':
            mock_csv_utils.get_headers_with_data.assert_called_once()
        else:
            mock_csv_utils.get_top_n_by_column.assert_called_once_with(
                int(input_value),
                'price' if user_choice == '2' else 'rating'
            )
        mock_print_table.assert_called()
        mock_finish_program.assert_called_once()


@patch.object(GUI, '_display_menu')
def test_start_menu(mock_display_menu: Mock, gui: GUI) -> None:
    """ Тест проверяет, что _start_menu вызывает _display_menu с нужными аргументами """
    gui._start_menu()

    mock_display_menu.assert_called_once_with(
        ' Стартовое меню ', [
            '1. Начать новый скрапинг и сохранить результат в SCV-файл',
            '2. Показать предыдущие результаты',
        ]
    )


@patch.object(GUI, '_display_menu')
@patch.object(GUI, '_handle_main_menu_choice')
def test_main_menu(mock_handle_choice, mock_display_menu, gui, test_df):
    """ Тест проверяет, что _main_menu вызывает _display_menu и _handle_main_menu_choice """
    gui._df = test_df
    with patch('builtins.print') as mock_print:
        gui._main_menu()
    mock_print.assert_called_with('\nВсего записей: 2')
    mock_display_menu.assert_called_once_with(
        ' Основное меню ', [
            '1. Показать результат в консоли',
            '2. Показать топ-N товаров по цене',
            '3. Показать топ-N товаров по рейтингу',
            '4. Вернуться к выбору файлов по дате',
            '5. Выйти',
        ]
    )
    mock_handle_choice.assert_called_once()


def test_finish_program(gui):
    """ Тест проверяет, что _finish_program вызывает exit(0) """
    with patch('builtins.print') as mock_print, patch('builtins.exit') as mock_exit:
        gui._finish_program()
    mock_print.assert_called_with('\n')
    mock_exit.assert_called_once_with(0)


def test_print_table(gui):
    """Тест вывода данных в виде таблицы с помощью `_print_table` """
    headers = ['Колонка 1', 'Колонка 2']
    tabular_data = [['Данные 1', 'Данные 2'], ['Данные 3', 'Данные 4']]
    expected_output = tabulate(tabular_data, headers, gui._table_format, maxcolwidths=30)
    with patch('builtins.print') as mock_print:
        gui._print_table(headers, tabular_data)
    mock_print.assert_called_once_with(expected_output)
