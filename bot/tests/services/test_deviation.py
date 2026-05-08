import pytest
import chess

from bot.domain.move_quality import MoveQuality
from unittest.mock import AsyncMock, MagicMock, patch


def test_classify_drop():
    from bot.services.deviation import _classify_drop

    assert _classify_drop(200) == MoveQuality.BLUNDER
    assert _classify_drop(150) == MoveQuality.BLUNDER
    assert _classify_drop(100) == MoveQuality.MISTAKE
    assert _classify_drop(50) == MoveQuality.MISTAKE
    assert _classify_drop(10) == MoveQuality.INACCURACY
    assert _classify_drop(0) is None
    assert _classify_drop(-10) is None


def test_parse_moves():
    from bot.services.deviation import parse_moves

    pgn_moves = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6"
    moves = parse_moves(pgn_moves)
    assert moves == ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"]

    pgn_moves = "1. d4 d5 2. c4 e6 3. Nc3 Nf6 4. 1-0"
    moves = parse_moves(pgn_moves)
    assert moves == ["d4", "d5", "c4", "e6", "Nc3", "Nf6"]

    pgn_moves = ""
    moves = parse_moves(pgn_moves)
    assert moves == []


def test_get_fen_from_moves():
    from bot.services.deviation import get_fen_from_moves

    fen_moves = get_fen_from_moves([])
    assert fen_moves == chess.STARTING_FEN

    fen_moves = get_fen_from_moves(["e4", "e5", "Nf3"])
    assert fen_moves == "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"


def test_find_deviation():
    from bot.services.deviation import find_deviation

    pgn_moves = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6"
    deviation = find_deviation(pgn_moves, "C60")
    assert deviation is None

    pgn_moves = "1. e4 e5 2. Nf3 Nc6 3. Bc4 a6"
    deviation = find_deviation(pgn_moves, "C60")
    assert deviation is not None
    assert deviation.move_number == 5
    assert deviation.user_move == "Bc4"
    assert deviation.expected_move == "Bb5"
    assert find_deviation("1. e4 e5", "Z99") is None
    assert find_deviation("", "C60") is None


@pytest.mark.asyncio
async def test_evaluate_deviation():
    from bot.services.deviation import evaluate_deviation
    from bot.domain.deviation_result import DeviationResult
    import chess.engine

    deviation = DeviationResult(
        move_number=3,
        user_move="Qh5",
        expected_move="Nf3",
        fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    )

    mock_transport = MagicMock()
    mock_engine = AsyncMock()
    mock_engine.analyse = AsyncMock(
        side_effect=[
            {"score": chess.engine.PovScore(chess.engine.Cp(100), chess.WHITE)},
            {"score": chess.engine.PovScore(chess.engine.Cp(-60), chess.WHITE)},
        ]
    )
    mock_engine.quit = AsyncMock()

    with patch(
        "bot.services.deviation.chess.engine.popen_uci",
        AsyncMock(return_value=(mock_transport, mock_engine)),
    ):
        quality = await evaluate_deviation(deviation)
        assert quality == MoveQuality.BLUNDER

    mock_engine.analyse = AsyncMock(
        side_effect=[
            {"score": chess.engine.PovScore(chess.engine.Mate(2), chess.WHITE)},
            {"score": chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)},
        ]
    )

    deviation = DeviationResult(
        move_number=2,
        user_move="e5",
        expected_move="c5",
        fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    )

    with patch(
        "bot.services.deviation.chess.engine.popen_uci",
        AsyncMock(return_value=(mock_transport, mock_engine)),
    ):
        quality = await evaluate_deviation(deviation)
        assert quality is None
