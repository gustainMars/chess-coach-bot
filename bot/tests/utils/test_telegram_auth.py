import hashlib
import hmac
from urllib.parse import urlencode

from bot.utils.telegram_auth import validate_init_data

_BOT_TOKEN = "123456:ABC-test-token"


def _make_init_data(**fields: str) -> str:
    """Build a valid Telegram initData string signed with _BOT_TOKEN."""
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", _BOT_TOKEN.encode(), hashlib.sha256).digest()
    sig = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": sig})


def test_valid_init_data_returns_true():
    init_data = _make_init_data(user='{"id":1}', auth_date="1700000000")
    assert validate_init_data(init_data, _BOT_TOKEN) is True


def test_wrong_token_returns_false():
    init_data = _make_init_data(user='{"id":1}', auth_date="1700000000")
    assert validate_init_data(init_data, "wrong:token") is False


def test_tampered_data_returns_false():
    init_data = _make_init_data(user='{"id":1}', auth_date="1700000000")
    tampered = init_data.replace("1700000000", "9999999999")
    assert validate_init_data(tampered, _BOT_TOKEN) is False


def test_missing_hash_returns_false():
    init_data = urlencode({"user": '{"id":1}', "auth_date": "1700000000"})
    assert validate_init_data(init_data, _BOT_TOKEN) is False


def test_empty_string_returns_false():
    assert validate_init_data("", _BOT_TOKEN) is False


def test_multiple_fields_validated_correctly():
    init_data = _make_init_data(
        user='{"id":42,"first_name":"Test"}',
        auth_date="1700000000",
        query_id="AABB",
    )
    assert validate_init_data(init_data, _BOT_TOKEN) is True
