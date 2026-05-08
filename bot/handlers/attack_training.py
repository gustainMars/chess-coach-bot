import os

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from bot.domain.messages import Messages
from bot.services.attack_generator import (
    generate_attack_position,
    get_capturable_squares,
    validate_capture_selection,
)
from bot.services.board_renderer import fen_to_png

router = Router()


def _attack_keyboard() -> InlineKeyboardMarkup | None:
    miniapp_url = os.getenv("MINIAPP_URL", "").rstrip("/")
    if not miniapp_url:
        return None
    public_url = os.getenv("WEBAPP_PUBLIC_URL", "").rstrip("/")
    url = f"{miniapp_url}?api={public_url}" if public_url else miniapp_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Open Attack Training", web_app=WebAppInfo(url=url)
                )
            ]
        ]
    )


async def _send_attack_message(target: Message) -> None:
    keyboard = _attack_keyboard()
    if not keyboard:
        await target.answer(
            "⚠️ Attack training is not available in this environment."
        )
        return
    await target.answer(
        Messages.ATTACK_QUESTION, reply_markup=keyboard, parse_mode="Markdown"
    )


@router.message(Command("attack"))
async def cmd_attack(message: Message):
    await _send_attack_message(message)


@router.callback_query(F.data == "open_attack")
async def cb_open_attack(callback: CallbackQuery):
    await callback.answer()
    await _send_attack_message(callback.message)
