# bot/database.py

import aiosqlite
import json
import os
from datetime import datetime
from .dungeon import Dungeon
from creatures.player import Player

DB_PATH = "players.db"  # ← Используем DB_PATH вместо DB_NAME

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA synchronous = FULL")
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                player_name TEXT NOT NULL,
                dungeon_data TEXT,
                player_attack INTEGER,
                player_defense INTEGER,
                player_max_health INTEGER,
                player_current_health INTEGER,
                player_heal_uses_left INTEGER,
                player_damage_min INTEGER,
                player_damage_max INTEGER
            )
        """)
        await db.commit()

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA synchronous = FULL")  
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                dungeon_state TEXT,
                player_state TEXT
            )
        """)
        await db.commit()
    async with aiosqlite.connect(DB_PATH) as db:
        # Create table with all columns
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                player_name TEXT NOT NULL,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                dungeon_data TEXT,
                player_attack INTEGER,
                player_defense INTEGER,
                player_max_health INTEGER,
                player_current_health INTEGER,
                player_heal_uses_left INTEGER,
                player_damage_min INTEGER,
                player_damage_max INTEGER
            )
        """)
        
        # Check if new columns exist and add them if they don't
        cursor = await db.execute("PRAGMA table_info(players)")
        columns = await cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        new_columns = [
            ("dungeon_data", "TEXT"),
            ("player_attack", "INTEGER"),
            ("player_defense", "INTEGER"),
            ("player_max_health", "INTEGER"),
            ("player_current_health", "INTEGER"),
            ("player_heal_uses_left", "INTEGER"),
            ("player_damage_min", "INTEGER"),
            ("player_damage_max", "INTEGER")
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                await db.execute(f"ALTER TABLE players ADD COLUMN {column_name} {column_type}")
                print(f"Added column {column_name} to players table")
        
        await db.commit()

async def save_game_state(user_id: int, dungeon: Dungeon, player: Player):
    """Сохраняет состояние игры в БД."""
    # Сериализуем подземелье как словарь
    dungeon_dict = {
        "width": dungeon.width,
        "height": dungeon.height,
        "player_x": dungeon.player_x,
        "player_y": dungeon.player_y,
        "rooms": {
            f"{x},{y}": {
                "room_type": dungeon.rooms[(x, y)].room_type,
                "visited": dungeon.rooms[(x, y)].visited
            }
            for y in range(dungeon.height)
            for x in range(dungeon.width)
            if (x, y) in dungeon.rooms
        }
    }


    player_name = await get_player_name(user_id) or player.name

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO players (
                user_id, player_name, dungeon_data,
                player_attack, player_defense, player_max_health,
                player_current_health, player_heal_uses_left,
                player_damage_min, player_damage_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            player_name,
            json.dumps(dungeon_dict),
            player.attack,
            player.defense,
            player.max_health,
            player.current_health,
            player.heal_uses_left,
            player.damage_range[0],
            player.damage_range[1]
        ))
        await db.commit()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO players (
                user_id, player_name, dungeon_data,
                player_attack, player_defense, player_max_health,
                player_current_health, player_heal_uses_left,
                player_damage_min, player_damage_max
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            # Получаем имя игрока для сохранения (на случай, если его нет)
            (await get_player_name(user_id)) or "Игрок",
            json.dumps(dungeon_dict),
            player.attack,
            player.defense,
            player.max_health,
            player.current_health,
            getattr(player, '_heal_uses_left', 4),  # fallback на 4
            player.damage_range[0],
            player.damage_range[1]
        ))
        await db.commit()

async def get_player_name(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT player_name FROM players WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def save_player_name(user_id: int, player_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO players (user_id, player_name)
            VALUES (?, ?)
        """, (user_id, player_name))
        await db.commit()

async def backup_game_state(user_id: int):
    """Сохраняет прогресс в отдельный JSON-файл на диске как резервную копию"""
    game_data = await load_game_state(user_id)
    if not game_data:
        return False

    dungeon, player = game_data
    name = await get_player_name(user_id) or "unknown"

    dungeon_dict = {
        "width": dungeon.width,
        "height": dungeon.height,
        "player_x": dungeon.player_x,
        "player_y": dungeon.player_y,
        "rooms": {
            f"{x},{y}": {
                "room_type": dungeon.rooms[(x, y)].room_type,
                "visited": dungeon.rooms[(x, y)].visited
            }
            for y in range(dungeon.height)
            for x in range(dungeon.width)
            if (x, y) in dungeon.rooms
        }
    }

    backup_data = {
        "user_id": user_id,
        "name": name,
        "timestamp": datetime.now().isoformat(),
        "dungeon": dungeon_dict,
        "player": {
            "attack": player.attack,
            "defense": player.defense,
            "max_health": player.max_health,
            "current_health": player.current_health,
            "heal_uses_left": player.heal_uses_left,
            "damage_range": player.damage_range
        }
    }

    filename = f"saves/{user_id}_{name.replace(' ', '_')}_{int(datetime.now().timestamp())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=4)

    return filename
    
async def load_game_state(user_id: int) -> tuple[Dungeon, Player] | None:
    """Загружает состояние игры из БД."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT dungeon_data, player_attack, player_defense, player_max_health,
                   player_current_health, player_heal_uses_left, player_damage_min, player_damage_max
            FROM players WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or not row[0]:
                return None

            dungeon_data = json.loads(row[0])
            player = Player(
                attack=row[1],
                defense=row[2],
                max_health=row[3],
                damage_range=(row[6], row[7])
            )
            player.current_health = row[4]
            player.heal_uses_left = row[5]

            from .dungeon import Dungeon
            dungeon = Dungeon(width=dungeon_data["width"], height=dungeon_data["height"])
            dungeon.player_x = dungeon_data["player_x"]
            dungeon.player_y = dungeon_data["player_y"]

            # Заполняем комнаты
            for key, room_data in dungeon_data["rooms"].items():
                x, y = map(int, key.split(","))
                if (x, y) in dungeon.rooms:
                    dungeon.rooms[(x, y)].room_type = room_data["room_type"]
                    dungeon.rooms[(x, y)].visited = room_data["visited"]

            return dungeon, player