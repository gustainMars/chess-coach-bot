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
from bot.utils.miniapp import miniapp_url

router = Router()


def _review_keyboard() -> InlineKeyboardMarkup | None:
    url = miniapp_url("study")
    if not url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Review My Blunders", web_app=WebAppInfo(url=url)
                )
            ]
        ]
    )


async def _send_review_message(target: Message) -> None:
    keyboard = _review_keyboard()
    if not keyboard:
        await target.answer(
            "⚠️ Blunder review is not available in this environment."
        )
        return
    await target.answer(
        Messages.STUDY_OPEN, reply_markup=keyboard, parse_mode="Markdown"
    )


@router.message(Command("review_blunders"))
async def cmd_review_blunders(message: Message):
    await _send_review_message(message)


@router.callback_query(F.data == "open_study")
async def cb_open_study(callback: CallbackQuery):
    await callback.answer()
    await _send_review_message(callback.message)
