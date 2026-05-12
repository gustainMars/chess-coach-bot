import os

import chess
from aiohttp import web

from bot.db.database import SessionFactory
from bot.db import repository
from bot.services.attack_generator import (
    generate_attack_position,
    get_capturable_squares,
    validate_capture_selection,
)
from bot.services.move_validator import validate_move_input
from bot.utils.telegram_auth import parse_telegram_user_id, validate_init_data

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, X-Telegram-Init-Data",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


def _bot_token() -> str:
    return os.getenv("TELEGRAM_TOKEN", "")


def _auth(request: web.Request) -> tuple[bool, int | None]:
    """Validate init_data and return (valid, telegram_user_id)."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not validate_init_data(init_data, _bot_token()):
        return False, None
    return True, parse_telegram_user_id(init_data)


async def handle_preflight(request: web.Request) -> web.Response:
    return web.Response(headers=_CORS_HEADERS)


# ── Attack endpoints ──────────────────────────────────────────────────────────

async def handle_get_position(request: web.Request) -> web.Response:
    valid, _ = _auth(request)
    if not valid:
        return web.json_response({"error": "unauthorized"}, status=401, headers=_CORS_HEADERS)
    board = generate_attack_position()
    return web.json_response({"fen": board.fen()}, headers=_CORS_HEADERS)


async def handle_attack_check(request: web.Request) -> web.Response:
    valid, _ = _auth(request)
    if not valid:
        return web.json_response({"error": "unauthorized"}, status=401, headers=_CORS_HEADERS)

    try:
        body = await request.json()
        fen: str = body["fen"]
        selected: set[str] = set(body.get("selected", []))
    except (KeyError, ValueError, TypeError):
        return web.json_response({"error": "invalid body"}, status=400, headers=_CORS_HEADERS)

    try:
        board = chess.Board(fen)
    except ValueError:
        return web.json_response({"error": "invalid fen"}, status=400, headers=_CORS_HEADERS)

    capturable = {chess.square_name(sq) for sq in get_capturable_squares(board)}
    missed, extra = validate_capture_selection(capturable, selected)

    return web.json_response(
        {"correct": not missed and not extra, "missed": sorted(missed),
         "extra": sorted(extra), "capturable": sorted(capturable)},
        headers=_CORS_HEADERS,
    )


# ── Study endpoints ───────────────────────────────────────────────────────────

async def handle_study_card(request: web.Request) -> web.Response:
    valid, user_id = _auth(request)
    if not valid or user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401, headers=_CORS_HEADERS)

    eco = request.rel_url.query.get("eco") or None

    async with SessionFactory() as session:
        blunder, reset = await repository.get_next_unreviewed_blunder(session, user_id, eco=eco)

    if blunder is None:
        return web.json_response({"blunder_id": None, "reset": False}, headers=_CORS_HEADERS)

    try:
        board = chess.Board(blunder.fen)
        move = board.parse_san(blunder.expected_move)
        expected_uci = move.uci()
    except Exception:
        expected_uci = ""

    return web.json_response(
        {
            "blunder_id": blunder.id,
            "fen": blunder.fen,
            "opening_name": blunder.opening_name,
            "opening_eco": blunder.opening_eco,
            "quality": blunder.quality,
            "reset": reset,
            "expected_uci": expected_uci,
        },
        headers=_CORS_HEADERS,
    )


async def handle_study_answer(request: web.Request) -> web.Response:
    valid, user_id = _auth(request)
    if not valid or user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401, headers=_CORS_HEADERS)

    try:
        body = await request.json()
        blunder_id: int = int(body["blunder_id"])
        move_input: str = str(body["move"])
    except (KeyError, ValueError, TypeError):
        return web.json_response({"error": "invalid body"}, status=400, headers=_CORS_HEADERS)

    async with SessionFactory() as session:
        blunder = await repository.get_blunder_by_id(session, blunder_id)
        if blunder is None:
            return web.json_response({"error": "not found"}, status=404, headers=_CORS_HEADERS)
        if blunder.telegram_id != user_id:
            return web.json_response({"error": "forbidden"}, status=403, headers=_CORS_HEADERS)

        user_move = validate_move_input(move_input, blunder.fen)
        if user_move is None:
            return web.json_response({"error": "invalid move"}, status=400, headers=_CORS_HEADERS)

        board = chess.Board(blunder.fen)
        expected = board.parse_san(blunder.expected_move)

        correct = user_move == expected
        if correct:
            await repository.mark_blunder_reviewed(session, blunder.id)

        try:
            expected_uci = expected.uci()
        except Exception:
            expected_uci = ""

    return web.json_response(
        {"correct": correct, "expected_move": blunder.expected_move, "expected_uci": expected_uci},
        headers=_CORS_HEADERS,
    )


async def handle_study_openings(request: web.Request) -> web.Response:
    valid, user_id = _auth(request)
    if not valid or user_id is None:
        return web.json_response({"error": "unauthorized"}, status=401, headers=_CORS_HEADERS)

    async with SessionFactory() as session:
        openings = await repository.get_blunder_openings(session, user_id)

    return web.json_response(openings, headers=_CORS_HEADERS)


# ── Health ────────────────────────────────────────────────────────────────────

async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="ok")


def create_web_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_health)

    app.router.add_options("/miniapp/attack/position", handle_preflight)
    app.router.add_options("/miniapp/attack/check", handle_preflight)
    app.router.add_get("/miniapp/attack/position", handle_get_position)
    app.router.add_post("/miniapp/attack/check", handle_attack_check)

    app.router.add_options("/miniapp/study/card", handle_preflight)
    app.router.add_options("/miniapp/study/answer", handle_preflight)
    app.router.add_options("/miniapp/study/openings", handle_preflight)
    app.router.add_get("/miniapp/study/card", handle_study_card)
    app.router.add_post("/miniapp/study/answer", handle_study_answer)
    app.router.add_get("/miniapp/study/openings", handle_study_openings)

    return app
