import hashlib
import hmac
from urllib.parse import urlencode

from bot.utils.telegram_auth import parse_telegram_user_id, validate_init_data

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


# ── parse_telegram_user_id ────────────────────────────────────────────────────

def test_parse_user_id_returns_correct_id():
    init_data = _make_init_data(user='{"id":42,"first_name":"Test"}', auth_date="1700000000")
    assert parse_telegram_user_id(init_data) == 42


def test_parse_user_id_no_user_field_returns_none():
    init_data = _make_init_data(auth_date="1700000000")
    assert parse_telegram_user_id(init_data) is None


def test_parse_user_id_invalid_json_returns_none():
    from urllib.parse import urlencode
    init_data = urlencode({"user": "not-valid-json", "auth_date": "1700000000"})
    assert parse_telegram_user_id(init_data) is None


def test_parse_user_id_empty_string_returns_none():
    assert parse_telegram_user_id("") is None


def test_parse_user_id_without_id_key_returns_none():
    init_data = _make_init_data(user='{"first_name":"Test"}', auth_date="1700000000")
    assert parse_telegram_user_id(init_data) is None
