import hashlib
import hmac
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer

from bot.web.routes import create_web_app

_BOT_TOKEN = "123456:test-token"
_SIMPLE_FEN = (
    "r7/8/8/8/8/8/8/4K3 w - - 0 1"  # black rook a8, white king e1 — neither attacked
)


def _make_init_data(**fields: str) -> str:
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", _BOT_TOKEN.encode(), hashlib.sha256).digest()
    sig = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": sig})


@pytest.fixture
def valid_init_data() -> str:
    return _make_init_data(user='{"id":1}', auth_date="1700000000")


@pytest_asyncio.fixture
async def client(monkeypatch, valid_init_data):
    monkeypatch.setenv("TELEGRAM_TOKEN", _BOT_TOKEN)
    app = create_web_app()
    server = TestServer(app)
    c = TestClient(server)
    await c.start_server()
    yield c
    await c.close()


@pytest.mark.asyncio
async def test_valid_request_returns_200(client, valid_init_data):
    resp = await client.post(
        "/miniapp/attack/check",
        json={"fen": _SIMPLE_FEN, "selected": []},
        headers={"X-Telegram-Init-Data": valid_init_data},
    )
    assert resp.status == 200


@pytest.mark.asyncio
async def test_invalid_auth_returns_401(client):
    resp = await client.post(
        "/miniapp/attack/check",
        json={"fen": _SIMPLE_FEN, "selected": []},
        headers={"X-Telegram-Init-Data": "hash=badhash"},
    )
    assert resp.status == 401


@pytest.mark.asyncio
async def test_missing_auth_header_returns_401(client):
    resp = await client.post(
        "/miniapp/attack/check",
        json={"fen": _SIMPLE_FEN, "selected": []},
    )
    assert resp.status == 401


@pytest.mark.asyncio
async def test_invalid_fen_returns_400(client, valid_init_data):
    resp = await client.post(
        "/miniapp/attack/check",
        json={"fen": "not-a-fen", "selected": []},
        headers={"X-Telegram-Init-Data": valid_init_data},
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_missing_fen_returns_400(client, valid_init_data):
    resp = await client.post(
        "/miniapp/attack/check",
        json={"selected": []},
        headers={"X-Telegram-Init-Data": valid_init_data},
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_correct_selection_returns_correct_true(client, valid_init_data):
    # In _SIMPLE_FEN neither rook nor king is attacked — correct answer is no selection
    resp = await client.post(
        "/miniapp/attack/check",
        json={"fen": _SIMPLE_FEN, "selected": []},
        headers={"X-Telegram-Init-Data": valid_init_data},
    )
    data = await resp.json()
    assert data["correct"] is True
    assert data["missed"] == []
    assert data["extra"] == []


@pytest.mark.asyncio
async def test_wrong_selection_returns_correct_false(client, valid_init_data):
    # a8 is not capturable in _SIMPLE_FEN
    resp = await client.post(
        "/miniapp/attack/check",
        json={"fen": _SIMPLE_FEN, "selected": ["a8"]},
        headers={"X-Telegram-Init-Data": valid_init_data},
    )
    data = await resp.json()
    assert data["correct"] is False
    assert "a8" in data["extra"]


@pytest.mark.asyncio
async def test_response_has_capturable_field(client, valid_init_data):
    resp = await client.post(
        "/miniapp/attack/check",
        json={"fen": _SIMPLE_FEN, "selected": []},
        headers={"X-Telegram-Init-Data": valid_init_data},
    )
    data = await resp.json()
    assert "capturable" in data
    assert isinstance(data["capturable"], list)


@pytest.mark.asyncio
async def test_cors_headers_present_on_post(client, valid_init_data):
    resp = await client.post(
        "/miniapp/attack/check",
        json={"fen": _SIMPLE_FEN, "selected": []},
        headers={"X-Telegram-Init-Data": valid_init_data},
    )
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"


@pytest.mark.asyncio
async def test_options_preflight_returns_200(client):
    resp = await client.options("/miniapp/attack/check")
    assert resp.status == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"
