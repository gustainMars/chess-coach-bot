import pytest
from bot.services.stats import aggregate_openings, top_openings
from bot.domain.opening import Outcome, OpeningStat


def make_game(white_username: str, black_username: str, white_result: str, eco: str, eco_url: str) -> dict:
    pgn = (
        f'[White "{white_username}"]\n'
        f'[Black "{black_username}"]\n'
        f'[ECO "{eco}"]\n'
        f'[ECOUrl "https://www.chess.com/openings/{eco_url}"]\n'
        "\n1. e4 e5 *"
    )
    return {
        "white": {"username": white_username, "result": white_result},
        "black": {"username": black_username, "result": "checkmated" if white_result == "win" else "win"},
        "pgn": pgn,
    }


def test_aggregate_openings_win_as_white():
    games = [make_game("alice", "bob", "win", "C60", "Ruy-Lopez-Opening")]
    white, black = aggregate_openings(games, "alice")
    assert white["C60"][Outcome.WIN] == 1
    assert white["C60"][Outcome.LOSS] == 0
    assert len(black) == 0


def test_aggregate_openings_loss_as_black():
    games = [make_game("alice", "bob", "win", "D00", "Queens-Pawn-Opening")]
    white, black = aggregate_openings(games, "bob")
    assert black["D00"][Outcome.LOSS] == 1
    assert black["D00"][Outcome.WIN] == 0
    assert len(white) == 0


def test_aggregate_openings_draw():
    pgn = (
        '[White "alice"]\n[Black "bob"]\n'
        '[ECO "A00"]\n[ECOUrl "https://www.chess.com/openings/Uncommon-Opening"]\n'
        "\n1. a4 a5 *"
    )
    game = {
        "white": {"username": "alice", "result": "agreed"},
        "black": {"username": "bob", "result": "agreed"},
        "pgn": pgn,
    }
    white, black = aggregate_openings([game], "alice")
    assert white["A00"][Outcome.DRAW] == 1


def test_aggregate_openings_skips_empty_pgn():
    game = {
        "white": {"username": "alice", "result": "win"},
        "black": {"username": "bob", "result": "checkmated"},
        "pgn": "",
    }
    white, black = aggregate_openings([game], "alice")
    assert len(white) == 0


def test_aggregate_openings_case_insensitive_username():
    games = [make_game("Alice", "bob", "win", "C60", "Ruy-Lopez-Opening")]
    white, _ = aggregate_openings(games, "alice")
    assert white["C60"][Outcome.WIN] == 1


def test_top_openings_returns_top_3():
    openings = {
        "C60": {"name": "Ruy Lopez", Outcome.WIN: 10, Outcome.LOSS: 5, Outcome.DRAW: 5},
        "D00": {"name": "Queens Pawn", Outcome.WIN: 5, Outcome.LOSS: 3, Outcome.DRAW: 0},
        "A00": {"name": "Rare", Outcome.WIN: 1, Outcome.LOSS: 0, Outcome.DRAW: 0},
        "E00": {"name": "Indian", Outcome.WIN: 8, Outcome.LOSS: 4, Outcome.DRAW: 2},
    }
    result = top_openings(openings)
    assert len(result) == 3
    assert result[0].eco == "C60"
    assert result[1].eco == "E00"


def test_top_openings_fewer_than_3():
    openings = {
        "C60": {"name": "Ruy Lopez", Outcome.WIN: 5, Outcome.LOSS: 1, Outcome.DRAW: 0},
    }
    result = top_openings(openings)
    assert len(result) == 1


def test_top_openings_empty():
    result = top_openings({})
    assert result == []


def test_opening_stat_winrate():
    stat = OpeningStat(eco="C60", name="Ruy Lopez", total=10, wins=6, losses=3, draws=1)
    assert stat.winrate == 60


def test_opening_stat_winrate_zero_total():
    stat = OpeningStat(eco="C60", name="Ruy Lopez", total=0, wins=0, losses=0, draws=0)
    assert stat.winrate == 0


def test_opening_stat_winrate_boundaries():
    assert OpeningStat(eco="X", name="X", total=100, wins=45, losses=55, draws=0).winrate == 45
    assert OpeningStat(eco="X", name="X", total=100, wins=55, losses=45, draws=0).winrate == 55
