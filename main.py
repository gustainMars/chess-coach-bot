import logging
import os
from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from bot.handlers.start import router as start_router
from bot.handlers.analyze import router as analyze_router
from bot.handlers.study import router as study_router
from bot.handlers.attack_training import router as attack_training_router
from bot.db.database import init_db

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WEBHOOK_PATH = "/webhook"

logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    await init_db()
    await bot.set_webhook(
        url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
    )


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_router(start_router)
    dp.include_router(analyze_router)
    dp.include_router(study_router)
    dp.include_router(attack_training_router)

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
