# main_bot.py
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
import asyncio
import logging
from aiogram.fsm.storage.memory import MemoryStorage

# ВСТАВЬТЕ СЮДА СВОЙ ТОКЕН
TOKEN = " "

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Создаём бота и диспетчер
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутер с обработчиками
    dp.include_router(router)

    # Устанавливаем команды в меню
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать"),
        BotCommand(command="fight", description="Начать бой"),
        BotCommand(command="next", description="Следующий раунд"),
    ])

    print("✅ Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
