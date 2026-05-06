import chess


def validate_move_input(user_input: str, fen: str) -> chess.Move | None:
    board = chess.Board(fen)
    text = user_input.strip()
    try:
        return board.parse_san(text)
    except (chess.InvalidMoveError, chess.AmbiguousMoveError, chess.IllegalMoveError):
        pass
    try:
        move = chess.Move.from_uci(text.lower())
        if move in board.legal_moves:
            return move
    except (chess.InvalidMoveError, ValueError):
        pass
    return None
