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

router = Router()


def _study_keyboard() -> InlineKeyboardMarkup | None:
    miniapp_url = os.getenv("STUDY_MINIAPP_URL", "").rstrip("/")
    if not miniapp_url:
        return None
    public_url = os.getenv("WEBAPP_PUBLIC_URL", "").rstrip("/")
    url = f"{miniapp_url}?api={public_url}" if public_url else miniapp_url
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Open Blunder Review", web_app=WebAppInfo(url=url)
                )
            ]
        ]
    )


async def _send_study_message(target: Message) -> None:
    keyboard = _study_keyboard()
    if not keyboard:
        await target.answer(
            "⚠️ Blunder review is not available in this environment."
        )
        return
    await target.answer(
        Messages.STUDY_OPEN, reply_markup=keyboard, parse_mode="Markdown"
    )


@router.message(Command("study"))
async def cmd_study(message: Message):
    await _send_study_message(message)


@router.callback_query(F.data == "open_study")
async def cb_open_study(callback: CallbackQuery):
    await callback.answer()
    await _send_study_message(callback.message)
