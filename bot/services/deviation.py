import logging
import re

import chess
import csv
from pathlib import Path
from bot.domain.deviation_result import DeviationResult
import os

from bot.domain.messages import Messages
from bot.domain.move_quality import MoveQuality

ECO_PATH = Path(__file__).parent.parent.parent / "data" / "eco.tsv"


def _strip_pgn_headers(pgn: str) -> str:
    """Remove PGN header tags and inline comments, leaving only move tokens."""
    pgn = re.sub(r'\[[^\]]*\]', '', pgn)   # [Tag "Value"]
    pgn = re.sub(r'\{[^}]*\}', '', pgn)    # { comments and %clk annotations }
    return pgn


def parse_moves(pgn: str) -> list[str]:
    pgn = _strip_pgn_headers(pgn)
    board = chess.Board()
    moves = []
    for token in pgn.split():
        if token[0].isdigit() or token[0] == '$':
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


async def find_blunders_in_game(
    pgn_moves: str,
    session,
    max_half_moves: int = 20,
) -> list[tuple[DeviationResult, MoveQuality]]:
    """
    Walk through the first max_half_moves of a game and detect blunders using
    the Lichess Opening Explorer (with SQLite cache) + Stockfish evaluation.

    A move is a blunder when:
    1. It is absent from the Explorer's top-N moves for that position, AND
    2. Stockfish eval drops by more than the blunder/mistake threshold.
    """
    from bot.services.lichess_explorer import get_top_moves
    from bot.db import repository

    moves = parse_moves(pgn_moves)
    if not moves:
        return []

    board = chess.Board()
    results: list[tuple[DeviationResult, MoveQuality]] = []

    for i, san in enumerate(moves[:max_half_moves]):
        fen_before = board.fen()

        cached = await repository.get_cached_explorer_moves(session, fen_before)
        if cached is None:
            top_ucis = await get_top_moves(fen_before)
            await repository.save_cached_explorer_moves(session, fen_before, top_ucis)
        else:
            top_ucis = cached

        move = board.parse_san(san)
        board.push(move)

        if not top_ucis or move.uci() in top_ucis:
            continue  # theory move or no explorer data

        top_san = _uci_to_san(chess.Board(fen_before), top_ucis[0])
        deviation = DeviationResult(
            move_number=i + 1,
            user_move=san,
            expected_move=top_san,
            fen=fen_before,
        )
        quality = await evaluate_deviation(deviation)
        if quality in (MoveQuality.BLUNDER, MoveQuality.MISTAKE):
            results.append((deviation, quality))

    return results


def _uci_to_san(board: chess.Board, uci: str) -> str:
    try:
        return board.san(chess.Move.from_uci(uci))
    except Exception:
        return uci


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
