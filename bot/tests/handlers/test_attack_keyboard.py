import chess
import pytest
from aiogram.types import InlineKeyboardMarkup

from bot.handlers.attack_training import _build_board_keyboard, _piece_symbol

# Torre preta em a8, rei branco em e1, brancas a jogar
SIMPLE_FEN = "r7/8/8/8/8/8/8/4K3 w - - 0 1"
# Mesmo tabuleiro mas pretas a jogar (tabuleiro virado)
BLACK_TURN_FEN = "r7/8/8/8/8/8/8/4K3 b - - 0 1"


# ── _piece_symbol ──────────────────────────────────────────────────────────────

def test_piece_symbol_black_pieces():
    assert _piece_symbol(chess.Piece(chess.PAWN,   chess.BLACK)) == "♟"
    assert _piece_symbol(chess.Piece(chess.KNIGHT, chess.BLACK)) == "♞"
    assert _piece_symbol(chess.Piece(chess.BISHOP, chess.BLACK)) == "♝"
    assert _piece_symbol(chess.Piece(chess.ROOK,   chess.BLACK)) == "♜"
    assert _piece_symbol(chess.Piece(chess.QUEEN,  chess.BLACK)) == "♛"
    assert _piece_symbol(chess.Piece(chess.KING,   chess.BLACK)) == "♚"


def test_piece_symbol_white_pieces():
    assert _piece_symbol(chess.Piece(chess.PAWN,   chess.WHITE)) == "♙"
    assert _piece_symbol(chess.Piece(chess.KNIGHT, chess.WHITE)) == "♘"
    assert _piece_symbol(chess.Piece(chess.BISHOP, chess.WHITE)) == "♗"
    assert _piece_symbol(chess.Piece(chess.ROOK,   chess.WHITE)) == "♖"
    assert _piece_symbol(chess.Piece(chess.QUEEN,  chess.WHITE)) == "♕"
    assert _piece_symbol(chess.Piece(chess.KING,   chess.WHITE)) == "♔"


# ── _build_board_keyboard — estrutura geral ────────────────────────────────────

def test_returns_inline_keyboard_markup():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    assert isinstance(kb, InlineKeyboardMarkup)


def test_has_nine_rows():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    assert len(kb.inline_keyboard) == 9  # 8 ranks + 1 check


def test_each_board_row_has_eight_buttons():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    for row in kb.inline_keyboard[:8]:
        assert len(row) == 8


def test_last_row_is_check_button():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    check_row = kb.inline_keyboard[8]
    assert len(check_row) == 1
    assert check_row[0].callback_data == "atk:check"
    assert "Check" in check_row[0].text


# ── orientação do tabuleiro ────────────────────────────────────────────────────

def test_white_turn_top_row_is_rank_8():
    """Com brancas a jogar, rank 8 aparece na primeira linha (não virado)."""
    board = chess.Board(SIMPLE_FEN)  # brancas a jogar
    kb = _build_board_keyboard(board, selected=set())
    # a8 = file 0, rank 7 → primeira linha, primeira coluna deve ser toggle
    first_button = kb.inline_keyboard[0][0]
    assert first_button.callback_data == "atk:toggle:a8"


def test_white_turn_bottom_row_is_rank_1():
    """Com brancas a jogar, rank 1 aparece na última linha do board."""
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    # e1 = file 4, rank 0 → última linha do board (índice 7), coluna 4
    e1_button = kb.inline_keyboard[7][4]
    assert e1_button.callback_data == "atk:toggle:e1"


def test_black_turn_board_is_flipped():
    """Com pretas a jogar, h1 aparece no canto superior esquerdo (virado)."""
    board = chess.Board(BLACK_TURN_FEN)
    kb = _build_board_keyboard(board, selected=set())
    # Flipped: ranks 0..7, files 7..0 → primeira célula é h1 (vazio)
    first_button = kb.inline_keyboard[0][0]
    assert first_button.callback_data == "atk:noop"
    assert first_button.text == "·"


def test_black_turn_black_rook_appears_in_last_row():
    """Com pretas a jogar (virado), a8 aparece na última linha do board."""
    board = chess.Board(BLACK_TURN_FEN)
    kb = _build_board_keyboard(board, selected=set())
    # Flipped: ranks 0..7 → rank 7 (rank 8) está na última linha (índice 7)
    # files 7..0 → file 0 (coluna a) está na posição 7
    a8_button = kb.inline_keyboard[7][7]
    assert a8_button.callback_data == "atk:toggle:a8"


# ── conteúdo dos botões ────────────────────────────────────────────────────────

def test_empty_square_label_and_callback():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    # b8 está vazio (coluna 1 da primeira linha)
    b8_button = kb.inline_keyboard[0][1]
    assert b8_button.text == "·"
    assert b8_button.callback_data == "atk:noop"


def test_piece_square_has_toggle_callback():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    a8_button = kb.inline_keyboard[0][0]
    assert a8_button.callback_data == "atk:toggle:a8"


def test_unselected_piece_shows_unicode_symbol():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    a8_button = kb.inline_keyboard[0][0]
    assert a8_button.text == "♜"  # torre preta


def test_selected_piece_shows_checkmark_prefix():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected={"a8"})
    a8_button = kb.inline_keyboard[0][0]
    assert a8_button.text == "✅♜"


def test_white_king_shows_correct_symbol():
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected=set())
    e1_button = kb.inline_keyboard[7][4]
    assert e1_button.text == "♔"


def test_selected_does_not_affect_other_squares():
    """Selecionar a8 não deve alterar o label de outros squares."""
    board = chess.Board(SIMPLE_FEN)
    kb = _build_board_keyboard(board, selected={"a8"})
    e1_button = kb.inline_keyboard[7][4]
    assert e1_button.text == "♔"  # não deve ter ✅
    b8_button = kb.inline_keyboard[0][1]
    assert b8_button.text == "·"  # vazio continua vazio
