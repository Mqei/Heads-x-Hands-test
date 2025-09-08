# bot/handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from .states import BattleStates
from creatures import Player, Monster
import random
import asyncio
from .database import get_player_name, save_player_name

player_names_db = {}
router = Router()

# 🎛️ Генерация клавиатуры в зависимости от состояния
def get_battle_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий раунд", callback_data="next_round")],
        [InlineKeyboardButton(text="💊 Исцелиться", callback_data="heal")],
        [InlineKeyboardButton(text="🏳️ Сдаться", callback_data="surrender")]
    ])

def get_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Начать бой", callback_data="start_fight")]
    ])

@router.message(Command("rename"))
async def cmd_rename(message: Message, state: FSMContext):
    await state.set_state(BattleStates.awaiting_player_name)
    await message.answer("✏️ Введите новое имя вашего героя:")

# 🏁 /start — начальное состояние
@router.message(Command("start"), StateFilter(default_state, BattleStates))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    player_name = await get_player_name(user_id)  # ✅ Получаем из БД

    if player_name:
        await state.update_data(player_name=player_name)
        await state.set_state(BattleStates.not_in_battle)
        await message.answer(
            f"🧙 С возвращением, *{player_name}*!\n\n"
            "Готовы к новому бою? Нажмите ⚔️ *Начать бой*!",
            reply_markup=get_start_keyboard()
        )
    else:
        await state.set_state(BattleStates.awaiting_player_name)
        await message.answer(
            "🎮 *Добро пожаловать в Creature Battle Bot!*\n\n"
            "✏️ Введите имя вашего героя (например, 'Дайте', 'Мне', 'Работу пж'):"
        )
#Forward name
@router.message(StateFilter(BattleStates.awaiting_player_name), F.text)
async def player_name_received(message: Message, state: FSMContext):
    player_name = message.text.strip()

    if len(player_name) < 2:
        await message.answer("❌ Имя должно быть не короче 2 символов. Попробуйте снова:")
        return
    if len(player_name) > 20:
        await message.answer("❌ Имя не должно быть длиннее 20 символов. Попробуйте снова:")
        return

    user_id = message.from_user.id
    await save_player_name(user_id, player_name)  # ✅ Сохраняем в БД

    await state.update_data(player_name=player_name)
    await state.set_state(BattleStates.not_in_battle)

    await message.answer(
        f"🧙 Добро пожаловать, *{player_name}*!\n\n"
        "Готовы сразиться с монстром? Нажмите ⚔️ *Начать бой*!",
        reply_markup=get_start_keyboard()
    )
    # Сохраняем имя в FSM
    await state.update_data(player_name=player_name)

    # Переходим к состоянию "не в бою"
    await state.set_state(BattleStates.not_in_battle)


# 🎲 Начало боя
@router.callback_query(F.data == "start_fight", StateFilter(BattleStates.not_in_battle))
async def start_fight(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player_name = data.get("player_name", "Игрок")  # на случай, если имя не задано

    # Генерируем игрока и монстра
    player = Player(
        attack=random.randint(10, 25),
        defense=random.randint(5, 20),
        max_health=random.randint(80, 150),
        damage_range=(random.randint(3, 7), random.randint(8, 15))
    )

    monster = Monster(
        attack=random.randint(8, 22),
        defense=random.randint(3, 18),
        max_health=random.randint(60, 130),
        damage_range=(random.randint(2, 6), random.randint(7, 13))
    )

    # Сохраняем в FSM
    await state.update_data(player=player, monster=monster, round_num=1, player_name=player_name)

    # Меняем состояние
    await state.set_state(BattleStates.in_battle)

    # 🎨 Формируем красивый текст с именем игрока
    text = (
        f"⚔️ *БОЙ НАЧИНАЕТСЯ!* ⚔️\n\n"
        f"🧙 *{player_name}*:\n"
        f"  🛡️ Атака: {player.attack}\n"
        f"  🛡️ Защита: {player.defense}\n"
        f"  ❤️ Здоровье: {player.current_health}/{player.max_health}\n"
        f"  💥 Урон: {player.damage_range[0]}–{player.damage_range[1]}\n"
        f"  🧹 Исцелений: {player.heal_uses_left}\n\n"
        f"👹 *Монстр*:\n"
        f"  🛡️ Атака: {monster.attack}\n"
        f"  🛡️ Защита: {monster.defense}\n"
        f"  ❤️ Здоровье: {monster.current_health}/{monster.max_health}\n"
        f"  💥 Урон: {monster.damage_range[0]}–{monster.damage_range[1]}\n\n"
        f"➡️ *Нажмите «Следующий раунд», чтобы начать бои!*"
    )

    await callback.message.edit_text(text, reply_markup=get_battle_keyboard())
    await callback.answer()
# 🔄 Следующий раунд
@router.callback_query(F.data == "next_round", StateFilter(BattleStates.in_battle))
async def next_round(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player = data["player"]
    monster = data["monster"]
    round_num = data["round_num"]

    # Проверка: если бой уже окончен (на случай сбоя)
    if not player.is_alive() or not monster.is_alive():
        await finish_battle(callback, state)
        return

    # === Генерация текста раунда ===
    lines = [f"=== 🎯 РАУНД {round_num} ==="]
    lines.append(f"❤️ Игрок: {player.current_health}/{player.max_health} | 🧹 Исцелений: {player.heal_uses_left}")
    lines.append(f"❤️ Монстр: {monster.current_health}/{monster.max_health}")
    lines.append("-" * 30)

    # Игрок атакует
    lines.append("\n👉 *Игрок атакует...*")
    success, dice_results = player.attack_target(monster)  # ✅ Получаем броски
    dice_str = ", ".join(map(str, dice_results))
    if 6 in dice_results:
        lines.append("🎯 *Критический бросок!*")
    lines.append(f"🎲 Бросок ({len(dice_results)}d6): [{dice_str}]")

    if success:
        lines.append("✅ *Попадание!* (выпало 5 или 6)")
    else:
        lines.append("❌ *Промах!* (ни одного 5 или 6)")

    # Монстр атакует
    lines.append("\n👹 *Монстр атакует...*")
    success, dice_results = monster.attack_target(player)  # ✅ Получаем броски
    dice_str = ", ".join(map(str, dice_results))
    if 6 in dice_results:
        lines.append("🎯 *Критический бросок!*")
    lines.append(f"🎲 Бросок ({len(dice_results)}d6): [{dice_str}]")

    if success:
        lines.append("💥 *Попадание!*")
    else:
        lines.append("🛡️ *Уклонение!*")

    # Обновляем данные в FSM
    await state.update_data(player=player, monster=monster, round_num=round_num + 1)

    # Обновляем сообщение
    await callback.message.edit_text("\n".join(lines), reply_markup=get_battle_keyboard())
    await callback.answer()

# 💊 Исцеление
@router.callback_query(F.data == "heal", StateFilter(BattleStates.in_battle))
async def heal_player(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player = data["player"]

    if not player.is_alive():
        await callback.answer("😵 Вы мертвы!", show_alert=True)
        return

    if player.current_health >= player.max_health * 0.5 and player.heal_uses_left > 0:
        await callback.answer("✨ Здоровье и так выше 50% — экономьте исцеления!", show_alert=True)
        return

    if player.heal():
        healed = int(Player.HEAL_PERCENT * player.max_health)
        await callback.answer(f"✨ +{healed} HP! Теперь: {player.current_health}/{player.max_health}", show_alert=True)
        await state.update_data(player=player)  # сохраняем обновлённого игрока
    else:
        await callback.answer("❌ Нельзя исцелиться (лимит исчерпан)", show_alert=True)

    # Обновляем клавиатуру — кнопка может исчезнуть, если здоровье стало >50%
    await callback.message.edit_reply_markup(reply_markup=get_battle_keyboard())

# 🏳️ Сдаться
@router.callback_query(F.data == "surrender", StateFilter(BattleStates.in_battle))
async def surrender(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BattleStates.battle_finished)
    await callback.message.edit_text(
        "🕊️ Вы сдались. Монстр торжествует!\n\nНачать новый бой — /start",
        reply_markup=None
    )
    await callback.answer()

# 🏁 Завершение боя
async def finish_battle(callback: CallbackQuery, state: FSMContext, winner: str = None):
    await state.set_state(BattleStates.battle_finished)

    data = await state.get_data()
    player = data["player"]
    monster = data["monster"]
    player_name = data.get("player_name", "Игрок")  # <-- добавлено получение имени

    if winner == "player" or (player.is_alive() and not monster.is_alive()):
        result = "🎉 *ПОБЕДА ИГРОКА!* 🎉"
    else:
        result = "💀 *МОНСТР ПОБЕДИЛ!* 💀"

    text = (
        f"{result}\n\n"
        f"🧙 *{player_name}*: {player.current_health}/{player.max_health} ❤️\n"
        f"👹 *Монстр*: {monster.current_health}/{monster.max_health} ❤️\n\n"
        f"Начать новый бой — /start"
    )

    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer()