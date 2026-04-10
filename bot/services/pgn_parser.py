import chess.pgn
import io
from bot.services.opening import find_opening

def parse_game(pgn_str: str) -> dict:
    """Extracts relevant information from a PGN match."""
    game = chess.pgn.read_game(io.StringIO(pgn_str))
    
    if not game:
        return None
    
    board = game.board()
    moves = []
    
    for i, move in enumerate(game.mainline_moves()):
        if i >= 20:
            break
        san = board.san(move)
        moves.append(san)
        board.push(move)
    
    pgn_moves = ""
    for i, move in enumerate(moves):
        if i % 2 == 0:
            pgn_moves += f"{(i // 2) + 1}"
        pgn_moves += f"{move} "
        
    opening = find_opening(pgn_moves.strip())
    
    return {
        "opening_eco": opening["eco"],
        "opening_name": opening["name"],
        "moves": moves,
        "pgn_moves": pgn_moves.strip(),
    }