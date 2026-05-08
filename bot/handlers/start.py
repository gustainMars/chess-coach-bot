from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

router = Router()

_HELP_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Study", callback_data="open_study"),
            InlineKeyboardButton(text="⚔️ Attack", callback_data="open_attack"),
        ]
    ]
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "♞ Welcome Chess Openings Coach Bot!\n\n"
        "I analyze your games and create a personalized study plan.\n\n"
        "Available commands:\n"
        "/analyze <username> - Analyzes Chess.com games from the last 30 days\n"
        "/study - Starts your flashcards\n"
        "/attack - Identify all capturable pieces\n"
        "/help - Help"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "How to use Chess Openings Coach Bot:\n\n"
        "1. /analyze <username> — analyze your Chess.com games from the last 30 days\n"
        "2. /study — flashcard quiz on your worst opening moments\n"
        "3. /attack — spot all pieces that can be captured in a position",
        reply_markup=_HELP_KEYBOARD,
    )
