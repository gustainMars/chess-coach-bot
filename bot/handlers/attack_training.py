import logging
import os
from urllib.parse import urlencode

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from bot.domain.messages import Messages
from bot.services.attack_generator import (
    generate_attack_position,
)
from bot.services.board_renderer import fen_to_png

router = Router()


def _webapp_keyboard(fen: str) -> InlineKeyboardMarkup | None:
    miniapp_url = os.getenv("MINIAPP_URL", "").rstrip("/")
    if not miniapp_url:
        return None
    query: dict[str, str] = {"fen": fen}
    public_url = os.getenv("WEBAPP_PUBLIC_URL", "").rstrip("/")
    if public_url:
        query["api"] = public_url
    url = f"{miniapp_url}?{urlencode(query)}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Open Training Board", web_app=WebAppInfo(url=url)
                )
            ]
        ]
    )


@router.message(Command("attack-training"))
async def cmd_attack_training(message: Message, state: FSMContext):
    await state.clear()

    try:
        board = generate_attack_position()
        png_bytes = fen_to_png(board.fen())
    except Exception:
        logging.exception("Failed to generate attack training position")
        await message.answer("Could not generate a position. Please try again.")
        return

    fen = board.fen()
    keyboard = _webapp_keyboard(fen)

    await message.answer_photo(
        photo=BufferedInputFile(png_bytes, filename="board.png"),
        caption=Messages.ATTACK_QUESTION,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
