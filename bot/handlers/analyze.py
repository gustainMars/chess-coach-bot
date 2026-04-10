from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from bot.domain.messages import Messages
from bot.domain.opening import OpeningStat
from bot.services.chesscom import get_recent_games, get_user_info
from bot.services.stats import aggregate_openings, top_openings

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

@router.message(Command("analyze"))
async def cmd_analyze(message: Message):
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer(Messages.ANALYZE_USAGE)
        return
    
    username = args[1].strip().lower()

    status_msg = await message.answer(Messages.SEARCHING_USER.format(username=username), parse_mode="Markdown")
    
    user_info = await get_user_info(username)
    
    if user_info is None:
        await status_msg.edit_text(Messages.USER_NOT_FOUND.format(username=username), parse_mode="Markdown")
        return
    
    games = await get_recent_games(username)    
    if not games:
        await status_msg.edit_text(Messages.NO_GAMES_FOUND.format(username=username), parse_mode="Markdown")
        return
    
    await status_msg.edit_text(Messages.ANALYZING_GAMES.format(total=len(games)), parse_mode="Markdown")
    
    white_openings, black_openings = aggregate_openings(games, username)
    white_stats = top_openings(white_openings)
    black_stats = top_openings(black_openings)
    
    await status_msg.edit_text(
        _format_report(username, games, white_stats, black_stats), 
        parse_mode="Markdown"
    )
    
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