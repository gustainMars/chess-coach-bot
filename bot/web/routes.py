import os

import chess
from aiohttp import web

from bot.services.attack_generator import (
    generate_attack_position,
    get_capturable_squares,
    validate_capture_selection,
)
from bot.utils.telegram_auth import validate_init_data

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, X-Telegram-Init-Data",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


async def handle_preflight(request: web.Request) -> web.Response:
    return web.Response(headers=_CORS_HEADERS)


async def handle_get_position(request: web.Request) -> web.Response:
    bot_token = os.getenv("TELEGRAM_TOKEN", "")
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not validate_init_data(init_data, bot_token):
        return web.json_response(
            {"error": "unauthorized"}, status=401, headers=_CORS_HEADERS
        )
    board = generate_attack_position()
    return web.json_response({"fen": board.fen()}, headers=_CORS_HEADERS)


async def handle_attack_check(request: web.Request) -> web.Response:
    bot_token = os.getenv("TELEGRAM_TOKEN", "")

    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not validate_init_data(init_data, bot_token):
        return web.json_response(
            {"error": "unauthorized"}, status=401, headers=_CORS_HEADERS
        )

    try:
        body = await request.json()
        fen: str = body["fen"]
        selected: set[str] = set(body.get("selected", []))
    except (KeyError, ValueError, TypeError):
        return web.json_response(
            {"error": "invalid body"}, status=400, headers=_CORS_HEADERS
        )

    try:
        board = chess.Board(fen)
    except ValueError:
        return web.json_response(
            {"error": "invalid fen"}, status=400, headers=_CORS_HEADERS
        )

    capturable = {chess.square_name(sq) for sq in get_capturable_squares(board)}
    missed, extra = validate_capture_selection(capturable, selected)

    return web.json_response(
        {
            "correct": not missed and not extra,
            "missed": sorted(missed),
            "extra": sorted(extra),
            "capturable": sorted(capturable),
        },
        headers=_CORS_HEADERS,
    )


def create_web_app() -> web.Application:
    app = web.Application()
    app.router.add_options("/miniapp/attack/position", handle_preflight)
    app.router.add_options("/miniapp/attack/check", handle_preflight)
    app.router.add_get("/miniapp/attack/position", handle_get_position)
    app.router.add_post("/miniapp/attack/check", handle_attack_check)
    return app
