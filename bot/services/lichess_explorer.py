import httpx

_EXPLORER_URL = "https://explorer.lichess.ovh/lichess"
_TOP_N = 5
_MAX_OPENING_HALF_MOVES = 20


async def get_top_moves(fen: str, n: int = _TOP_N) -> list[str]:
    """
    Query Lichess Opening Explorer for the most-played moves in a position.
    Returns up to n move strings in UCI format (e.g. ['e2e4', 'd2d4']).
    Returns [] if the position has no data or the request fails.
    """
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
