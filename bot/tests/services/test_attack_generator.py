import chess

from bot.services.attack_generator import generate_attack_position, get_capturable_squares

# FEN where White can capture d5 (exd5) and Black can capture e4 (dxe4)
MULTI_CAPTURE_FEN = "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3"

# Starting position — no captures available
NO_CAPTURE_FEN = chess.STARTING_FEN


# ── get_capturable_squares ────────────────────────────────────────────────────


def test_capturable_includes_both_sides_attacks():
    """d5 (attacked by white e4) and e4 (attacked by black d5) both capturable."""
    board = chess.Board(MUTUAL_CAPTURE_FEN)
    squares = get_capturable_squares(board)
    assert chess.D5 in squares  # white pawn e4 attacks d5
    assert chess.E4 in squares  # black pawn d5 attacks e4


def test_capturable_finds_squares_when_not_current_player_turn():
    """White pawns e4 and g6 attack black pawns f5 and h7 even when it's Black's turn."""
    board = chess.Board(BLACK_TURN_FEN)
    assert board.turn == chess.BLACK
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
