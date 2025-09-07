import random
from typing import List

class Dice:
    """
    Утилитарный класс для бросков шестигранных кубиков (d6).
    """

    @staticmethod
    def roll(n: int) -> List[int]:
        """
        Бросить N шестигранных кубиков.

        :param n: количество кубиков (должно быть >= 1)
        :return: список результатов бросков (целые числа от 1 до 6)
        :raises ValueError: если n < 1
        """
        if not isinstance(n, int) or n < 1:
            raise ValueError("Количество кубиков должно быть целым числом >= 1")

        return [random.randint(1, 6) for _ in range(n)]