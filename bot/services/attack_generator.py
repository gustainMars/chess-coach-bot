import random

import chess


def get_capturable_squares(board: chess.Board) -> set[int]:
    """Return squares of pieces that can be captured by either side."""
    squares: set[int] = set()
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        if board.attackers(not piece.color, square):
            squares.add(square)
    return squares


def validate_capture_selection(
    capturable: set[str], selected: set[str]
) -> tuple[set[str], set[str]]:
    """Return (missed, extra) for the user's selection of square names."""
    return capturable - selected, selected - capturable


def generate_attack_position(min_captures: int = 2, max_captures: int = 5) -> chess.Board:
    for _ in range(50):
        board = chess.Board()
        num_moves = random.randint(14, 26)
        for _ in range(num_moves):
            legal = list(board.legal_moves)
            if not legal or board.is_game_over():
                break
            board.push(random.choice(legal))
        if board.is_check() or board.is_game_over():
            continue
        capturable = get_capturable_squares(board)
        if min_captures <= len(capturable) <= max_captures:
            return board
    return _fallback_position()


def _fallback_position() -> chess.Board:
    # Sicilian middlegame with multiple captures available
    board = chess.Board("r1bqkb1r/pp3ppp/2nppn2/8/3NP3/2N1B3/PPP2PPP/R2QKB1R w KQkq - 0 8")
    return board
