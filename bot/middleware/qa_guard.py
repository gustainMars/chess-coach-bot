import os
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

_IS_QA = os.getenv("BOT_ENV", "").lower() == "qa"
_ALLOWED_ID = int(os.getenv("ALLOWED_USER_ID", "0"))


class QAGuardMiddleware(BaseMiddleware):
    """
    When BOT_ENV=qa, drops every update that doesn't come from ALLOWED_USER_ID.
    No-op in any other environment.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not _IS_QA:
            return await handler(event, data)

        user: User | None = data.get("event_from_user")

        # Unknown sender or authorised user — let through
        if user is None or user.id == _ALLOWED_ID:
            return await handler(event, data)

        # Silently drop everything except interactive events that deserve a reply
        if isinstance(event, Message):
            await event.answer("⛔ QA environment — private access only.")
        elif isinstance(event, CallbackQuery):
            await event.answer(
                "⛔ QA environment — private access only.", show_alert=True
            )

        return None
