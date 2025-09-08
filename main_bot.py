# main_bot.py
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
from bot.database import init_db  # <-- добавили импорт
import asyncio
import logging

TOKEN = "8230967064:AAGEo2RbMSQq8dPpQBFHmn9k7WCcVv5p97s"

async def main():
    await init_db()  # ✅ Инициализируем базу данных
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Начать"),
        BotCommand(command="rename", description="Изменить имя"),
        BotCommand(command="fight", description="Начать бой"),
    ])

    print("✅ Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())