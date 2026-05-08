import logging

import chess
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.db import repository
from bot.db.database import SessionFactory
from bot.domain.messages import Messages
from bot.services.board_renderer import fen_to_png
from bot.services.move_validator import validate_move_input

router = Router()


class StudyStates(StatesGroup):
    waiting_for_move = State()


async def _send_study_card(message: Message, user_id: int, state: FSMContext) -> None:
    try:
        async with SessionFactory() as session:
            blunder, reset_happened = await repository.get_next_unreviewed_blunder(
                session, user_id
            )
    except Exception:
        logging.exception("DB error fetching blunder for user %s", user_id)
        await message.answer("Something went wrong. Please try again later.")
        return

    if blunder is None:
        await message.answer(Messages.STUDY_NO_BLUNDERS)
        return

    try:
        png_bytes = fen_to_png(blunder.fen)
    except Exception:
        logging.exception("Board rendering failed for FEN %s", blunder.fen)
        await message.answer("Could not render the board position. Please try again.")
        return

    caption = Messages.STUDY_QUESTION.format(
        opening_name=blunder.opening_name, quality=blunder.quality
    )
    if reset_happened:
        caption = Messages.STUDY_DECK_RESET + caption

    await message.answer_photo(
        photo=BufferedInputFile(png_bytes, filename="board.png"),
        caption=caption,
        parse_mode="Markdown",
    )
    await state.set_state(StudyStates.waiting_for_move)
    await state.update_data(blunder_id=blunder.id)


@router.message(Command("study"))
async def cmd_study(message: Message, state: FSMContext):
    await state.clear()
    await _send_study_card(message, message.from_user.id, state)


@router.callback_query(F.data == "open_study")
async def cb_open_study(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await _send_study_card(callback.message, callback.from_user.id, state)


@router.message(StudyStates.waiting_for_move)
async def handle_study_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    blunder_id = data.get("blunder_id")

    try:
        async with SessionFactory() as session:
            blunder = await repository.get_blunder_by_id(session, blunder_id)
            if blunder is None:
                await state.clear()
                await message.answer(
                    "Could not find the current question. Use /study to start again."
                )
                return

            user_move = validate_move_input(message.text or "", blunder.fen)
            if user_move is None:
                await message.answer(Messages.STUDY_INVALID_MOVE, parse_mode="Markdown")
                return

            board = chess.Board(blunder.fen)
            expected = board.parse_san(blunder.expected_move)

            if user_move == expected:
                reply = Messages.STUDY_CORRECT.format(expected=blunder.expected_move)
            else:
                reply = Messages.STUDY_WRONG.format(
                    user_move=message.text.strip(), expected=blunder.expected_move
                )

            await repository.mark_blunder_reviewed(session, blunder.id)

    except Exception:
        logging.exception(
            "Error processing study answer for user %s", message.from_user.id
        )
        await state.clear()
        await message.answer("Something went wrong. Use /study to try again.")
        return

    await state.clear()
    await message.answer(reply, parse_mode="Markdown")
