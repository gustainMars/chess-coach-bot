import pytest


def test_miniapp_url_valid_screen_with_both_env_vars(monkeypatch):
    monkeypatch.setenv("MINIAPP_URL", "https://example.com/miniapp")
    monkeypatch.setenv("WEBAPP_PUBLIC_URL", "https://api.example.com")

    from bot.utils.miniapp import miniapp_url

    assert miniapp_url("study") == (
        "https://example.com/miniapp/study/index.html?api=https://api.example.com"
    )
    assert miniapp_url("learn") == (
        "https://example.com/miniapp/learn/index.html?api=https://api.example.com"
    )


def test_miniapp_url_no_public_url(monkeypatch):
    monkeypatch.setenv("MINIAPP_URL", "https://example.com/miniapp")
    monkeypatch.delenv("WEBAPP_PUBLIC_URL", raising=False)

    from bot.utils.miniapp import miniapp_url

    url = miniapp_url("study")
    assert url == "https://example.com/miniapp/study/index.html"
    assert "?api=" not in url


def test_miniapp_url_missing_base(monkeypatch):
    monkeypatch.delenv("MINIAPP_URL", raising=False)

    from bot.utils.miniapp import miniapp_url

    assert miniapp_url("study") is None


def test_miniapp_url_invalid_screen(monkeypatch):
    monkeypatch.setenv("MINIAPP_URL", "https://example.com/miniapp")

    from bot.utils.miniapp import miniapp_url

    assert miniapp_url("shared") is None
    assert miniapp_url("../../etc/passwd") is None
    assert miniapp_url("") is None
