import hashlib
import hmac
import json
from urllib.parse import parse_qsl


def validate_init_data(init_data: str, bot_token: str) -> bool:
    """Validate Telegram WebApp initData HMAC signature."""
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_received = parsed.pop("hash", "")
    if not hash_received:
        return False
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, hash_received)


def parse_telegram_user_id(init_data: str) -> int | None:
    """Extract the Telegram user ID from a validated initData string."""
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    user_json = parsed.get("user", "")
    if not user_json:
        return None
    try:
        return json.loads(user_json).get("id")
    except (json.JSONDecodeError, AttributeError):
        return None
