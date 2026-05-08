import logging
from datetime import datetime, timezone
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from bot.domain.messages import Messages
from bot.domain.move_quality import MoveQuality
from bot.domain.opening import Color, OpeningStat
from bot.services.chesscom import get_player_rating, get_recent_games, get_user_info
from bot.services.deviation import evaluate_deviation, find_deviation
from bot.services.opening_extractor import extract_opening_from
from bot.services.stats import aggregate_openings, top_openings
from bot.db.database import SessionFactory
from bot.db import repository

router = Router()


def _format_opening_block(op: OpeningStat, rank: int):
    emoji = "🟢" if op.winrate >= 55 else "🔴" if op.winrate < 45 else "🟡"
    return (
        f"{rank}. *{op.name}* `[{op.eco}]`\n"
        f"  {emoji} {op.winrate}% winrate "
        f"({op.wins}V {op.losses}L {op.draws}D) "
        f"in {op.total} matches\n"
    )


def _format_report(username, games, white_stats, black_stats):
    msg = Messages.REPORT_HEADER.format(username=username, total=len(games))

    msg += Messages.PLAYING_WHITE
    if white_stats:
        for i, op in enumerate(white_stats, 1):
            msg += _format_opening_block(op, i)
    else:
        msg += Messages.NO_WHITE_DATA

    msg += Messages.PLAYING_BLACK
    if black_stats:
        for i, op in enumerate(black_stats, 1):
            msg += _format_opening_block(op, i)
    else:
        msg += Messages.NO_BLACK_DATA

    all_stats = white_stats + black_stats
    if all_stats:
        worst = min(all_stats, key=lambda x: x.winrate)
        msg += Messages.STUDY_SUGGESTION.format(name=worst.name, winrate=worst.winrate)

    return msg


async def _save_blunders(session, telegram_id, games):
    for game in games:
        pgn = game.get("pgn", "")
        if not pgn:
            continue

        opening = extract_opening_from(pgn)
        if not opening:
            continue

        deviation = find_deviation(pgn, opening["opening_eco"])
        if deviation is None:
            continue

        quality = await evaluate_deviation(deviation)
        if quality in (MoveQuality.BLUNDER, MoveQuality.MISTAKE):
            await repository.save_blunder(
                session,
                telegram_id=telegram_id,
                opening_eco=opening["opening_eco"],
                opening_name=opening["opening_name"],
                fen=deviation.fen,
                user_move=deviation.user_move,
                expected_move=deviation.expected_move,
                quality=quality,
            )


@router.message(Command("analyze"))
async def cmd_analyze(message: Message):
    def _evaluate_games() -> tuple:
        white_openings, black_openings = aggregate_openings(games, username)
        return top_openings(white_openings), top_openings(black_openings)

    args = message.text.split()
    if len(args) < 2:
        await message.answer(Messages.ANALYZE_USAGE)
        return

    username_og = args[1].strip()
    username = args[1].strip().lower()

    try:
        months = max(1, min(6, int(args[2]))) if len(args) >= 3 else 1
    except ValueError:
        months = 1

    status_msg = await message.answer(
        Messages.SEARCHING_USER.format(username=username), parse_mode="Markdown"
    )

    user_info = await get_user_info(username)
    if user_info is None:
        await status_msg.edit_text(
            Messages.USER_NOT_FOUND.format(username=username), parse_mode="Markdown"
        )
        return

    games = await get_recent_games(username, num_months=months)
    if not games:
        await status_msg.edit_text(
            Messages.NO_GAMES_FOUND.format(username=username), parse_mode="Markdown"
        )
        return

    await status_msg.edit_text(
        Messages.ANALYZING_GAMES.format(total=len(games)), parse_mode="Markdown"
    )
    white_stats, black_stats = _evaluate_games()

    report = _format_report(username_og, games, white_stats, black_stats)

    try:
        now = datetime.now(timezone.utc)
        rating = await get_player_rating(username)
        async with SessionFactory() as session:
            await repository.upsert_user(
                session, telegram_id=message.from_user.id, chesscom_username=username
            )
            for stat in white_stats:
                await repository.upsert_opening_stat(
                    session,
                    username,
                    stat.eco,
                    Color.WHITE,
                    now.month,
                    now.year,
                    rating,
                    stat.total,
                    stat.wins,
                    stat.losses,
                    stat.draws,
                )
            for stat in black_stats:
                await repository.upsert_opening_stat(
                    session,
                    username,
                    stat.eco,
                    Color.BLACK,
                    now.month,
                    now.year,
                    rating,
                    stat.total,
                    stat.wins,
                    stat.losses,
                    stat.draws,
                )
            prev_rating = await repository.get_previous_rating(
                session, username, now.month, now.year
            )
            if rating and prev_rating and rating > prev_rating:
                report += Messages.RATING_PROGRESS.format(
                    prev=prev_rating, current=rating
                )
            await _save_blunders(session, message.from_user.id, games)
    except Exception:
        logging.exception("DB persistence failed for user %s", username)

    await status_msg.edit_text(report, parse_mode="Markdown")


@router.message(Command("debug"))
async def cmd_debug(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer(Messages.DEBUG_USAGE)
        return

    username = args[1].strip().lower()
    games = await get_recent_games(username)

    if not games:
        await message.answer(Messages.NO_GAMES_FOUND.format(username=username))
        return

    game = games[0]
    pgn = game.get("pgn", "")

    first_lines = "\n".join(pgn.split("\n")[:15])
    await message.answer(f"```\n{first_lines}\n```", parse_mode="Markdown")
