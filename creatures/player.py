from .creature import Creature
import math

class Player(Creature):
    """
    Класс Игрока — наследник Creature с возможностью исцеления.
    Может исцелиться до 4 раз на 30% от максимального здоровья.
    """

    MAX_HEAL_USES = 4
    HEAL_PERCENT = 0.3  # 30%

    def __init__(self, attack: int, defense: int, max_health: int, damage_range: tuple):
        """
        Инициализация игрока.

        :param attack: Атака (1-30)
        :param defense: Защита (1-30)
        :param max_health: Максимальное здоровье (>0)
        :param damage_range: Диапазон урона (min, max)
        """
        super().__init__(attack, defense, max_health, damage_range)
        self._heal_uses_left = self.MAX_HEAL_USES

    @property
    def heal_uses_left(self) -> int:
        return self._heal_uses_left

    @property
    def current_health(self):
        return self._current_health

    @current_health.setter
    def current_health(self, value):
        self._current_health = value

    def heal(self) -> bool:
        """
        Исцелить себя на 30% от максимального здоровья.
        Можно использовать только если:
          - Игрок жив
          - Остались попытки исцеления

        Здоровье не может превысить максимальное.

        :return: True, если исцеление успешно, иначе False
        """
        if not self.is_alive():
            return False  # Мертвый игрок не может лечиться

        if self._heal_uses_left <= 0:
            return False  # Попытки исцеления закончились

        # Рассчитываем, сколько ХП восстановить (30% от максимума, округляем вниз)
        heal_amount = int(self.HEAL_PERCENT * self.max_health)

        # Не лечим больше, чем нужно до максимума
        actual_heal = min(heal_amount, self.max_health - self._current_health)

        self._current_health += actual_heal
        self._heal_uses_left -= 1

        return True

    def __str__(self):
        return (f"Player(ATK={self.attack}, DEF={self.defense}, "
                f"HP={self.current_health}/{self.max_health}, "
                f"DMG={self.damage_range[0]}-{self.damage_range[1]}, "
                f"Heals left: {self.heal_uses_left})")