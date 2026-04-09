from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "♞ Welcome Chess Openings Coach Bot!\n\n"
        "I analyze your games and create a personalized study plan.\n\n"
        "Available commands:\n"
        "/analyze <username> - Analyzes games from Chess.com\n"
        "/study - Starts your flashcards\n"
        "/help - Help"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "How to use Chess Openings Coach Bot:\n\n"
        "1. Use /analyze <your username on chess.com> so I can analyze your games and identify improvements in your openings\n"
        "2. Use /study to practice with flashcards based on your mistakes"
    )