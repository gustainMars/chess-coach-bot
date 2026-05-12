import httpx

_EXPLORER_URL = "https://explorer.lichess.ovh/masters"
_TOP_N = 5


async def get_top_moves(fen: str, n: int = _TOP_N) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                _EXPLORER_URL,
                params={"fen": fen, "topGames": 0, "recentGames": 0},
                headers={"Accept": "application/json"},
            )
        if resp.status_code != 200:
            return []
        data = resp.json()
        moves = data.get("moves", [])
        return [m["uci"] for m in moves[:n]]
    except Exception:
        return []
