import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers.start import router as start_router
from bot.handlers.analyze import router as analyze_router
from bot.handlers.study import router as study_router
from bot.handlers.attack_training import router as attack_training_router
from bot.db.database import init_db

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)


async def on_startup(**kwargs):
    await init_db()


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(on_startup)
    dp.include_router(start_router)
    dp.include_router(analyze_router)
    dp.include_router(study_router)
    dp.include_router(attack_training_router)

    print("Bot rodando!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
