# main_bot.py
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
from bot.database import init_db
import asyncio
import logging

<<<<<<< HEAD
TOKEN = "8230967064:AAHW8ImubQfCz_QGTsz-47n6tSYwGPSRicY"
=======
# ВСТАВЬТЕ СЮДА СВОЙ ТОКЕН
TOKEN = " "

# Настройка логирования
logging.basicConfig(level=logging.INFO)
>>>>>>> 4df39e53d3d6c0a4cafadbfb2a4ec9f3ac2e1956

async def main():
    await init_db()  # ✅ Инициализируем базу данных
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    await bot.set_my_commands([
    BotCommand(command="start", description="Начать"),
    BotCommand(command="dungeon", description="Войти в подземелье"),
    BotCommand(command="rename", description="Изменить имя"),
    ])

    print("✅ Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
