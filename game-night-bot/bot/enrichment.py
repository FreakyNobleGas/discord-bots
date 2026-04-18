import json
import logging

import httpx
import anthropic

from bot import config

logger = logging.getLogger(__name__)

RAWG_SEARCH_URL = "https://api.rawg.io/api/games"

CROSSPLAY_SYSTEM_PROMPT = (
    "You are a gaming research assistant. Given game metadata, determine whether the game "
    "supports Xbox Console <-> PC crossplay for co-op multiplayer.\n"
    "Return ONLY valid JSON, no markdown, no code blocks:\n"
    '{"crossplay": true or false, "confidence": "high" or "medium" or "low", '
    '"source": "URL or brief note", "notes": "any caveats"}'
)


async def search_rawg(name: str) -> list[dict]:
    """Search RAWG and return up to 3 match dicts."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            RAWG_SEARCH_URL,
            params={"search": name, "key": config.RAWG_API_KEY, "page_size": 5},
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for game in data.get("results", [])[:3]:
        platforms = [p["platform"]["name"] for p in (game.get("platforms") or [])]
        genres = [g["name"] for g in (game.get("genres") or [])]
        results.append({
            "id": game["id"],
            "slug": game.get("slug", ""),
            "name": game["name"],
            "cover_url": game.get("background_image") or "",
            "genres": genres,
            "platforms": platforms,
            "released": game.get("released") or "unknown",
        })
    return results


async def check_crossplay(game_data: dict) -> dict:
    """
    Call Claude with web_search to verify Xbox <-> PC crossplay.
    Returns dict: {crossplay, confidence, source, notes}.
    """
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    user_content = (
        f'Check if "{game_data["name"]}" supports Xbox Console <-> PC crossplay '
        f"for co-op multiplayer.\n\n"
        f"RAWG metadata:\n"
        f"- Name: {game_data['name']}\n"
        f"- Platforms: {', '.join(game_data['platforms'])}\n"
        f"- Genres: {', '.join(game_data['genres'])}\n"
        f"- Released: {game_data.get('released', 'unknown')}\n\n"
        f"Search the web to verify current crossplay status, then return ONLY valid JSON "
        f"(no markdown, no code fences):\n"
        f'{{"crossplay": true or false, "confidence": "high"|"medium"|"low", '
        f'"source": "URL or brief note", "notes": "any caveats"}}'
    )

    messages = [{"role": "user", "content": user_content}]

    for _ in range(10):  # safety iteration cap
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=CROSSPLAY_SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    text = block.text.strip()
                    # Strip markdown code fences if Claude adds them anyway
                    if "```" in text:
                        parts = text.split("```")
                        for part in parts:
                            part = part.strip()
                            if part.startswith("json"):
                                part = part[4:].strip()
                            try:
                                return json.loads(part)
                            except json.JSONDecodeError:
                                continue
                    return json.loads(text)
            raise ValueError("No text block in Claude end_turn response")

        # Build tool_result continuations for any tool_use blocks
        tool_results = [
            {"type": "tool_result", "tool_use_id": block.id, "content": "Search complete."}
            for block in response.content
            if hasattr(block, "type") and block.type == "tool_use"
        ]
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    raise ValueError("Claude did not return a crossplay result within the iteration limit.")
