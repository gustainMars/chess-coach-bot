import chess

from bot.services.attack_generator import (
    generate_attack_position,
    get_capturable_squares,
    validate_capture_selection,
)

# Both sides have captures: White exd5, Black dxe4
MUTUAL_CAPTURE_FEN = "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3"

# Black's turn — white pawn e4 attacks f5, white pawn g6 attacks h7
BLACK_TURN_FEN = "6k1/7p/6P1/5p2/4P3/8/8/6K1 b - - 0 1"

# Starting position — no captures at all
NO_CAPTURE_FEN = chess.STARTING_FEN


# ── get_capturable_squares ────────────────────────────────────────────────────


def test_capturable_includes_both_sides_attacks():
    """d5 (attacked by white e4) and e4 (attacked by black d5) both capturable."""
    board = chess.Board(MUTUAL_CAPTURE_FEN)
    squares = get_capturable_squares(board)
    assert chess.D5 in squares  # white pawn e4 attacks d5
    assert chess.E4 in squares  # black pawn d5 attacks e4


def test_capturable_finds_squares_when_not_current_player_turn():
    """White pawns attack black pawns f5 and h7 even when it's Black's turn."""
    board = chess.Board(BLACK_TURN_FEN)
    assert board.turn == chess.BLACK
    squares = get_capturable_squares(board)
    assert chess.F5 in squares  # white pawn e4 attacks f5
    assert chess.H7 in squares  # white pawn g6 attacks h7


def test_get_capturable_squares_empty_when_no_captures():
    board = chess.Board(NO_CAPTURE_FEN)
    assert get_capturable_squares(board) == set()


def test_get_capturable_squares_returns_set_of_squares():
    board = chess.Board(MUTUAL_CAPTURE_FEN)
    squares = get_capturable_squares(board)
    assert isinstance(squares, set)
    for sq in squares:
        assert isinstance(sq, int)
        assert 0 <= sq <= 63


# ── validate_capture_selection ────────────────────────────────────────────────


def test_validate_all_correct_returns_empty_sets():
    capturable = {"e4", "d5"}
    selected = {"e4", "d5"}
    missed, extra = validate_capture_selection(capturable, selected)
    assert missed == set()
    assert extra == set()


def test_validate_missed_squares():
    capturable = {"e4", "d5", "f3"}
    selected = {"e4"}
    missed, extra = validate_capture_selection(capturable, selected)
    assert missed == {"d5", "f3"}
    assert extra == set()


def test_validate_extra_squares():
    capturable = {"e4"}
    selected = {"e4", "g7"}
    missed, extra = validate_capture_selection(capturable, selected)
    assert missed == set()
    assert extra == {"g7"}


def test_validate_missed_and_extra():
    capturable = {"e4", "d5"}
    selected = {"e4", "f6"}
    missed, extra = validate_capture_selection(capturable, selected)
    assert missed == {"d5"}
    assert extra == {"f6"}


def test_validate_empty_selection_all_missed():
    capturable = {"e4", "d5"}
    missed, extra = validate_capture_selection(capturable, set())
    assert missed == {"e4", "d5"}
    assert extra == set()


def test_validate_empty_capturable_all_extra():
    selected = {"e4", "d5"}
    missed, extra = validate_capture_selection(set(), selected)
    assert missed == set()
    assert extra == {"e4", "d5"}


def test_validate_both_empty():
    missed, extra = validate_capture_selection(set(), set())
    assert missed == set()
    assert extra == set()


# ── generate_attack_position ──────────────────────────────────────────────────


def test_generate_returns_board():
    assert isinstance(generate_attack_position(), chess.Board)


def test_generate_has_min_captures():
    board = generate_attack_position(min_captures=2)
    assert len(get_capturable_squares(board)) >= 2


def test_generate_attack_position_not_in_check():
    assert not generate_attack_position().is_check()


def test_generate_respects_min_max():
    board = generate_attack_position(min_captures=2, max_captures=4)
    assert 2 <= len(get_capturable_squares(board)) <= 4


def test_generate_attack_position_is_valid_position():
    assert generate_attack_position().is_valid()
