from collections import defaultdict
from bot.domain.opening import OpeningStat, Outcome
from bot.services.pgn_parser import extract_opening_from

def aggregate_openings(games: list, username: str) -> tuple:
    white_openings = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "name": "Unknown opening"})
    black_openings = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "name": "Unknown opening"})
    
    for game in games:
        white = game.get("white", {})
        black = game.get("black", {})
        
        playing_white = white.get("username", "").lower() == username.lower()
        result = white.get("result") if playing_white else black.get("result")
        
        if result == "win":
            outcome = Outcome.WIN
        elif result in ("checkmated", "resigned", "timeout", "abandoned"):
            outcome = Outcome.LOSS
        else:
            outcome = Outcome.DRAW
        
        pgn = game.get("pgn", "")
        if not pgn:
            continue
        
        parsed = extract_opening_from(pgn)
        if not parsed:
            continue
        
        eco = parsed["opening_eco"]
        name = parsed["opening_name"]
        
        if playing_white:
            white_openings[eco]["name"] = name
            white_openings[eco][outcome] += 1
        else:
            black_openings[eco]["name"] = name
            black_openings[eco][outcome] += 1
    
    return white_openings, black_openings

def top_openings(openings: dict) -> list[OpeningStat]:
    stats = []
    for eco, data in openings.items():
        total = data[Outcome.WIN] + data[Outcome.LOSS] + data[Outcome.DRAW]
        stats.append(OpeningStat(
            eco=eco,
            name=data["name"],
            total=total,
            wins=data[Outcome.WIN],
            losses=data[Outcome.LOSS],
            draws=data[Outcome.DRAW],
        ))
    stats.sort(key=lambda x: x.total, reverse=True)
    return stats[:3]