from src.base import BaseValidator


class PageNumberValidator(BaseValidator[int]):
    """ Класс для валидации количества страниц, которое необходимо спарсить """

    @staticmethod
    def validate(value: int) -> int:
        """ Валидирует количество страниц """
        if not isinstance(value, int):
            raise TypeError('Количество страниц должно быть целым числом')
        if not 0 < value < 100_000:
            raise ValueError('Количество страниц должно быть от 0 до 100 000')
        return value


class GoldAppleDataValidator(BaseValidator[dict]):
    """ Класс для валидации данных, собранных с Золотого яблока """

    @staticmethod
    def validate(value: dict) -> dict:
        """ Валидирует извлеченные данные """
        if not isinstance(value, dict):
            raise TypeError('Данные должны быть словарного типа')
        return value
