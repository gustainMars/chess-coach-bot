import chess
import pytest

from bot.services.attack_generator import generate_attack_position, get_capturable_squares

# FEN where White can capture d5 (exd5) and Black can capture e4 (dxe4)
MULTI_CAPTURE_FEN = "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3"

# Starting position — no captures available
NO_CAPTURE_FEN = chess.STARTING_FEN


def test_get_capturable_squares_finds_captures():
    board = chess.Board(MULTI_CAPTURE_FEN)
    squares = get_capturable_squares(board)
    assert len(squares) >= 1
    assert chess.D5 in squares  # White can capture on d5


def test_get_capturable_squares_empty_when_no_captures():
    board = chess.Board(NO_CAPTURE_FEN)
    squares = get_capturable_squares(board)
    assert len(squares) == 0


def test_get_capturable_squares_returns_set_of_squares():
    board = chess.Board(MULTI_CAPTURE_FEN)
    squares = get_capturable_squares(board)
    assert isinstance(squares, set)
    for sq in squares:
        assert isinstance(sq, int)
        assert 0 <= sq <= 63


def test_generate_attack_position_returns_board():
    board = generate_attack_position()
    assert isinstance(board, chess.Board)


def test_generate_attack_position_has_captures():
    board = generate_attack_position(min_captures=2)
    capturable = get_capturable_squares(board)
    assert len(capturable) >= 2


def test_generate_attack_position_not_in_check():
    board = generate_attack_position()
    assert not board.is_check()


def test_generate_attack_position_respects_min_max():
    board = generate_attack_position(min_captures=2, max_captures=4)
    capturable = get_capturable_squares(board)
    assert 2 <= len(capturable) <= 4


def test_generate_attack_position_is_valid_position():
    board = generate_attack_position()
    assert board.is_valid()
