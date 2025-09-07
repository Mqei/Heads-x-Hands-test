# bot/states.py
from aiogram.fsm.state import State, StatesGroup

class BattleStates(StatesGroup):
    not_in_battle = State()    # вне боя (начальное состояние)
    in_battle = State()        # в процессе боя
    battle_finished = State()  # бой завершён (ожидание действия)