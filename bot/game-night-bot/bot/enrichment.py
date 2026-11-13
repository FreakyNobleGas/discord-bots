import logging
import time

import httpx

from bot import config

logger = logging.getLogger(__name__)

RAWG_SEARCH_URL = "https://api.rawg.io/api/games"

# Autocomplete fires a search on every keystroke and Discord only waits 3s for
# the answer, so keep one client (connection reuse) and cache recent searches.
_SEARCH_CACHE_TTL = 600
_SEARCH_CACHE_MAX = 256

_http: httpx.AsyncClient | None = None
_search_cache: dict[tuple[str, int], tuple[float, list[dict]]] = {}


def _client() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(timeout=10.0)
    return _http


async def close() -> None:
    global _http
    if _http is not None:
        await _http.aclose()
        _http = None


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


async def search_rawg(name: str, limit: int = 10) -> list[dict]:
    """Search RAWG and return up to `limit` match dicts."""
    key = (name.strip().lower(), limit)
    cached = _search_cache.get(key)
    if cached and time.monotonic() - cached[0] < _SEARCH_CACHE_TTL:
        return cached[1]

    response = await _client().get(
        RAWG_SEARCH_URL,
        params={
            "search": name,
            "key": config.RAWG_API_KEY,
            "page_size": limit,
            "search_precise": "true",
        },
    )
    response.raise_for_status()
    data = response.json()
    results = [_parse_rawg_game(g) for g in data.get("results", [])[:limit]]

    _search_cache.pop(key, None)
    if len(_search_cache) >= _SEARCH_CACHE_MAX:
        _search_cache.pop(next(iter(_search_cache)))
    _search_cache[key] = (time.monotonic(), results)
    return results


async def get_rawg_game_by_id(game_id: int) -> dict:
    """Fetch a specific game from RAWG by ID."""
    response = await _client().get(
        f"{RAWG_SEARCH_URL}/{game_id}",
        params={"key": config.RAWG_API_KEY},
    )
    response.raise_for_status()
    return _parse_rawg_game(response.json())
