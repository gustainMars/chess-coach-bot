from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from bot.domain.messages import Messages
from bot.utils.miniapp import miniapp_url

router = Router()


def _learn_keyboard() -> InlineKeyboardMarkup | None:
    url = miniapp_url("learn")
    if not url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📚 Learn an Opening", web_app=WebAppInfo(url=url)
                )
            ]
        ]
    )


@router.message(Command("learn"))
async def cmd_learn(message: Message):
    keyboard = _learn_keyboard()
    if not keyboard:
        await message.answer(
            "⚠️ Opening learning is not available in this environment."
        )
        return
    await message.answer(
        Messages.LEARN_OPEN, reply_markup=keyboard, parse_mode="Markdown"
    )
