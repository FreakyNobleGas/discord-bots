import discord
from datetime import datetime

from bot.locale import t

GENRE_EMOJIS: dict[str, str] = {
    "shooter": "🔫",
    "horror": "👻",
    "simulation": "🔬",
    "automation": "🔬",
    "action": "⚔️",
    "rpg": "🎭",
    "strategy": "♟️",
    "sports": "⚽",
    "racing": "🏎️",
    "puzzle": "🧩",
    "adventure": "🗺️",
    "survival": "🏕️",
    "indie": "🎨",
    "arcade": "🕹️",
    "fighting": "🥊",
    "platformer": "🦘",
    "card": "🃏",
    "sci-fi": "🚀",
    "co-op": "🤝",
    "massively multiplayer": "🌐",
}

# Tags that are too broad to be useful as a primary identifier
_GENERIC_TAGS = {"action", "adventure", "indie"}

# Per-game overrides for games RAWG doesn't tag specifically enough
GAME_OVERRIDES: dict[str, str] = {
    "phasmophobia": "👻",
    "content warning": "📹",
    "helldivers 2": "🪖",
    "warhammer 40,000: space marine ii": "🪖",
    "toxic commando": "☣️",
    "diablo iv": "😈",
    "abiotic factor": "🧪",
    "roadside research": "🗺️",
    "halo infinite": "🔫",
    "the first descendant": "🔫",
}

def get_primary_emoji(genre_tags: list, game_name: str = "") -> str:
    if game_name:
        override = GAME_OVERRIDES.get(game_name.lower())
        if override:
            return override
    # Prefer specific tags over generic ones
    for tag in genre_tags:
        if tag.lower() not in _GENERIC_TAGS:
            emoji = GENRE_EMOJIS.get(tag.lower())
            if emoji:
                return emoji
    # Fall back to generic tags
    for tag in genre_tags:
        emoji = GENRE_EMOJIS.get(tag.lower())
        if emoji:
            return emoji
    return "🎮"


def rawg_matches(matches: list[dict], query: str) -> discord.Embed:
    embed = discord.Embed(
        title=t("search_title", query=query),
        description=t("search_description"),
        color=discord.Color.blurple(),
    )
    for i, m in enumerate(matches, 1):
        year = (m.get("released") or "")[:4]
        platforms_str = ", ".join(m["platforms"][:4]) if m["platforms"] else "Unknown"
        genres_str = ", ".join(m["genres"][:3]) if m["genres"] else "Unknown"
        embed.add_field(
            name=f"{i}. {m['name']}{f' ({year})' if year else ''}",
            value=f"**Platform:** {platforms_str}\n**Genre:** {genres_str}",
            inline=False,
        )
    if matches and matches[0].get("cover_url"):
        embed.set_thumbnail(url=matches[0]["cover_url"])
    return embed


def game_added(game_data: dict) -> discord.Embed:
    emoji = get_primary_emoji(game_data.get("genres", []), game_data.get("name", ""))
    embed = discord.Embed(
        title=t("game_added_title", emoji=emoji, name=game_data["name"]),
        color=discord.Color.green(),
    )
    genres_str = ", ".join(game_data.get("genres", [])) or "Unknown"
    embed.add_field(name="Genre", value=genres_str, inline=True)
    if game_data.get("released") and game_data["released"] != "unknown":
        embed.add_field(name="Released", value=game_data["released"][:4], inline=True)
    if game_data.get("cover_url"):
        embed.set_image(url=game_data["cover_url"])
    return embed


def _fmt_date(last_played) -> str:
    if not last_played:
        return "never"
    try:
        dt = datetime.strptime(str(last_played)[:10], "%Y-%m-%d")
        return dt.strftime("%b %-d")
    except ValueError:
        return str(last_played)[:10]


def rotation_board(games: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title=t("rotation_title"),
        color=discord.Color.gold(),
    )
    if not games:
        embed.description = t("rotation_empty")
        return embed

    entries = []
    for i, g in enumerate(games, 1):
        emoji = get_primary_emoji(g.get("genre_tags", []), g.get("name", ""))
        session_count = g.get("session_count", 0)
        plays = f"{session_count} play{'s' if session_count != 1 else ''}"
        date_str = _fmt_date(g.get("last_played"))
        entries.append(f"{emoji} **{i}. {g['name']}**\n-# {plays} · {date_str}")

    embed.description = "\n\n".join(entries)
    return embed
