import discord

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

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


def get_primary_emoji(genre_tags: list) -> str:
    for tag in genre_tags:
        emoji = GENRE_EMOJIS.get(tag.lower())
        if emoji:
            return emoji
    return "🎮"


def rawg_matches(matches: list[dict], query: str) -> discord.Embed:
    embed = discord.Embed(
        title=f'🔍 I find dese game for you, "{query}"',
        description="Pick da light one, dammit:",
        color=discord.Color.blurple(),
    )
    for i, m in enumerate(matches, 1):
        year = (m.get("released") or "")[:4]
        platforms_str = ", ".join(m["platforms"][:4]) if m["platforms"] else "Unknown"
        genres_str = ", ".join(m["genres"][:3]) if m["genres"] else "Unknown"
        embed.add_field(
            name=f"{i}. {m['name']}{f' ({year})' if year else ''}",
            value=f"**Platfolm:** {platforms_str}\n**Genle:** {genres_str}",
            inline=False,
        )
    if matches and matches[0].get("cover_url"):
        embed.set_thumbnail(url=matches[0]["cover_url"])
    return embed


def game_added(game_data: dict) -> discord.Embed:
    emoji = get_primary_emoji(game_data.get("genres", []))
    embed = discord.Embed(
        title=f"{emoji} {game_data['name']} — Added to Lotation!",
        color=discord.Color.green(),
    )
    genres_str = ", ".join(game_data.get("genres", [])) or "Unknown"
    embed.add_field(name="Genle", value=genres_str, inline=True)
    if game_data.get("released") and game_data["released"] != "unknown":
        embed.add_field(name="Released", value=game_data["released"][:4], inline=True)
    if game_data.get("cover_url"):
        embed.set_image(url=game_data["cover_url"])
    return embed


def rotation_board(games: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title="🎮 City Wok Game Night Lotation",
        color=discord.Color.gold(),
    )
    if not games:
        embed.description = "No game in da lotation! Use `/add-game`, you son of bitch!"
        return embed

    lines = [SEP]
    for g in games:
        emoji = get_primary_emoji(g.get("genre_tags", []))
        session_count = g.get("session_count", 0)
        last_played = g.get("last_played")
        if last_played:
            date_str = str(last_played)[:10]
        else:
            date_str = "never"
        lines.append(f"{emoji} **{g['name']}**")
        lines.append(f"   └ {session_count} session{'s' if session_count != 1 else ''}  •  last pwayed: {date_str}")
    lines.append(SEP)

    embed.description = "\n".join(lines)
    return embed
