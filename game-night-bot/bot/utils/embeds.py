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


def game_added(game_data: dict, crossplay_result: dict, confidence: str) -> discord.Embed:
    emoji = get_primary_emoji(game_data.get("genres", []))
    confidence_icon = {"high": "✅", "medium": "⚠️", "low": "❓"}.get(confidence, "✅")
    embed = discord.Embed(
        title=f"{emoji} {game_data['name']} — On Da Bench Now, Git!",
        color=discord.Color.green(),
    )
    genres_str = ", ".join(game_data.get("genres", [])) or "Unknown"
    embed.add_field(name="Genle", value=genres_str, inline=True)
    embed.add_field(
        name="Cwossplay",
        value=f"{confidence_icon} Velified ({confidence} confidence)",
        inline=True,
    )
    if crossplay_result.get("source"):
        embed.add_field(name="Soulce", value=crossplay_result["source"][:200], inline=False)
    if crossplay_result.get("notes"):
        embed.add_field(name="Note", value=crossplay_result["notes"][:200], inline=False)
    if game_data.get("cover_url"):
        embed.set_image(url=game_data["cover_url"])
    return embed


def crossplay_rejected(game_data: dict, crossplay_result: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"❌ {game_data['name']} — No Cwossplay, You Son of Bitch!",
        description="Dis game no support Xbox ↔ PC cwossplay. Cannot add. Git out!",
        color=discord.Color.red(),
    )
    if crossplay_result.get("notes"):
        embed.add_field(name="Detail", value=crossplay_result["notes"][:300], inline=False)
    if crossplay_result.get("source"):
        embed.add_field(name="Soulce", value=crossplay_result["source"][:200], inline=False)
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
        lines.append("▶ **NOW PLAYING**   *(nobody pwaying! Git out and use `/advance`!)*")

    lines.append(SEP)

    if queue:
        for i, g in enumerate(queue):
            emoji = get_primary_emoji(g.get("genre_tags", []))
            prefix = "   **UP NEXT**      " if i == 0 else "                   "
            lines.append(f"{prefix}{g['name']}   {emoji}")
    else:
        lines.append("   **UP NEXT**      *(queue empty, add some game!)*")

    lines.append(SEP)

    if bench:
        for i, g in enumerate(bench):
            emoji = get_primary_emoji(g.get("genre_tags", []))
            votes = g.get("vote_count", 0)
            prefix = "   **BENCH**        " if i == 0 else "                   "
            vote_str = f"  ({votes} votes)" if votes > 0 else ""
            lines.append(f"{prefix}{g['name']}   {emoji}{vote_str}")
    else:
        lines.append("   **BENCH**        *(empty — use /add-game, dammit!)*")

    if cooldown:
        lines.append(SEP)
        for i, g in enumerate(cooldown):
            weeks = g.get("weeks_remaining", 0)
            prefix = "⏳ **COOLDOWN**     " if i == 0 else "                   "
            lines.append(f"{prefix}{g['name']}   ({weeks}w left)")

    lines.append(SEP)

    embed = discord.Embed(
        title="🎮 City Wok Game Night Lotation",
        description="\n".join(lines),
        color=discord.Color.gold(),
    )
    if active and active.get("cover_url"):
        embed.set_thumbnail(url=active["cover_url"])
    return embed


def rotation_advanced(result: dict) -> discord.Embed:
    if result.get("error"):
        return discord.Embed(
            title="❌ Lotation Fail, Dammit!",
            description=result["error"],
            color=discord.Color.red(),
        )
    prev = result.get("previous", "Unknown")
    next_game = result.get("next")
    from_bench = result.get("from_bench", False)
    if next_game:
        source = " *(flom bench)*" if from_bench else ""
        transition = f"**{prev}** → cooldown\n" if prev else ""
        desc = f"{transition}**{next_game}**{source} → now pwaying, you bettah show up! 🎮"
    else:
        transition = f"**{prev}** → cooldown\n\n" if prev else ""
        desc = transition + "⚠️ Queue and bench awe empty. Add some game with `/add-game`, you son of bitch!"
    embed = discord.Embed(
        title="🔄 Lotation Move Now!",
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
        title="🪑 Da Bench (Dey Waiting)",
        description="Dese game waiting for lotation. Vote 👍 to move up da line!",
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
        title=f"📜 History Book, Page {page}/{total_pages}",
        color=discord.Color.purple(),
    )
    for s in sessions:
        date = (s.get("played_on") or "")[:10]
        notes = s.get("notes")
        value = f"Wogged by **{s.get('logged_by', '?')}**"
        if notes:
            value += f"\n_{notes}_"
        embed.add_field(
            name=f"{s.get('game_name', '?')} — {date}",
            value=value,
            inline=False,
        )
    return embed


def stats_board(stats: dict) -> discord.Embed:
    embed = discord.Embed(title="📊 City Wok Game Stats", color=discord.Color.teal())
    embed.add_field(name="Total Session", value=str(stats.get("total_sessions", 0)), inline=True)
    most_played = stats.get("most_played")
    if most_played:
        embed.add_field(
            name="Most Pwayed",
            value=f"{most_played['name']} ({most_played['count']} session)",
            inline=True,
        )
    per_game = stats.get("per_game", [])
    if per_game:
        lines = [
            f"**{g['name']}**: {g['total_sessions']} session  *(added by {g['added_by']})*"
            for g in per_game[:15]
        ]
        embed.add_field(name="Per Game", value="\n".join(lines), inline=False)
    return embed
