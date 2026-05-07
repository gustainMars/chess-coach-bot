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
from bot.services.attack_generator import (
    generate_attack_position,
    get_capturable_squares,
    validate_capture_selection,
)
from bot.services.board_renderer import fen_to_png

router = Router()

_PIECE_SYMBOLS: dict[int, tuple[str, str]] = {
    chess.PAWN:   ("♟", "♙"),
    chess.KNIGHT: ("♞", "♘"),
    chess.BISHOP: ("♝", "♗"),
    chess.ROOK:   ("♜", "♖"),
    chess.QUEEN:  ("♛", "♕"),
    chess.KING:   ("♚", "♔"),
}


class AttackTrainingStates(StatesGroup):
    selecting = State()


def _piece_symbol(piece: chess.Piece) -> str:
    black_sym, white_sym = _PIECE_SYMBOLS[piece.piece_type]
    return white_sym if piece.color == chess.WHITE else black_sym


def _build_board_keyboard(
    board: chess.Board, selected: set[str]
) -> InlineKeyboardMarkup:
    """Build an 8×8 InlineKeyboard that mirrors the board orientation."""
    flipped = board.turn == chess.BLACK
    ranks = range(7, -1, -1) if not flipped else range(0, 8)
    files = range(0, 8) if not flipped else range(7, -1, -1)

    rows: list[list[InlineKeyboardButton]] = []
    for rank in ranks:
        row: list[InlineKeyboardButton] = []
        for file in files:
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            sq_name = chess.square_name(square)

            if piece is None:
                label = "·"
                cb = "atk:noop"
            else:
                sym = _piece_symbol(piece)
                label = f"✅{sym}" if sq_name in selected else sym
                cb = f"atk:toggle:{sq_name}"

            row.append(InlineKeyboardButton(text=label, callback_data=cb))
        rows.append(row)

    rows.append([InlineKeyboardButton(text="✅ Check", callback_data="atk:check")])
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
    keyboard = _build_board_keyboard(board, selected=set())

    await message.answer_photo(
        photo=BufferedInputFile(png_bytes, filename="board.png"),
        caption=Messages.ATTACK_QUESTION,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    await state.set_state(AttackTrainingStates.selecting)
    await state.update_data(
        fen=board.fen(),
        capturable=list(capturable),
        selected=[],
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

    if action == "noop":
        await query.answer()
        return

    if action == "toggle":
        sq_name = parts[2]
        selected.discard(sq_name) if sq_name in selected else selected.add(sq_name)
        await state.update_data(selected=list(selected))
        await query.message.edit_reply_markup(
            reply_markup=_build_board_keyboard(board, selected)
        )
        await query.answer()
        return

    if action == "check":
        missed, extra = validate_capture_selection(capturable, selected)

        if not missed and not extra:
            await state.clear()
            await query.message.edit_reply_markup(reply_markup=None)
            await query.message.answer(
                Messages.ATTACK_CORRECT.format(count=len(capturable)),
                parse_mode="Markdown",
            )
        elif missed and extra:
            await query.answer(
                Messages.ATTACK_WRONG_BOTH.format(
                    missed=", ".join(sorted(missed)),
                    extra=", ".join(sorted(extra)),
                ),
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
