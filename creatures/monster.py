from .creature import Creature

class Monster(Creature):
    """
    Класс Монстра — наследник Creature.
    По ТЗ не имеет особых способностей, отличных от базового существа.
    """

    def __init__(self, attack: int, defense: int, max_health: int, damage_range: tuple):
        """
        Инициализация монстра.

        :param attack: Атака (1-30)
        :param defense: Защита (1-30)
        :param max_health: Максимальное здоровье (>0)
        :param damage_range: Диапазон урона (min, max)
        """
        super().__init__(attack, defense, max_health, damage_range)

    def __str__(self):
        return (f"Monster(ATK={self.attack}, DEF={self.defense}, "
                f"HP={self.current_health}/{self.max_health}, "
                f"DMG={self.damage_range[0]}-{self.damage_range[1]})")