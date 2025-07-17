import logging

from src.data_manager import CSVFileManager
from src.gui import GUI
from src.scraper import GoldAppleScraper


logger = logging.getLogger('src.scraper')


def main() -> None:
    """ Функция запуска программы """
    scraper = GoldAppleScraper(page_number=2)  # по умолчанию скрапинг с 3 страниц
    file_manager = CSVFileManager()  # по умолчанию CSV-файлы сохраняются в директорию `scraped_data`
    user_interface = GUI(scraper, file_manager)

    user_interface.start()  # запуск графического интерфейса пользователя


if __name__ == '__main__':
    try:
        main()
    except Exception as exc_info:
        logger.error(f'❌ Ошибка: {exc_info}')
