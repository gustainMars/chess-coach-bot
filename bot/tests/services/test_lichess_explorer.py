from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


def _make_response(status_code: int, json_data: dict) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def _mock_client(response: MagicMock):
    """Return a context-manager mock that yields a client returning `response`."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=response)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.mark.asyncio
async def test_get_top_moves_returns_uci_list():
    from bot.services.lichess_explorer import get_top_moves

    payload = {"moves": [{"uci": "e2e4"}, {"uci": "d2d4"}, {"uci": "c2c4"}]}
    with patch("httpx.AsyncClient", return_value=_mock_client(_make_response(200, payload))):
        result = await get_top_moves("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    assert result == ["e2e4", "d2d4", "c2c4"]


@pytest.mark.asyncio
async def test_get_top_moves_respects_n_limit():
    from bot.services.lichess_explorer import get_top_moves

    payload = {"moves": [{"uci": f"e{i}e{i+1}"} for i in range(1, 8)]}
    with patch("httpx.AsyncClient", return_value=_mock_client(_make_response(200, payload))):
        result = await get_top_moves("fen", n=3)

    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_top_moves_returns_empty_on_non_200():
    from bot.services.lichess_explorer import get_top_moves

    with patch("httpx.AsyncClient", return_value=_mock_client(_make_response(404, {}))):
        result = await get_top_moves("any_fen")

    assert result == []


@pytest.mark.asyncio
async def test_get_top_moves_returns_empty_when_no_moves():
    from bot.services.lichess_explorer import get_top_moves

    payload = {"moves": []}
    with patch("httpx.AsyncClient", return_value=_mock_client(_make_response(200, payload))):
        result = await get_top_moves("fen")

    assert result == []


@pytest.mark.asyncio
async def test_get_top_moves_returns_empty_on_network_error():
    from bot.services.lichess_explorer import get_top_moves

    client = AsyncMock()
    client.get = AsyncMock(side_effect=httpx.ConnectError("timeout"))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=cm):
        result = await get_top_moves("fen")

    assert result == []
