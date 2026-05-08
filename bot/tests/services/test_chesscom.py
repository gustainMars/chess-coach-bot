from datetime import datetime, timedelta, timezone

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def make_response(status_code: int, json_data: dict) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def _current_month_url() -> str:
    now = datetime.now(timezone.utc)
    return f"https://api.chess.com/pub/player/testuser/games/{now.year}/{now.month:02d}"


def _recent_ts() -> int:
    return int((datetime.now(timezone.utc) - timedelta(days=10)).timestamp())


def _old_ts() -> int:
    return int((datetime.now(timezone.utc) - timedelta(days=60)).timestamp())


@pytest.mark.asyncio
async def test_get_recent_games_returns_games():
    from bot.services.chesscom import get_recent_games

    game = {"pgn": "1. e4 e5", "end_time": _recent_ts(), "white": {}, "black": {}}
    archives_resp = make_response(200, {"archives": [_current_month_url()]})
    games_resp = make_response(200, {"games": [game]})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[archives_resp, games_resp])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_recent_games("testuser")

    assert len(result) == 1
    assert result[0]["pgn"] == "1. e4 e5"


@pytest.mark.asyncio
async def test_get_recent_games_filters_old_games():
    from bot.services.chesscom import get_recent_games

    archives_resp = make_response(200, {"archives": [_current_month_url()]})
    games_resp = make_response(
        200, {"games": [{"pgn": "1. d4", "end_time": _old_ts()}]}
    )

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[archives_resp, games_resp])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_recent_games("testuser")

    assert result == []


@pytest.mark.asyncio
async def test_get_recent_games_skips_old_archives():
    from bot.services.chesscom import get_recent_games

    old_url = "https://api.chess.com/pub/player/testuser/games/2020/01"
    archives_resp = make_response(200, {"archives": [old_url, _current_month_url()]})
    games_resp = make_response(
        200, {"games": [{"pgn": "1. e4", "end_time": _recent_ts()}]}
    )

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[archives_resp, games_resp])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_recent_games("testuser")

    assert len(result) == 1
    assert mock_client.get.call_count == 2  # archives fetch + only current month


@pytest.mark.asyncio
async def test_get_recent_games_user_not_found():
    from bot.services.chesscom import get_recent_games

    archives_resp = make_response(404, {})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=archives_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_recent_games("unknownuser")

    assert result is None


@pytest.mark.asyncio
async def test_get_recent_games_no_archives():
    from bot.services.chesscom import get_recent_games

    archives_resp = make_response(200, {"archives": []})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=archives_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_recent_games("testuser")

    assert result == []



@pytest.mark.asyncio
async def test_get_user_info_returns_profile():
    from bot.services.chesscom import get_user_info

    profile = {"username": "testuser", "player_id": 123}
    resp = make_response(200, profile)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_user_info("testuser")

    assert result == profile


@pytest.mark.asyncio
async def test_get_user_info_not_found():
    from bot.services.chesscom import get_user_info

    resp = make_response(404, {})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_user_info("ghost")

    assert result is None


# --- get_player_rating ---


@pytest.mark.asyncio
async def test_get_player_rating_returns_rapid_rating():
    from bot.services.chesscom import get_player_rating

    payload = {"chess_rapid": {"last": {"rating": 1350}}}
    resp = make_response(200, payload)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_player_rating("alice")

    assert result == 1350


@pytest.mark.asyncio
async def test_get_player_rating_no_rapid_games():
    from bot.services.chesscom import get_player_rating

    # utilizador existe mas nunca jogou rapid
    resp = make_response(200, {"chess_bullet": {"last": {"rating": 900}}})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_player_rating("alice")

    assert result is None


@pytest.mark.asyncio
async def test_get_player_rating_api_error():
    from bot.services.chesscom import get_player_rating

    resp = make_response(404, {})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.chesscom.httpx.AsyncClient", return_value=mock_client):
        result = await get_player_rating("ghost")

    assert result is None
