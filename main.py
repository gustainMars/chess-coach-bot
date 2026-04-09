import asyncio
import logging
import os
import ssl
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from bot.handlers.start import router as start_router
from bot.handlers.analyze import router as analyze_router

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)

async def main():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    session = AiohttpSession()
    session._connector = connector
    
    bot = Bot(token=TOKEN, session=session)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(analyze_router)
    
    print("Bot rodando!")
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())