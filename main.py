import logging
import os

# load_dotenv must run before any local imports so module-level os.getenv() calls
# in handlers, middleware, and services read the correct values from .env
from dotenv import load_dotenv

load_dotenv()

from aiohttp import web  # noqa: E402
from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application  # noqa: E402
from bot.handlers.start import router as start_router  # noqa: E402
from bot.handlers.analyze import router as analyze_router  # noqa: E402
from bot.handlers.study import router as study_router  # noqa: E402
from bot.handlers.attack_training import router as attack_training_router  # noqa: E402
from bot.db.database import init_db  # noqa: E402
from bot.web.routes import create_web_app  # noqa: E402
from bot.middleware.qa_guard import QAGuardMiddleware  # noqa: E402

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WEBHOOK_PATH = "/webhook"

logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    await init_db()
    if not WEBHOOK_URL:
        logging.error("WEBHOOK_URL env var is not set — webhook will not be registered")
        return
    await bot.set_webhook(
        url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
    )
    logging.info("Webhook set to %s%s", WEBHOOK_URL, WEBHOOK_PATH)


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(QAGuardMiddleware())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_router(start_router)
    dp.include_router(analyze_router)
    dp.include_router(study_router)
    dp.include_router(attack_training_router)

    app = create_web_app()
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
