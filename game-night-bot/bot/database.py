import json
import logging

import aiosqlite

from bot import config

logger = logging.getLogger(__name__)


async def init_db():
    """Create tables if they don't exist."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                rawg_id INTEGER,
                rawg_slug TEXT,
                cover_url TEXT,
                genre_tags TEXT,
                added_by TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES games(id),
                played_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logged_by TEXT,
                notes TEXT
            );
        """)
        await db.commit()


# ---------------------------------------------------------------------------
# Game operations
# ---------------------------------------------------------------------------

def _parse_game(row) -> dict:
    d = dict(row)
    d["genre_tags"] = json.loads(d.get("genre_tags") or "[]")
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
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO games
               (guild_id, name, rawg_id, rawg_slug, cover_url, genre_tags, added_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (guild_id, name, rawg_id, rawg_slug, cover_url, json.dumps(genre_tags), added_by),
        )
        await db.commit()
        return cursor.lastrowid


async def remove_game(guild_id: int, game_id: int):
    """Delete a game and its sessions from the rotation."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "DELETE FROM sessions WHERE game_id = ? AND game_id IN (SELECT id FROM games WHERE guild_id = ?)",
            (game_id, guild_id),
        )
        await db.execute(
            "DELETE FROM games WHERE id = ? AND guild_id = ?",
            (game_id, guild_id),
        )
        await db.commit()


async def game_exists_by_rawg_id(guild_id: int, rawg_id: int) -> bool:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM games WHERE guild_id = ? AND rawg_id = ?", (guild_id, rawg_id)
        )
        return await cursor.fetchone() is not None


async def get_games(guild_id: int) -> list[dict]:
    """All games in the rotation for a guild, ordered by name."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM games WHERE guild_id = ? ORDER BY name ASC",
            (guild_id,),
        )
        return [_parse_game(row) for row in await cursor.fetchall()]


async def get_game_stats(guild_id: int) -> list[dict]:
    """All games with last_played date and session_count, ordered by last_played desc."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT g.*,
                      COUNT(s.id) AS session_count,
                      MAX(s.played_on) AS last_played
               FROM games g
               LEFT JOIN sessions s ON s.game_id = g.id
               WHERE g.guild_id = ?
               GROUP BY g.id
               ORDER BY last_played DESC NULLS LAST, g.name ASC""",
            (guild_id,),
        )
        return [_parse_game(row) for row in await cursor.fetchall()]


async def search_games(guild_id: int, name: str) -> list[dict]:
    """Search games by partial name for autocomplete."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, name FROM games WHERE guild_id = ? AND name LIKE ? ORDER BY name ASC LIMIT 25",
            (guild_id, f"%{name}%"),
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_game_by_id(guild_id: int, game_id: int) -> dict | None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM games WHERE id = ? AND guild_id = ?",
            (game_id, guild_id),
        )
        row = await cursor.fetchone()
        return _parse_game(row) if row else None


# ---------------------------------------------------------------------------
# Session operations
# ---------------------------------------------------------------------------

async def log_session(game_id: int, logged_by: str, notes: str | None = None) -> int:
    """Log a session. Returns the new total session count for that game."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT INTO sessions (game_id, logged_by, notes) VALUES (?, ?, ?)",
            (game_id, logged_by, notes),
        )
        cursor = await db.execute(
            "SELECT COUNT(*) FROM sessions WHERE game_id = ?",
            (game_id,),
        )
        count = (await cursor.fetchone())[0]
        await db.commit()
        return count
