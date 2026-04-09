import httpx

BASE_URL = "https://api.chess.com/pub"

async def get_recent_games(username: str, num_months: int = 1) -> list:
    """Search for recent games played by a Chess.com user."""
    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{BASE_URL}/player/{username}/games/archives",
            headers={"User-Agent": "ChessOpeningsCoachBot/1.0"}
        )

        if response.status_code == 404:
            return None

        archives = response.json().get("archives", [])

        if not archives:
            return []

        recent_archives = archives[-num_months:]
        all_games = []

        for archive_url in recent_archives:
            resp = await client.get(
                archive_url,
                headers={"User-Agent": "ChessOpeningsCoachBot/1.0"}
            )
            games = resp.json().get("games", [])
            all_games.extend(games)

    return all_games


async def get_user_info(username: str) -> dict:
    """Search for user profile information."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/player/{username}",
            headers={"User-Agent": "ChessOpeningsCoachBot/1.0"}
        )

        if response.status_code == 404:
            return None

        return response.json()