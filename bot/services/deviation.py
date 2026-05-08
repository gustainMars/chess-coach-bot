import logging

import chess
import csv
from pathlib import Path
from bot.domain.deviation_result import DeviationResult
import os

from bot.domain.messages import Messages
from bot.domain.move_quality import MoveQuality

ECO_PATH = Path(__file__).parent.parent.parent / "data" / "eco.tsv"


def parse_moves(pgn_moves: str) -> list[str]:
    board = chess.Board()
    moves = []
    for token in pgn_moves.split():
        if token[0].isdigit():
            continue
        if token == "*" or token.endswith("-"):
            continue
        try:
            move = board.parse_san(token)
            moves.append(token)
            board.push(move)
        except Exception:
            logging.warning(Messages.DEBUG_INVALID_MOVE.format(token=token))
            break
    return moves


def get_opening_moves(eco: str) -> str | None:
    with open(ECO_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["eco"] == eco:
                return parse_moves(row["pgn"])
    return None


def get_fen_from_moves(moves: list[str]) -> str:
    board = chess.Board()
    for move in moves:
        board.push_san(move)
    return board.fen()


def find_deviation(pgn_moves: str, opening_eco: str) -> DeviationResult | None:
    moves = parse_moves(pgn_moves)

    if not moves:
        return None

    opening_moves = get_opening_moves(opening_eco)
    print(opening_moves)
    if not opening_moves:
        return None

    for i in range(min(len(moves), len(opening_moves))):
        if moves[i] != opening_moves[i]:
            return DeviationResult(
                move_number=i + 1,
                user_move=moves[i],
                expected_move=opening_moves[i],
                fen=get_fen_from_moves(moves[:i]),
            )

    return None


def _classify_drop(drop: int) -> MoveQuality | None:
    if drop >= 150:
        return MoveQuality.BLUNDER
    elif drop >= 50:
        return MoveQuality.MISTAKE
    elif drop > 0:
        return MoveQuality.INACCURACY
    else:
        return None


async def evaluate_deviation(deviation: DeviationResult) -> str:
    board_before = chess.Board(deviation.fen)
    is_white = board_before.turn == chess.WHITE
    transport, engine = await chess.engine.popen_uci(
        os.getenv("STOCKFISH_PATH", "stockfish")
    )

    try:
        eval_before = await engine.analyse(board_before, chess.engine.Limit(depth=15))

        board_after = board_before.copy()
        board_after.push_san(deviation.user_move)
        eval_after = await engine.analyse(board_after, chess.engine.Limit(depth=15))

        pov = chess.WHITE if is_white else chess.BLACK
        score_before = eval_before["score"].pov(pov).score()
        score_after = eval_after["score"].pov(pov).score()

        if score_before is None or score_after is None:
            return None

        return _classify_drop(score_before - score_after)
    finally:
        await engine.quit()
