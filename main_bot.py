# main_bot.py
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
from bot.database import init_db
from creatures.creature import Creature  # Creature определён в creatures/creature.py
import asyncio
import logging
import os
os.makedirs("saves", exist_ok=True)

class Player(Creature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_health = 100  # или другое начальное значение

    @property
    def current_health(self):
        return self._current_health

    @current_health.setter
    def current_health(self, value):
        self._current_health = value

TOKEN = "8230967064:AAFxO5lhHGiSrqHa5OJ7Q-Dv-q4DhIlYMM4"

# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def main():
    await init_db()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    await bot.set_my_commands([
    BotCommand(command="start", description="Продолжить приключение"),
    BotCommand(command="newgame", description="Начать заново"),
    BotCommand(command="rename", description="Изменить имя"),
    ])

    print("✅ Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
