from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from collections import defaultdict
from bot.services.chesscom import get_recent_games, get_user_info
from bot.services.pgn_parser import parse_game

router = Router()

@router.message(Command("analyze"))
async def cmd_analyze(message: Message):
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer(
            "Use like this: /analyze <username>\n"
            "Example: /analyze magnuscarlsen"
        )
        return
    
    username = args[1].strip()
    
    status_msg = await message.answer(f"Searching for user *{username}*...", parse_mode="Markdown")
    
    user_info = await get_user_info(username)
    
    if user_info is None:
        await status_msg.edit_text(f"User *{username}* not found on chess.com", parse_mode="Markdown")
        return
    
    games = await get_recent_games(username)    
    if not games:
        await status_msg.edit_text(f"No matches found for the user *{username}*", parse_mode="Markdown")
        return
    
    white_openings = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "eco": "?"})
    black_openings = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "eco": "?"})
    
    for game in games:
        white = game.get("white", {})
        black = game.get("black", {})
        
        playing_white = white.get("username", "").lower() == username.lower()
        if playing_white:
            result = white.get("result")
        else:
            result = black.get("result")
        
        if result == "win":
            outcome = "wins"
        elif result in ("checkmated", "resigned", "timeout", "abandoned"):
            outcome = "losses"
        else:
            outcome = "draws"
            
        pgn = game.get("pgn", "")
        if not pgn:
            continue
        
        parsed = parse_game(pgn)
        if not parsed:
            continue
        
        name = parsed["opening_name"]
        eco = parsed["opening_eco"]
        
        if playing_white:
            white_openings[name]["eco"] = eco
            white_openings[name][outcome] += 1
        else:
            black_openings[name]["eco"] = eco
            black_openings[name][outcome] += 1
    
    def calc_stats(openings):
        stats = []
        for name, data in openings.items():
            total = data["wins"] + data["losses"] + data["draws"]
            winrate = round((data["wins"] / total) * 100) if total > 0 else 0
            stats.append({
                "name": name,
                "eco": data["eco"],
                "total": total,
                "wins":  data["wins"],
                "losses": data["losses"],
                "draws": data["draws"],
                "winrate": winrate,
            })
        stats.sort(key=lambda x: x["winrate"], reverse=True)
        return stats[:3]
    
    def format_opening_block(op, rank):
        emoji = "🟢" if op["winrate"] >= 55 else "🔴" if op["winrate"] >= 45 else "🟡"
        return (
            f"{rank}. *{op['name']}* `[{op['eco']}]`\n"
            f"  {emoji} {op['winrate']}% winrate "
            f"({op['wins']}V {op['losses']}D {op['draws']}E) "
            f"em {op['total']} partidas\n"
        )
        
    white_stats = calc_stats(white_openings)
    black_stats = calc_stats(black_openings)
    
    msg = f"♟️ *Openings Analysis — {username}*\n"
    msg += f"_{len(games)} matches on the last month_\n\n"
    
    msg += "*Playing as White:*\n"
    if white_stats:
        for i, op in enumerate(white_stats, 1):
            msg += format_opening_block(op, i)
    else:
        msg += "_No data for white openings_\n"
        
    msg += "\n*Playing as Black:*\n"
    if black_stats:
        for i, op in enumerate(black_stats, 1):
            msg += format_opening_block(op, i)
    else:
        msg += "_No data for black openings_\n"
        
    allStats = white_stats + black_stats
    if allStats:
        worst = min(allStats, key=lambda x: x["winrate"])
        msg += (
            f"\n📚 *Study suggestion:*\n"
            f"Focus on improving the opening *{worst['name']}* - with a winrate of {worst['winrate']}%.\n"
            f"Use /study to get personalized study materials for this opening.\n"
        )
    
    await status_msg.edit_text(msg, parse_mode="Markdown")
    
@router.message(Command("debug"))
async def cmd_debug(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Use: /debug <username>")
        return

    username = args[1].strip().lower()
    games = await get_recent_games(username)

    if not games:
        await message.answer("No matches found")
        return

    game = games[0]
    pgn = game.get("pgn", "")

    first_lines = "\n".join(pgn.split("\n")[:15])
    await message.answer(f"```\n{first_lines}\n```", parse_mode="Markdown")