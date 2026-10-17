import json
import logging
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg

from bot import config

logger = logging.getLogger(__name__)

# Shared with the game night website (website/game-night-website). See CLAUDE.md.
_SCHEMA_FILE = Path(__file__).parent.parent / "schema.sql"

_pool: asyncpg.Pool | None = None


def _dsn(url: str) -> str:
    """Drop query params asyncpg doesn't understand (Neon adds channel_binding)."""
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    return urlunsplit(parts._replace(query=urlencode(query)))


async def _init_connection(conn: asyncpg.Connection):
    # Return jsonb columns (genre_tags) as Python lists instead of strings.
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


def _db() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("init_db() has not been called")
    return _pool


async def init_db():
    """Open the connection pool and create tables if they don't exist."""
    global _pool
    _pool = await asyncpg.create_pool(
        _dsn(config.DATABASE_URL),
        # Neon's free plan bills compute while connections are active, and suspends after
        # 5 idle minutes. Hold no idle connections so the database can scale to zero.
        min_size=0,
        max_size=5,
        max_inactive_connection_lifetime=60,
        init=_init_connection,
    )
    await _pool.execute(_SCHEMA_FILE.read_text(encoding="utf-8"))


async def close_db():
    if _pool is not None:
        await _pool.close()


# ---------------------------------------------------------------------------
# Game operations
# ---------------------------------------------------------------------------

def _parse_game(row) -> dict:
    d = dict(row)
    d["genre_tags"] = d.get("genre_tags") or []
    return d


async def add_game(
    guild_id: int,
    name: str,
    rawg_id: int | None,
    rawg_slug: str | None,
    cover_url: str,
    genre_tags: list,
    added_by: str,
) -> int:
    """Insert a game into the rotation. Returns the new game_id."""
    return await _db().fetchval(
        """INSERT INTO games
           (guild_id, name, rawg_id, rawg_slug, cover_url, genre_tags, added_by)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           RETURNING id""",
        guild_id, name, rawg_id, rawg_slug, cover_url, genre_tags, added_by,
    )


async def remove_game(guild_id: int, game_id: int):
    """Delete a game from the rotation. Its sessions and patch notes cascade."""
    await _db().execute(
        "DELETE FROM games WHERE id = $1 AND guild_id = $2",
        game_id, guild_id,
    )


async def game_exists_by_rawg_id(guild_id: int, rawg_id: int) -> bool:
    return await _db().fetchval(
        "SELECT EXISTS (SELECT 1 FROM games WHERE guild_id = $1 AND rawg_id = $2)",
        guild_id, rawg_id,
    )


async def get_games(guild_id: int) -> list[dict]:
    """All games in the rotation for a guild, ordered by name."""
    rows = await _db().fetch(
        "SELECT * FROM games WHERE guild_id = $1 ORDER BY name ASC",
        guild_id,
    )
    return [_parse_game(row) for row in rows]


async def get_game_stats(guild_id: int) -> list[dict]:
    """All games with last_played date and session_count, ordered by last_played desc."""
    rows = await _db().fetch(
        """SELECT g.*,
                  COUNT(s.id) AS session_count,
                  MAX(s.played_on) AS last_played
           FROM games g
           LEFT JOIN sessions s ON s.game_id = g.id
           WHERE g.guild_id = $1
           GROUP BY g.id
           ORDER BY last_played DESC NULLS LAST, g.name ASC""",
        guild_id,
    )
    return [_parse_game(row) for row in rows]


async def search_games(guild_id: int, name: str) -> list[dict]:
    """Search games by partial name for autocomplete."""
    rows = await _db().fetch(
        "SELECT id, name FROM games WHERE guild_id = $1 AND name ILIKE $2 ORDER BY name ASC LIMIT 25",
        guild_id, f"%{name}%",
    )
    return [dict(row) for row in rows]


async def get_game_by_id(guild_id: int, game_id: int) -> dict | None:
    row = await _db().fetchrow(
        "SELECT * FROM games WHERE id = $1 AND guild_id = $2",
        game_id, guild_id,
    )
    return _parse_game(row) if row else None


# ---------------------------------------------------------------------------
# Session operations
# ---------------------------------------------------------------------------

async def log_session(game_id: int, logged_by: str, notes: str | None = None) -> int:
    """Log a session. Returns the new total session count for that game."""
    async with _db().acquire() as conn, conn.transaction():
        await conn.execute(
            "INSERT INTO sessions (game_id, logged_by, notes) VALUES ($1, $2, $3)",
            game_id, logged_by, notes,
        )
        return await conn.fetchval(
            "SELECT COUNT(*) FROM sessions WHERE game_id = $1",
            game_id,
        )
