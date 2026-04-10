import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from bot.handlers.start import router as start_router
from bot.handlers.analyze import router as analyze_router

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)

async def main():    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(analyze_router)
    
    print("Bot rodando!")
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())