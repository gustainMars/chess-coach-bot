import logging

import chess
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.domain.messages import Messages
from bot.services.attack_generator import generate_attack_position, get_capturable_squares
from bot.services.board_renderer import fen_to_png

router = Router()

_PIECE_SYMBOLS = {
    chess.PAWN: ("♟", "♙"),
    chess.KNIGHT: ("♞", "♘"),
    chess.BISHOP: ("♝", "♗"),
    chess.ROOK: ("♜", "♖"),
    chess.QUEEN: ("♛", "♕"),
    chess.KING: ("♚", "♔"),
}


class AttackTrainingStates(StatesGroup):
    selecting = State()


def _piece_label(board: chess.Board, square: int) -> str:
    piece = board.piece_at(square)
    if piece is None:
        return chess.square_name(square)
    black_sym, white_sym = _PIECE_SYMBOLS[piece.piece_type]
    sym = white_sym if piece.color == chess.WHITE else black_sym
    return f"{sym} {chess.square_name(square)}"


def _build_keyboard(board: chess.Board, selected: set[str]) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    for square in chess.SQUARES:
        if board.piece_at(square) is None:
            continue
        sq_name = chess.square_name(square)
        label = _piece_label(board, square)
        is_selected = sq_name in selected
        display = f"✅ {label}" if is_selected else f"⬜ {label}"
        buttons.append(
            InlineKeyboardButton(text=display, callback_data=f"atk:toggle:{sq_name}")
        )

    rows = [buttons[i : i + 4] for i in range(0, len(buttons), 4)]
    rows.append([InlineKeyboardButton(text="Check ✅", callback_data="atk:check")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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

    capturable = {chess.square_name(sq) for sq in get_capturable_squares(board)}
    keyboard = _build_keyboard(board, selected=set())

    sent = await message.answer_photo(
        photo=BufferedInputFile(png_bytes, filename="board.png"),
        caption=Messages.ATTACK_QUESTION,
        parse_mode="Markdown",
    )
    await message.answer("Select pieces:", reply_markup=keyboard)

    await state.set_state(AttackTrainingStates.selecting)
    await state.update_data(
        fen=board.fen(),
        capturable=list(capturable),
        selected=[],
        keyboard_msg_id=sent.message_id + 1,
    )


@router.callback_query(F.data.startswith("atk:"), AttackTrainingStates.selecting)
async def handle_attack_callback(query: CallbackQuery, state: FSMContext):
    parts = query.data.split(":")
    action = parts[1]

    data = await state.get_data()
    fen = data["fen"]
    capturable: set[str] = set(data["capturable"])
    selected: set[str] = set(data["selected"])
    board = chess.Board(fen)

    if action == "toggle":
        sq_name = parts[2]
        if sq_name in selected:
            selected.discard(sq_name)
        else:
            selected.add(sq_name)

        await state.update_data(selected=list(selected))
        keyboard = _build_keyboard(board, selected)
        await query.message.edit_reply_markup(reply_markup=keyboard)
        await query.answer()
        return

    if action == "check":
        missed = capturable - selected
        extra = selected - capturable

        if not missed and not extra:
            await state.clear()
            await query.message.edit_reply_markup(reply_markup=None)
            await query.message.answer(
                Messages.ATTACK_CORRECT.format(count=len(capturable)),
                parse_mode="Markdown",
            )
        elif missed and extra:
            missed_str = ", ".join(sorted(missed))
            extra_str = ", ".join(sorted(extra))
            await query.answer(
                Messages.ATTACK_WRONG_BOTH.format(missed=missed_str, extra=extra_str),
                show_alert=True,
            )
        elif missed:
            await query.answer(
                Messages.ATTACK_WRONG_MISSED.format(missed=", ".join(sorted(missed))),
                show_alert=True,
            )
        else:
            await query.answer(
                Messages.ATTACK_WRONG_EXTRA.format(extra=", ".join(sorted(extra))),
                show_alert=True,
            )
