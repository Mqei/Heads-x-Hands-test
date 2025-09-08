# bot/states.py
from aiogram.fsm.state import State, StatesGroup

class BattleStates(StatesGroup):
    not_in_battle = State()        # вне боя
    awaiting_player_name = State() # ждём ввода имени
    in_battle = State()            # в бою
    battle_finished = State()      # бой завершён
    in_dungeon = State()           # в подземелье