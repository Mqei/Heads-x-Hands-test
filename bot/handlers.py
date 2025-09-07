# bot/handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from .states import BattleStates
from creatures import Player, Monster
import random
import asyncio

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

# 🏁 /start — начальное состояние
@router.message(Command("start"), StateFilter(default_state, BattleStates))
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(BattleStates.not_in_battle)
    await message.answer(
        "🎮 *Добро пожаловать в Creature Battle Bot!*\n\n"
        "Нажмите ⚔️ *Начать бой*, чтобы сразиться с монстром!\n"
        "Управляйте боем с помощью кнопок — удобно и быстро.",
        reply_markup=get_start_keyboard()
    )

# 🎲 Начало боя
@router.callback_query(F.data == "start_fight", StateFilter(BattleStates.not_in_battle))
async def start_fight(callback: CallbackQuery, state: FSMContext):
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
    await state.update_data(player=player, monster=monster, round_num=1)
    await callback.message.edit_text("🌀 Подготовка к бою...")
    await asyncio.sleep(1)
    # Меняем состояние
    await state.set_state(BattleStates.in_battle)

    # 🎨 Формируем красивый текст
    text = (
        f"⚔️ *БОЙ НАЧИНАЕТСЯ!* ⚔️\n\n"
        f"🧙 *Игрок*:\n"
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
        f"➡️ *Нажмите «Следующий раунд», чтобы начать бои!*\n"
    )

    # Отправляем сообщение
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
    success = player.attack_target(monster)
    if success:
        lines.append("✅ Попадание!")
    else:
        lines.append("❌ Промах!")

    if not monster.is_alive():
        lines.append("\n🏆 *Монстр повержен!*")
        await callback.message.edit_text("\n".join(lines))
        await finish_battle(callback, state, winner="player")
        return

    # Монстр атакует
    lines.append("\n👹 *Монстр атакует...*")
    success = monster.attack_target(player)
    if success:
        lines.append("💥 Попадание!")
    else:
        lines.append("🛡️ Уклонение!")

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

    if winner == "player" or (player.is_alive() and not monster.is_alive()):
        result = "🎉 *ПОБЕДА ИГРОКА!* 🎉"
    else:
        result = "💀 *МОНСТР ПОБЕДИЛ!* 💀"

    text = (
        f"{result}\n\n"
        f"🧙 Игрок: {player.current_health}/{player.max_health} ❤️\n"
        f"👹 Монстр: {monster.current_health}/{monster.max_health} ❤️\n\n"
        f"Начать новый бой — /start"
    )

    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer()