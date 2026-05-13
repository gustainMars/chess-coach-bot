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


def test_parse_moves_with_full_chesscom_pgn():
    """parse_moves must handle the full PGN format returned by chess.com API.

    chess.com returns a complete PGN string with header tags ([Event], [Site],
    [ECO], etc.) and inline clock annotations ({ [%clk 0:09:58.2] }).
    Previously, parse_moves received this full string and immediately stopped
    on the first token '[Event', producing an empty list for every game.
    """
    from bot.services.deviation import parse_moves

    full_pgn = (
        '[Event "Live Chess"]\n'
        '[Site "Chess.com"]\n'
        '[Date "2026.05.11"]\n'
        '[White "player1"]\n'
        '[Black "player2"]\n'
        '[Result "1-0"]\n'
        '[ECO "C60"]\n'
        '[ECOUrl "https://www.chess.com/openings/Ruy-Lopez-Opening"]\n'
        '\n'
        '1. e4 { [%clk 0:09:58.2] } e5 { [%clk 0:09:57.4] } '
        '2. Nf3 { [%clk 0:09:55.1] } Nc6 { [%clk 0:09:54.8] } '
        '3. Bb5 { [%clk 0:09:52.0] } a6 { [%clk 0:09:51.3] } 1-0\n'
    )
    moves = parse_moves(full_pgn)
    assert moves == ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"]


def test_parse_moves_strips_nag_annotations():
    """Numeric Annotation Glyphs ($1, $2 …) must be silently skipped."""
    from bot.services.deviation import parse_moves

    pgn = "1. e4 $1 e5 $2 2. Nf3 Nc6"
    assert parse_moves(pgn) == ["e4", "e5", "Nf3", "Nc6"]


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
async def test_find_blunders_in_game_detects_blunder():
    from bot.services.deviation import find_blunders_in_game
    from bot.domain.deviation_result import DeviationResult
    import chess.engine

    # pgn has 4 moves: e4, e5, Qh5, Nc6
    # Qh5 is the blunder (big score drop); Nc6 is a neutral reply
    pgn = "1. e4 e5 2. Qh5 Nc6"

    mock_transport = MagicMock()
    mock_engine = AsyncMock()
    def _s(cp):
        return {"score": chess.engine.PovScore(chess.engine.Cp(cp), chess.WHITE)}

    mock_engine.analyse = AsyncMock(side_effect=[
        _s(20),  _s(20),   # e4: no drop
        _s(-20), _s(-20),  # e5: no drop
        _s(20),  _s(-130), # Qh5: drop 150 → BLUNDER
        _s(130), _s(130),  # Nc6: neutral
    ])
    mock_move = MagicMock()
    mock_move.move = chess.Move.from_uci("g1f3")
    mock_engine.play = AsyncMock(return_value=mock_move)
    mock_engine.quit = AsyncMock()

    with patch(
        "bot.services.deviation.chess.engine.popen_uci",
        AsyncMock(return_value=(mock_transport, mock_engine)),
    ):
        results = await find_blunders_in_game(pgn, session=None)

    assert len(results) == 1
    deviation, quality = results[0]
    assert quality == MoveQuality.BLUNDER
    assert deviation.user_move == "Qh5"
    assert deviation.move_number == 3


@pytest.mark.asyncio
async def test_find_blunders_in_game_returns_all_blunders_sorted():
    """All blunders in a game are returned (not just the first), sorted worst-first."""
    from bot.services.deviation import find_blunders_in_game
    import chess.engine

    # e4 (white, pov=WHITE): before=300, after=0, drop=300 → BLUNDER
    # e5 (black, pov=BLACK): PovScore(-50,W).pov(B)=50, PovScore(150,W).pov(B)=-150
    #   drop = 50 - (-150) = 200 → BLUNDER
    pgn = "1. e4 e5"

    mock_transport = MagicMock()
    mock_engine = AsyncMock()

    def _s(cp):
        return {"score": chess.engine.PovScore(chess.engine.Cp(cp), chess.WHITE)}

    mock_engine.analyse = AsyncMock(side_effect=[
        _s(300), _s(0),    # e4: drop 300
        _s(-50), _s(150),  # e5: drop 200 from black's pov
    ])
    mock_move = MagicMock()
    mock_move.move = chess.Move.from_uci("g1f3")
    mock_engine.play = AsyncMock(return_value=mock_move)
    mock_engine.quit = AsyncMock()

    with patch(
        "bot.services.deviation.chess.engine.popen_uci",
        AsyncMock(return_value=(mock_transport, mock_engine)),
    ):
        results = await find_blunders_in_game(pgn, session=None)

    assert len(results) == 2
    assert all(q in (MoveQuality.BLUNDER, MoveQuality.MISTAKE) for _, q in results)
    # Worst blunder (drop=300, e4) must come first
    assert results[0][0].user_move == "e4"


@pytest.mark.asyncio
async def test_find_blunders_in_game_returns_empty_on_no_blunder():
    from bot.services.deviation import find_blunders_in_game
    import chess.engine

    pgn = "1. e4 e5 2. Nf3 Nc6"

    mock_transport = MagicMock()
    mock_engine = AsyncMock()
    mock_engine.analyse = AsyncMock(return_value={
        "score": chess.engine.PovScore(chess.engine.Cp(20), chess.WHITE)
    })
    mock_engine.quit = AsyncMock()

    with patch(
        "bot.services.deviation.chess.engine.popen_uci",
        AsyncMock(return_value=(mock_transport, mock_engine)),
    ):
        results = await find_blunders_in_game(pgn, session=None)

    assert results == []


@pytest.mark.asyncio
async def test_find_blunders_in_game_empty_pgn():
    from bot.services.deviation import find_blunders_in_game

    results = await find_blunders_in_game("", session=None)
    assert results == []


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
