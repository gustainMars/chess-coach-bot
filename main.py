import asyncio
import logging
import os

# load_dotenv must run before any local imports so module-level os.getenv() calls
# in handlers, middleware, and services read the correct values from .env
from dotenv import load_dotenv
load_dotenv()

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers.start import router as start_router
from bot.handlers.analyze import router as analyze_router
from bot.handlers.study import router as study_router
from bot.handlers.attack_training import router as attack_training_router
from bot.db.database import init_db
from bot.web.routes import create_web_app
from bot.middleware.qa_guard import QAGuardMiddleware

TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)


async def on_startup(**kwargs):
    await init_db()


async def main():
    web_app = create_web_app()
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.getenv("WEBAPP_PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info("Web server started on port %d", port)

    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(QAGuardMiddleware())
    dp.startup.register(on_startup)
    dp.include_router(start_router)
    dp.include_router(analyze_router)
    dp.include_router(study_router)
    dp.include_router(attack_training_router)

    print("Bot rodando!")
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
