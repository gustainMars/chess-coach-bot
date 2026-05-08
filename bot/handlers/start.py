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
        "/analyze <username> [months] - Analyzes games from Chess.com\n"
        "/study - Starts your flashcards\n"
        "/attack-training - Identify all capturable pieces\n"
        "/help - Help"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "How to use Chess Openings Coach Bot:\n\n"
        "1. /analyze <username> [months] — analyze your Chess.com games"
        " (1–6 months, default 1)\n"
        "2. /study — flashcard quiz on your worst opening moments\n"
        "3. /attack-training — spot all pieces that can be captured in a position"
    )
