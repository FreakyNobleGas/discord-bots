import logging

import httpx

from bot import config

logger = logging.getLogger(__name__)

RAWG_SEARCH_URL = "https://api.rawg.io/api/games"


def _parse_rawg_game(game: dict) -> dict:
    platforms = [p["platform"]["name"] for p in (game.get("platforms") or [])]
    genres = [g["name"] for g in (game.get("genres") or [])]
    return {
        "id": game["id"],
        "slug": game.get("slug", ""),
        "name": game["name"],
        "cover_url": game.get("background_image") or "",
        "genres": genres,
        "platforms": platforms,
        "released": game.get("released") or "unknown",
    }


async def search_rawg(name: str, limit: int = 5) -> list[dict]:
    """Search RAWG and return up to `limit` match dicts."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            RAWG_SEARCH_URL,
            params={"search": name, "key": config.RAWG_API_KEY, "page_size": limit},
        )
        response.raise_for_status()
        data = response.json()
    return [_parse_rawg_game(g) for g in data.get("results", [])[:limit]]


async def get_rawg_game_by_id(game_id: int) -> dict:
    """Fetch a specific game from RAWG by ID."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{RAWG_SEARCH_URL}/{game_id}",
            params={"key": config.RAWG_API_KEY},
        )
        response.raise_for_status()
        return _parse_rawg_game(response.json())
