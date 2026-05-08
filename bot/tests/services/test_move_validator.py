import chess

from bot.services.move_validator import validate_move_input

STARTING_FEN = chess.STARTING_FEN

# FEN where e-pawn is on e7, ready to promote (White to move)
PROMOTION_FEN = "8/4P3/8/8/8/8/8/4K1k1 w - - 0 1"

# FEN where White can castle kingside
CASTLING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1"


def test_valid_san_accepted():
    move = validate_move_input("e4", STARTING_FEN)
    assert move is not None
    assert move == chess.Move.from_uci("e2e4")


def test_valid_uci_accepted():
    move = validate_move_input("e2e4", STARTING_FEN)
    assert move is not None
    assert move == chess.Move.from_uci("e2e4")


def test_invalid_string_returns_none():
    move = validate_move_input("xpto", STARTING_FEN)
    assert move is None


def test_illegal_move_returns_none():
    # Pawn can't move backwards
    move = validate_move_input("e2e1", STARTING_FEN)
    assert move is None


def test_empty_string_returns_none():
    move = validate_move_input("", STARTING_FEN)
    assert move is None


def test_whitespace_only_returns_none():
    move = validate_move_input("   ", STARTING_FEN)
    assert move is None


def test_castling_san_accepted():
    move = validate_move_input("O-O", CASTLING_FEN)
    assert move is not None
    assert move == chess.Move.from_uci("e1g1")


def test_promotion_san_accepted():
    move = validate_move_input("e8=Q", PROMOTION_FEN)
    assert move is not None
    assert move.promotion == chess.QUEEN


def test_promotion_uci_accepted():
    move = validate_move_input("e7e8q", PROMOTION_FEN)
    assert move is not None
    assert move.promotion == chess.QUEEN


def test_strips_surrounding_whitespace():
    move = validate_move_input("  e4  ", STARTING_FEN)
    assert move is not None
