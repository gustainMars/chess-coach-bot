import chess
import chess.svg
import cairosvg


def fen_to_png(fen: str) -> bytes:
    board = chess.Board(fen)
    flipped = board.turn == chess.BLACK
    svg = chess.svg.board(board, flipped=flipped)
    return cairosvg.svg2png(
        bytestring=svg.encode(), output_width=512, output_height=512
    )
