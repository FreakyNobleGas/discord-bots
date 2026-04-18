import json
import math
import logging
from datetime import datetime, timedelta
from typing import Optional

import aiosqlite

from bot import config

logger = logging.getLogger(__name__)


async def init_db():
    """Create all tables if they don't exist."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rawg_id INTEGER,
                rawg_slug TEXT,
                cover_url TEXT,
                genre_tags TEXT,
                crossplay_verified BOOLEAN NOT NULL DEFAULT 0,
                crossplay_confidence TEXT,
                crossplay_source TEXT,
                added_by TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rotation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES games(id),
                status TEXT NOT NULL,
                position INTEGER,
                session_count INTEGER DEFAULT 0,
                entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exited_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES games(id),
                played_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logged_by TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES games(id),
                vote_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_id, vote_type, user_id)
            );
        """)
        await db.commit()


async def refresh_cooldowns():
    """Move games whose cooldown period has expired back to bench."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cutoff = (datetime.utcnow() - timedelta(weeks=config.COOLDOWN_WEEKS)).isoformat()
        await db.execute(
            "UPDATE rotation SET status='bench', position=NULL WHERE status='cooldown' AND exited_at <= ?",
            (cutoff,),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Game operations
# ---------------------------------------------------------------------------

async def add_game(
    name: str,
    rawg_id: int,
    rawg_slug: str,
    cover_url: str,
    genre_tags: list,
    crossplay_verified: bool,
    crossplay_confidence: str,
    crossplay_source: str,
    added_by: str,
) -> int:
    """Insert a game and a bench rotation entry. Returns the new game_id."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO games
               (name, rawg_id, rawg_slug, cover_url, genre_tags,
                crossplay_verified, crossplay_confidence, crossplay_source, added_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name, rawg_id, rawg_slug, cover_url, json.dumps(genre_tags),
                int(crossplay_verified), crossplay_confidence, crossplay_source, added_by,
            ),
        )
        game_id = cursor.lastrowid
        await db.execute(
            "INSERT INTO rotation (game_id, status) VALUES (?, 'bench')",
            (game_id,),
        )
        await db.commit()
        return game_id


async def game_exists_by_rawg_id(rawg_id: int) -> bool:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("SELECT 1 FROM games WHERE rawg_id = ?", (rawg_id,))
        return await cursor.fetchone() is not None


async def find_games_by_name(name: str) -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, name FROM games WHERE name LIKE ?", (f"%{name}%",)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def retire_game(game_id: int):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """UPDATE rotation SET status='retired', exited_at=CURRENT_TIMESTAMP
               WHERE game_id=? AND status NOT IN ('retired')""",
            (game_id,),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Rotation read operations
# ---------------------------------------------------------------------------

def _parse_row(row) -> dict:
    d = dict(row)
    d["genre_tags"] = json.loads(d.get("genre_tags") or "[]")
    return d


async def get_active() -> Optional[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT g.*, r.id as rotation_id, r.session_count, r.entered_at
            FROM rotation r
            JOIN games g ON r.game_id = g.id
            WHERE r.status = 'active'
            LIMIT 1
        """)
        row = await cursor.fetchone()
        return _parse_row(row) if row else None


async def get_queue() -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT g.*, r.id as rotation_id, r.position, r.session_count
            FROM rotation r
            JOIN games g ON r.game_id = g.id
            WHERE r.status = 'queue'
            ORDER BY r.position ASC
        """)
        return [_parse_row(row) for row in await cursor.fetchall()]


async def get_bench() -> list[dict]:
    """Bench games sorted by vote count descending."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT g.*, r.id as rotation_id,
                   COUNT(v.id) as vote_count
            FROM rotation r
            JOIN games g ON r.game_id = g.id
            LEFT JOIN votes v ON v.game_id = g.id AND v.vote_type = 'bench_up'
            WHERE r.status = 'bench'
            GROUP BY g.id
            ORDER BY vote_count DESC
        """)
        return [_parse_row(row) for row in await cursor.fetchall()]


async def get_cooldown() -> list[dict]:
    """Cooldown games with weeks_remaining calculated."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT g.*, r.id as rotation_id, r.exited_at
            FROM rotation r
            JOIN games g ON r.game_id = g.id
            WHERE r.status = 'cooldown'
        """)
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = _parse_row(row)
        if d.get("exited_at"):
            exited = datetime.fromisoformat(d["exited_at"])
            expiry = exited + timedelta(weeks=config.COOLDOWN_WEEKS)
            d["weeks_remaining"] = max(0, math.ceil((expiry - datetime.utcnow()).days / 7))
        else:
            d["weeks_remaining"] = config.COOLDOWN_WEEKS
        result.append(d)
    return result


async def get_queue_genres() -> list[str]:
    """Primary genres of active + queued games in play order."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT g.genre_tags
            FROM rotation r
            JOIN games g ON r.game_id = g.id
            WHERE r.status IN ('active', 'queue')
            ORDER BY CASE r.status WHEN 'active' THEN 0 ELSE 1 END, r.position
        """)
        rows = await cursor.fetchall()
    genres = []
    for row in rows:
        tags = json.loads(row["genre_tags"] or "[]")
        if tags:
            genres.append(tags[0])
    return genres


# ---------------------------------------------------------------------------
# Rotation write operations
# ---------------------------------------------------------------------------

async def advance_rotation() -> dict:
    """
    Move active game to cooldown, promote next queue or bench game to active.
    Returns a summary dict: {previous, next, from_bench}.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("""
            SELECT r.id, r.game_id, g.name FROM rotation r
            JOIN games g ON g.id = r.game_id
            WHERE r.status = 'active'
        """)
        active = await cursor.fetchone()

        if active:
            await db.execute(
                "UPDATE rotation SET status='cooldown', exited_at=CURRENT_TIMESTAMP WHERE id=?",
                (active["id"],),
            )

        # Try queue first
        from_bench = False
        cursor = await db.execute("""
            SELECT r.id, r.game_id, g.name, g.cover_url FROM rotation r
            JOIN games g ON g.id = r.game_id
            WHERE r.status = 'queue'
            ORDER BY r.position ASC
            LIMIT 1
        """)
        next_game = await cursor.fetchone()

        if not next_game:
            from_bench = True
            cursor = await db.execute("""
                SELECT r.id, r.game_id, g.name, g.cover_url, COUNT(v.id) as vote_count
                FROM rotation r
                JOIN games g ON g.id = r.game_id
                LEFT JOIN votes v ON v.game_id = g.id AND v.vote_type = 'bench_up'
                WHERE r.status = 'bench'
                GROUP BY r.id
                ORDER BY vote_count DESC
                LIMIT 1
            """)
            next_game = await cursor.fetchone()

        if not next_game:
            await db.commit()
            return {"previous": active["name"] if active else None, "next": None, "from_bench": False}

        await db.execute(
            "UPDATE rotation SET status='active', position=NULL, entered_at=CURRENT_TIMESTAMP WHERE id=?",
            (next_game["id"],),
        )

        # Re-number remaining queue positions
        cursor = await db.execute(
            "SELECT id FROM rotation WHERE status='queue' ORDER BY position ASC"
        )
        queue_rows = await cursor.fetchall()
        for i, row in enumerate(queue_rows):
            await db.execute("UPDATE rotation SET position=? WHERE id=?", (i + 1, row["id"]))

        await db.commit()
        return {
            "previous": active["name"] if active else None,
            "next": next_game["name"],
            "next_cover_url": next_game["cover_url"] or "",
            "from_bench": from_bench,
        }


# ---------------------------------------------------------------------------
# Session operations
# ---------------------------------------------------------------------------

async def log_session(game_id: int, logged_by: str, notes: Optional[str] = None) -> int:
    """Log a session and increment active rotation session_count. Returns new count."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT INTO sessions (game_id, logged_by, notes) VALUES (?, ?, ?)",
            (game_id, logged_by, notes),
        )
        await db.execute(
            "UPDATE rotation SET session_count = session_count + 1 WHERE game_id=? AND status='active'",
            (game_id,),
        )
        cursor = await db.execute(
            "SELECT session_count FROM rotation WHERE game_id=? AND status='active'",
            (game_id,),
        )
        row = await cursor.fetchone()
        await db.commit()
        return row[0] if row else 0


async def get_sessions_paginated(page: int = 1, per_page: int = 10) -> tuple:
    """Returns (sessions_list, total_count)."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        offset = (page - 1) * per_page
        cursor = await db.execute("SELECT COUNT(*) FROM sessions")
        total = (await cursor.fetchone())[0]
        cursor = await db.execute("""
            SELECT s.*, g.name as game_name
            FROM sessions s
            JOIN games g ON s.game_id = g.id
            ORDER BY s.played_on DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows], total


async def get_stats() -> dict:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT g.name, COUNT(s.id) as cnt
            FROM sessions s JOIN games g ON s.game_id = g.id
            GROUP BY g.id ORDER BY cnt DESC LIMIT 1
        """)
        row = await cursor.fetchone()
        most_played = {"name": row[0], "count": row[1]} if row else None

        cursor = await db.execute("""
            SELECT g.name, g.added_by, g.added_at, COUNT(s.id) as total_sessions
            FROM games g
            LEFT JOIN sessions s ON s.game_id = g.id
            GROUP BY g.id
            ORDER BY total_sessions DESC
        """)
        rows = await cursor.fetchall()
        per_game = [
            {"name": r[0], "added_by": r[1], "added_at": r[2], "total_sessions": r[3]}
            for r in rows
        ]

        return {
            "total_sessions": total_sessions,
            "most_played": most_played,
            "per_game": per_game,
        }


# ---------------------------------------------------------------------------
# Vote operations
# ---------------------------------------------------------------------------

async def add_vote(game_id: int, vote_type: str, user_id: str) -> bool:
    """Returns True if vote was recorded, False if duplicate."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO votes (game_id, vote_type, user_id) VALUES (?, ?, ?)",
                (game_id, vote_type, user_id),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_vote_count(game_id: int, vote_type: str) -> int:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM votes WHERE game_id=? AND vote_type=?",
            (game_id, vote_type),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def has_voted(game_id: int, vote_type: str, user_id: str) -> bool:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM votes WHERE game_id=? AND vote_type=? AND user_id=?",
            (game_id, vote_type, user_id),
        )
        return await cursor.fetchone() is not None


async def clear_votes(game_id: int, vote_type: str):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "DELETE FROM votes WHERE game_id=? AND vote_type=?",
            (game_id, vote_type),
        )
        await db.commit()
