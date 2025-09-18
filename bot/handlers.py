# bot/handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from .states import BattleStates
from creatures import Player, Monster
from creatures.creature import Creature
import random
import asyncio
import os
import json
import aiosqlite
from .database import get_player_name, save_player_name, save_game_state, load_game_state
from .dungeon import Dungeon

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

@router.message(Command("restore"))
async def cmd_restore(message: Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /restore <имя_файла>")
        return

    filename = f"saves/{args[1]}"
    if not os.path.exists(filename):
        await message.answer("Файл не найден.")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)


    dungeon_data = backup_data["dungeon"]
    player_data = backup_data["player"]
    name = backup_data["name"]

    await save_player_name(user_id, name)

    async with aiosqlite.connect("players.db") as db:
        await db.execute("""
            UPDATE players SET dungeon_state = ?, player_state = ? WHERE user_id = ?
        """, (json.dumps(dungeon_data), json.dumps(player_data), user_id))
        await db.commit()

    await message.answer(f"✅ Прогресс из {args[1]} восстановлен!")
    await cmd_start(message, state)  

@router.message(Command("rename"))
async def cmd_rename(message: Message, state: FSMContext):
    await state.set_state(BattleStates.awaiting_player_name)
    await message.answer("✏️ Введите новое имя вашего героя:")

# 🏁 /start — начальное состояние
@router.message(Command("start"), StateFilter(default_state, BattleStates))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    player_name = await get_player_name(user_id)

    if player_name:
        await state.update_data(player_name=player_name)
        # ✅ Сразу создаём подземелье
        await enter_dungeon_automatically(message, state, player_name)
    else:
        await state.set_state(BattleStates.awaiting_player_name)
        await message.answer(
            "🎮 *Добро пожаловать в Creature Battle Bot!*\n\n"
            "✏️ Введите имя вашего героя (например, 'Дайте', 'Мне','Работу пж'):"
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
    await save_player_name(user_id, player_name)

    # ✅ Сразу отправляем в подземелье с созданием игрока
    await enter_dungeon_automatically(message, state, player_name)

#автоматизация подземелья, что бы работало    
async def enter_dungeon_automatically(message: Message, state: FSMContext, player_name: str):
    """Автоматический вход в подземелье после /start — с загрузкой сохранения"""
    user_id = message.from_user.id

    # Пробуем загрузить сохранение
    game_state = await load_game_state(user_id)
    
    if game_state:
        dungeon, player = game_state
        text = f"🧙 *{player_name}*, добро пожаловать обратно!\nВаше приключение продолжается..."
    else:
        # Создаём нового игрока и подземелье
        player = Player(
            attack=random.randint(10, 25),
            defense=random.randint(5, 20),
            max_health=random.randint(80, 150),
            damage_range=(random.randint(3, 7), random.randint(8, 15))
        )
        dungeon = Dungeon(width=5, height=5)
        text = (
            f"🧙 *{player_name}*, храбрый искатель приключений!\n"
            f"Вы стоите у входа в *Забытое Подземелье Загадок*...\n"
            f"Говорят, в его глубинах спрятаны сокровища древних королей."
        )

    # Сохраняем в FSM
    await state.update_data(
        player=player,
        player_name=player_name,
        dungeon=dungeon
    )
    await state.set_state(BattleStates.in_dungeon)

    # Сохраняем в БД (даже если загрузили — обновляем)
    await save_game_state(user_id, dungeon, player)

    current_room = dungeon.get_current_room()
    directions = dungeon.get_available_directions()

    keyboard_buttons = []
    dir_map = {"⬆️ Вверх": "up", "⬇️ Вниз": "down", "⬅️ Налево": "left", "➡️ Направо": "right"}
    for dir_text in directions:
        dir_key = dir_map.get(dir_text)
        if dir_key:
            keyboard_buttons.append([InlineKeyboardButton(text=dir_text, callback_data=f"move_{dir_key}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    text += (
        f"\n\n🗺️ *Ваша карта:*\n\n"
        f"{dungeon.render_map()}\n\n"
        f"🛡️ Ваши статы: ATK={player.attack}, DEF={player.defense}, "
        f"HP={player.current_health}/{player.max_health}\n"
        f"📍 *Текущая комната:* {current_room.room_type.upper()}\n"
        f"➡️ Выберите путь:"
    )

    await message.answer(text, reply_markup=keyboard)
#Движение
@router.callback_query(F.data.startswith("move_"), StateFilter(BattleStates.in_dungeon))
async def handle_move(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dungeon: Dungeon = data["dungeon"]

    direction = callback.data.split("_")[1]

    if dungeon.move_player(direction):
        current_room = dungeon.get_current_room()
        current_room.visited = True

        # ✅ Убрали дублирующий блок здесь — оставляем один ниже

        # Генерация клавиатуры
        directions = dungeon.get_available_directions()
        keyboard_buttons = []
        dir_map = {"⬆️ Вверх": "up", "⬇️ Вниз": "down", "⬅️ Налево": "left", "➡️ Направо": "right"}
        for dir_text in directions:
            dir_key = dir_map.get(dir_text)
            if dir_key:
                keyboard_buttons.append([InlineKeyboardButton(text=dir_text, callback_data=f"move_{dir_key}")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        # Проверка типа комнаты
        room_text = ""
        if current_room.room_type == "monster":
            # ✅ Генерируем монстра и начинаем бой
            monster = Monster(
                attack=random.randint(8, 22),
                defense=random.randint(3, 18),
                max_health=random.randint(60, 130),
                damage_range=(random.randint(2, 6), random.randint(7, 13))
            )
            await state.update_data(monster=monster, round_num=1)
            await state.set_state(BattleStates.in_battle)

            text = (
                f"👹 *БОЙ С МОНСТРОМ!*\n\n"
                f"Здоровье монстра: {monster.current_health}/{monster.max_health}\n\n"
                f"Нажмите ➡️ *Следующий раунд*, чтобы начать!"
            )
            await callback.message.edit_text(text, reply_markup=get_battle_keyboard())
            return  # ✅ Важно — выходим, чтобы не показывать карту

        elif current_room.room_type == "treasure":
            room_text = "💰 *ВЫ НАШЛИ СОКРОВИЩЕ!* +50 монет!"
        elif current_room.room_type == "trap":
            room_text = "💀 *ЛОВУШКА!* Вы потеряли 20 HP."
        elif current_room.room_type == "exit":
            room_text = "🏆 *ПОЗДРАВЛЯЕМ! ВЫ НАШЛИ СОКРОВИЩНИЦУ!*"
            await state.set_state(BattleStates.not_in_battle)

        # Формируем сообщение с картой
        text = (
            f"🗺️ *КАРТА ПОДЗЕМЕЛЬЯ*\n\n"
            f"{dungeon.render_map()}\n\n"
            f"{room_text}\n"
            f"Текущая комната: *{current_room.room_type.upper()}*\n"
            f"Выберите направление:"
        )

        await callback.message.edit_text(text, reply_markup=keyboard)

    else:
        await callback.answer("Туда нельзя идти!", show_alert=True)

    await callback.answer()
        # Автосохранение прогресса
    user_id = callback.from_user.id
    data = await state.get_data()
    player = data["player"]
    dungeon = data["dungeon"]
    await save_game_state(user_id, dungeon, player)
#newgame
@router.message(Command("newgame"))
async def cmd_newgame(message: Message, state: FSMContext):
    """Начать новое приключение — стирает сохранение"""
    user_id = message.from_user.id
    data = await state.get_data()
    player_name = data.get("player_name")

    if not player_name:
        await message.answer("Сначала введите имя командой /start")
        return

    # Создаём нового игрока и подземелье
    player = Player(
        attack=random.randint(10, 25),
        defense=random.randint(5, 20),
        max_health=random.randint(80, 150),
        damage_range=(random.randint(3, 7), random.randint(8, 15))
    )
    dungeon = Dungeon(width=5, height=5)

    # Сохраняем в FSM и БД
    await state.update_data(player=player, player_name=player_name, dungeon=dungeon)
    await state.set_state(BattleStates.in_dungeon)
    await save_game_state(user_id, dungeon, player)

    current_room = dungeon.get_current_room()
    directions = dungeon.get_available_directions()

    keyboard_buttons = []
    dir_map = {"⬆️ Вверх": "up", "⬇️ Вниз": "down", "⬅️ Налево": "left", "➡️ Направо": "right"}
    for dir_text in directions:
        dir_key = dir_map.get(dir_text)
        if dir_key:
            keyboard_buttons.append([InlineKeyboardButton(text=dir_text, callback_data=f"move_{dir_key}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    text = (
        f"🆕 *НОВОЕ ПРИКЛЮЧЕНИЕ!*\n"
        f"🧙 {player_name}, вы входите в новое подземелье!\n\n"
        f"🗺️ *Карта:*\n\n"
        f"{dungeon.render_map()}\n\n"
        f"🛡️ Статы: ATK={player.attack}, DEF={player.defense}, HP={player.current_health}/{player.max_health}\n"
        f"📍 Текущая комната: {current_room.room_type.upper()}\n"
        f"➡️ Вперёд, к приключениям!"
    )

    await message.answer(text, reply_markup=keyboard)

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
    lines.append(f"🎲 Бросок (4d6): [{dice_str}]")

    if success:
        lines.append("✅ *Попадание!* (выпало 5 или 6)")
    else:
        lines.append("❌ *Промах!* (ни одного 5 или 6)")

    # Проверка: если монстр умер — завершаем бой
    if not monster.is_alive():
        lines.append("\n🏆 *Монстр повержен!*")
        await callback.message.edit_text("\n".join(lines))
        await finish_battle(callback, state, winner="player")
        return  # ✅ ВЫХОДИМ — монстр мёртв, не даём ему атаковать

    # Монстр атакует — только если жив
    if monster.is_alive():
        lines.append("\n👹 *Монстр атакует...*")
        success, dice_results = monster.attack_target(player)  # ✅ Получаем броски
        dice_str = ", ".join(map(str, dice_results))
        lines.append(f"🎲 Бросок (4d6): [{dice_str}]")

        if success:
            lines.append("💥 *Попадание!*")
        else:
            lines.append("🛡️ *Уклонение!*")
    else:
        lines.append("\n🏆 *Монстр уже мёртв!*")

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

# Подземелье
#@router.message(Command("dungeon"), StateFilter(BattleStates.not_in_battle))
#async def cmd_dungeon(message: Message, state: FSMContext):
#    ...
#    # Создаём новое подземелье
#    dungeon = Dungeon(width=5, height=5)
#
    # Сохраняем в FSM
#    await state.update_data(dungeon=dungeon)
#    await state.set_state(BattleStates.in_dungeon)
#
#    current_room = dungeon.get_current_room()
#    directions = dungeon.get_available_directions()
#
#    # Генерируем клавиатуру
#    keyboard = InlineKeyboardMarkup(inline_keyboard=[
#        [InlineKeyboardButton(text=dir_text, callback_data=f"move_{dir_key}")]
#        for dir_text, dir_key in zip(directions, ["up", "down", "left", "right"][:len(directions)])
#    ])

    # Сообщение с картой
    #text = (
    #    f"🗺️ *КАРТА ПОДЗЕМЕЛЬЯ*\n\n"
   #     f"{dungeon.render_map()}\n\n"
  #      f"Вы в комнате: *{current_room.room_type.upper()}*\n"
 #       f"Выберите направление:"
 #   )
#
#    await message.answer(text, reply_markup=keyboard)

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
    data = await state.get_data()
    player = data["player"]
    monster = data["monster"]
    player_name = data.get("player_name", "Игрок")

    if winner == "player" or (player.is_alive() and not monster.is_alive()):
        result = "🎉 *ПОБЕДА ИГРОКА!* 🎉"

        # Проверяем, был ли бой в подземелье
        current_state = await state.get_state()
        if current_state == BattleStates.in_battle.state:
            dungeon_data = data.get("dungeon")
            if dungeon_data:
                # Возвращаемся в подземелье
                await state.set_state(BattleStates.in_dungeon)

                dungeon: Dungeon = dungeon_data
                current_room = dungeon.get_current_room()
                directions = dungeon.get_available_directions()

                # Генерируем клавиатуру
                keyboard_buttons = []
                dir_map = {
                    "⬆️ Вверх": "up",
                    "⬇️ Вниз": "down",
                    "⬅️ Налево": "left",
                    "➡️ Направо": "right"
                }
                for dir_text in directions:
                    dir_key = dir_map.get(dir_text)
                    if dir_key:
                        keyboard_buttons.append([
                            InlineKeyboardButton(text=dir_text, callback_data=f"move_{dir_key}")
                        ])

                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

                # Сообщение
                text = (
                    f"🗺️ *КАРТА ПОДЗЕМЕЛЬЯ*\n\n"
                    f"{dungeon.render_map()}\n\n"
                    f"✅ *Монстр повержен!*\n"
                    f"Текущая комната: *{current_room.room_type.upper()}*\n"
                    f"Выберите направление:"
                )

                await callback.message.edit_text(text, reply_markup=keyboard)
                return  # ✅ Завершаем функцию — не показываем стандартное сообщение о победе

    else:
        result = "💀 *МОНСТР ПОБЕДИЛ!* 💀"

    # Стандартное сообщение о конце боя (если не в подземелье)
    text = (
        f"{result}\n\n"
        f"🧙 *{player_name}*: {player.current_health}/{player.max_health} ❤️\n"
        f"👹 *Монстр*: {monster.current_health}/{monster.max_health} ❤️\n\n"
        f"Начать новый бой — /start"
    )

    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer()