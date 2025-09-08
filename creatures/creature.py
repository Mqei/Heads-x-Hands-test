import random
from typing import Tuple

class Creature:
    """
    Базовый класс для всех существ в игре: Игрок и Монстр.
    """

    def __init__(self, attack: int, defense: int, max_health: int, damage_range: Tuple[int, int]):
        """
        Инициализация существа.

        :param attack: Атака (целое число от 1 до 30)
        :param defense: Защита (целое число от 1 до 30)
        :param max_health: Максимальное здоровье (натуральное число > 0)
        :param damage_range: Диапазон урона — кортеж (min_damage, max_damage), где min <= max, и оба > 0
        :raises ValueError: если параметры не соответствуют требованиям
        """
        self._validate_stats(attack, defense, max_health, damage_range)

        self._attack = attack
        self._defense = defense
        self._max_health = max_health
        self._current_health = max_health
        self._damage_range = damage_range

    def _validate_stats(self, attack, defense, max_health, damage_range):
        """Валидация входных параметров."""
        if not isinstance(attack, int) or not (1 <= attack <= 30):
            raise ValueError("Атака должна быть целым числом от 1 до 30")
        if not isinstance(defense, int) or not (1 <= defense <= 30):
            raise ValueError("Защита должна быть целым числом от 1 до 30")
        if not isinstance(max_health, int) or max_health <= 0:
            raise ValueError("Максимальное здоровье должно быть натуральным числом (> 0)")
        if (not isinstance(damage_range, tuple) or len(damage_range) != 2 or
            not all(isinstance(x, int) and x > 0 for x in damage_range) or
            damage_range[0] > damage_range[1]):
            raise ValueError("Урон должен быть кортежем из двух натуральных чисел (min, max), где min <= max")

    @property
    def attack(self) -> int:
        return self._attack

    @property
    def defense(self) -> int:
        return self._defense

    @property
    def max_health(self) -> int:
        return self._max_health

    @property
    def current_health(self) -> int:
        return self._current_health

    @property
    def damage_range(self) -> Tuple[int, int]:
        return self._damage_range

    def is_alive(self) -> bool:
        """Проверяет, живо ли существо."""
        return self._current_health > 0

    def take_damage(self, damage: int):
        """
        Получить урон. Здоровье не может опуститься ниже 0.

        :param damage: количество урона (натуральное число)
        """
        if not isinstance(damage, int) or damage < 0:
            raise ValueError("Урон должен быть неотрицательным целым числом")
        if not self.is_alive():
            return

        self._current_health = max(0, self._current_health - damage)

    def _roll_dice(self, num_dice: int) -> list[int]:
        """
        Бросить N шестигранных кубиков.

        :param num_dice: количество кубиков (>= 1)
        :return: список выпавших значений
        """
        if num_dice < 1:
            raise ValueError("Должен быть брошен хотя бы один кубик")
        return [random.randint(1, 6) for _ in range(num_dice)]

    def attack_target(self, target: 'Creature') -> tuple[bool, list[int]]:
        """
        Атаковать другое существо.

        Всегда бросается 4 кубика d6.
        Успех — если хотя бы один кубик 5 или 6.

        :param target: цель атаки (объект Creature)
        :return: (успех: bool, результаты_бросков: list[int])
        """
        if not isinstance(target, Creature):
            raise TypeError("Цель должна быть объектом класса Creature")
        if not self.is_alive():
            raise ValueError("Мертвое существо не может атаковать")
        if not target.is_alive():
            return False, []

        # 🎲 Всегда бросаем 4 кубика — независимо от модификатора
        num_dice = 4
        dice_results = self._roll_dice(num_dice)

        # ✅ Успех — если хотя бы один кубик 5 или 6
        success = any(die >= 5 for die in dice_results)

        # Если успешно — наносим урон
        if success:
            min_dmg, max_dmg = self.damage_range
            damage_dealt = random.randint(min_dmg, max_dmg)
            target.take_damage(damage_dealt)

        return success, dice_results

    def __str__(self):
            return (f"{self.__class__.__name__}(ATK={self.attack}, DEF={self.defense}, "
                    f"HP={self.current_health}/{self.max_health}, DMG={self.damage_range[0]}-{self.damage_range[1]})")