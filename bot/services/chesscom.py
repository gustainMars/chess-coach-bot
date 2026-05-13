from datetime import datetime, timedelta, timezone

import httpx

BASE_URL = "https://api.chess.com/pub"


def _archive_ym(url: str) -> tuple[int, int]:
    parts = url.rstrip("/").split("/")
    return int(parts[-2]), int(parts[-1])


async def get_recent_games(username: str) -> list:
    """Return games from the last 15 days for a Chess.com user."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=15)
    cutoff_ym = (cutoff.year, cutoff.month)
    cutoff_ts = cutoff.timestamp()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/player/{username}/games/archives",
            headers={"User-Agent": "ChessOpeningsCoachBot/1.0"},
        )

        if response.status_code == 404:
            return None

        archives = response.json().get("archives", [])
        if not archives:
            return []

        relevant = [a for a in archives if _archive_ym(a) >= cutoff_ym]
        if not relevant:
            relevant = archives[-1:]

        all_games = []
        for archive_url in relevant:
            resp = await client.get(
                archive_url,
                headers={"User-Agent": "ChessOpeningsCoachBot/1.0"},
            )
            for game in resp.json().get("games", []):
                if game.get("end_time", 0) >= cutoff_ts:
                    all_games.append(game)

    return all_games


async def get_player_rating(username: str) -> int | None:
    """Returns the user's current rapid rating, or None if unavailable."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/player/{username}/stats",
            headers={"User-Agent": "ChessOpeningsCoachBot/1.0"},
        )
        if response.status_code != 200:
            return None
        data = response.json()
        try:
            return data["chess_rapid"]["last"]["rating"]
        except (KeyError, TypeError):
            return None


async def get_user_info(username: str) -> dict:
    """Search for user profile information."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/player/{username}",
            headers={"User-Agent": "ChessOpeningsCoachBot/1.0"},
        )

        if response.status_code == 404:
            return None

        return response.json()
