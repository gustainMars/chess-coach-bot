from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from bot.services.chesscom import get_recent_games, get_user_info

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
    
    wins = losses = draws = 0
    
    for game in games:
        white = game.get("white", {})
        black = game.get("black", {})
        
        if white.get("username", "").lower() == username.lower():
            result = white.get("result")
        else:
            result = black.get("result")
        
        if result == "win":
            wins += 1
        elif result in ("checkmated", "resigned", "timeout", "abandoned"):
            losses += 1
        else:
            draws += 1
        
    total = wins + losses + draws
    winrate = round((wins / total) * 100) if total > 0 else 0
    
    await status_msg.edit_text(
        f"♟️ *Report of {username}*\n\n"
        f"📊 Analyzed matches: {total}\n"
        f"✅ Victories: {wins}\n"
        f"❌ Losses: {losses}\n"
        f"🤝 Draws: {draws}\n"
        f"📈 Winrate: {winrate}%\n\n"
        f"_Openings analyzes soon!_",
        parse_mode="Markdown"
    )