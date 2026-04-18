import math

import discord

from bot import config

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


# ---------------------------------------------------------------------------
# /add-game flow
# ---------------------------------------------------------------------------

def rawg_matches(matches: list[dict], query: str) -> discord.Embed:
    embed = discord.Embed(
        title=f'🔍 Search Results for "{query}"',
        description="Select the correct game below:",
        color=discord.Color.blurple(),
    )
    for i, m in enumerate(matches, 1):
        year = (m.get("released") or "")[:4]
        platforms_str = ", ".join(m["platforms"][:4]) if m["platforms"] else "Unknown"
        genres_str = ", ".join(m["genres"][:3]) if m["genres"] else "Unknown"
        embed.add_field(
            name=f"{i}. {m['name']}{f' ({year})' if year else ''}",
            value=f"**Platforms:** {platforms_str}\n**Genres:** {genres_str}",
            inline=False,
        )
    if matches and matches[0].get("cover_url"):
        embed.set_thumbnail(url=matches[0]["cover_url"])
    return embed


def game_added(game_data: dict, crossplay_result: dict, confidence: str) -> discord.Embed:
    emoji = get_primary_emoji(game_data.get("genres", []))
    confidence_icon = {"high": "✅", "medium": "⚠️", "low": "❓"}.get(confidence, "✅")
    embed = discord.Embed(
        title=f"{emoji} {game_data['name']} — Added to Bench",
        color=discord.Color.green(),
    )
    genres_str = ", ".join(game_data.get("genres", [])) or "Unknown"
    embed.add_field(name="Genres", value=genres_str, inline=True)
    embed.add_field(
        name="Crossplay",
        value=f"{confidence_icon} Verified ({confidence} confidence)",
        inline=True,
    )
    if crossplay_result.get("source"):
        embed.add_field(name="Source", value=crossplay_result["source"][:200], inline=False)
    if crossplay_result.get("notes"):
        embed.add_field(name="Notes", value=crossplay_result["notes"][:200], inline=False)
    if game_data.get("cover_url"):
        embed.set_image(url=game_data["cover_url"])
    return embed


def crossplay_rejected(game_data: dict, crossplay_result: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"❌ {game_data['name']} — Crossplay Not Supported",
        description="This game does not support Xbox Console ↔ PC crossplay and cannot be added.",
        color=discord.Color.red(),
    )
    if crossplay_result.get("notes"):
        embed.add_field(name="Details", value=crossplay_result["notes"][:300], inline=False)
    if crossplay_result.get("source"):
        embed.add_field(name="Source", value=crossplay_result["source"][:200], inline=False)
    if game_data.get("cover_url"):
        embed.set_image(url=game_data["cover_url"])
    return embed


# ---------------------------------------------------------------------------
# /rotation
# ---------------------------------------------------------------------------

def rotation_board(active, queue, bench, cooldown) -> discord.Embed:
    lines = [SEP]

    if active:
        emoji = get_primary_emoji(active.get("genre_tags", []))
        sc = active.get("session_count", 0)
        lines.append(
            f"▶ **NOW PLAYING**   {active['name']}   "
            f"[Session {sc} of {config.MIN_SESSIONS} min] {emoji}"
        )
    else:
        lines.append("▶ **NOW PLAYING**   *(none — use `/advance`)*")

    lines.append(SEP)

    if queue:
        for i, g in enumerate(queue):
            emoji = get_primary_emoji(g.get("genre_tags", []))
            prefix = "   **UP NEXT**      " if i == 0 else "                   "
            lines.append(f"{prefix}{g['name']}   {emoji}")
    else:
        lines.append("   **UP NEXT**      *(queue empty)*")

    lines.append(SEP)

    if bench:
        for i, g in enumerate(bench):
            emoji = get_primary_emoji(g.get("genre_tags", []))
            votes = g.get("vote_count", 0)
            prefix = "   **BENCH**        " if i == 0 else "                   "
            vote_str = f"  ({votes} votes)" if votes > 0 else ""
            lines.append(f"{prefix}{g['name']}   {emoji}{vote_str}")
    else:
        lines.append("   **BENCH**        *(empty)*")

    if cooldown:
        lines.append(SEP)
        for i, g in enumerate(cooldown):
            weeks = g.get("weeks_remaining", 0)
            prefix = "⏳ **COOLDOWN**     " if i == 0 else "                   "
            lines.append(f"{prefix}{g['name']}   ({weeks}w left)")

    lines.append(SEP)

    embed = discord.Embed(
        title="🎮 Thursday Night Rotation",
        description="\n".join(lines),
        color=discord.Color.gold(),
    )
    if active and active.get("cover_url"):
        embed.set_thumbnail(url=active["cover_url"])
    return embed


def rotation_advanced(result: dict) -> discord.Embed:
    if result.get("error"):
        return discord.Embed(
            title="❌ Advance Failed",
            description=result["error"],
            color=discord.Color.red(),
        )
    prev = result.get("previous", "Unknown")
    next_game = result.get("next")
    from_bench = result.get("from_bench", False)
    if next_game:
        source = " *(from bench)*" if from_bench else ""
        transition = f"**{prev}** → cooldown\n" if prev else ""
        desc = f"{transition}**{next_game}**{source} → now playing! 🎮"
    else:
        transition = f"**{prev}** → cooldown\n\n" if prev else ""
        desc = transition + "⚠️ Queue and bench are empty. Add more games with `/add-game`!"
    embed = discord.Embed(
        title="🔄 Rotation Advanced",
        description=desc,
        color=discord.Color.green(),
    )
    cover = result.get("next_cover_url")
    if cover:
        embed.set_image(url=cover)
    return embed


# ---------------------------------------------------------------------------
# /bench
# ---------------------------------------------------------------------------

def bench_list(bench_games: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title="🪑 Bench",
        description="Games waiting to join the rotation. Vote 👍 to prioritize!",
        color=discord.Color.blue(),
    )
    for g in bench_games:
        emoji = get_primary_emoji(g.get("genre_tags", []))
        votes = g.get("vote_count", 0)
        embed.add_field(
            name=f"{emoji} {g['name']}",
            value=f"👍 {votes} vote{'s' if votes != 1 else ''} | Added by {g.get('added_by', '?')}",
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# /history & /stats
# ---------------------------------------------------------------------------

def session_history(sessions: list[dict], page: int, total_pages: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"📜 Session History  (page {page}/{total_pages})",
        color=discord.Color.purple(),
    )
    for s in sessions:
        date = (s.get("played_on") or "")[:10]
        notes = s.get("notes")
        value = f"Logged by **{s.get('logged_by', '?')}**"
        if notes:
            value += f"\n_{notes}_"
        embed.add_field(
            name=f"{s.get('game_name', '?')} — {date}",
            value=value,
            inline=False,
        )
    return embed


def stats_board(stats: dict) -> discord.Embed:
    embed = discord.Embed(title="📊 Rotation Stats", color=discord.Color.teal())
    embed.add_field(name="Total Sessions", value=str(stats.get("total_sessions", 0)), inline=True)
    most_played = stats.get("most_played")
    if most_played:
        embed.add_field(
            name="Most Played",
            value=f"{most_played['name']} ({most_played['count']} sessions)",
            inline=True,
        )
    per_game = stats.get("per_game", [])
    if per_game:
        lines = [
            f"**{g['name']}**: {g['total_sessions']} sessions  *(added by {g['added_by']})*"
            for g in per_game[:15]
        ]
        embed.add_field(name="Per Game", value="\n".join(lines), inline=False)
    return embed
