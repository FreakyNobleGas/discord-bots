"""One-time copy of the bot's old SQLite rotation.db into the shared Postgres database.

Usage (inside the bot container, with DATABASE_URL in .env):
    docker compose run --rm bot uv run python -m scripts.migrate_sqlite_to_postgres /app/data/rotation.db

Keeps the original game and session ids so nothing that refers to them breaks, then moves
the id sequences past them. Refuses to run if Postgres already has games (use --force to
add to them anyway). Everything runs in one transaction: it all lands or nothing does.
"""

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg
from dotenv import load_dotenv

SCHEMA_FILE = Path(__file__).parent.parent / "schema.sql"


def _dsn(url: str) -> str:
    # Same as bot/database.py: asyncpg rejects Neon's channel_binding param.
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    return urlunsplit(parts._replace(query=urlencode(query)))


def _utc(value) -> datetime | None:
    """SQLite CURRENT_TIMESTAMP values are UTC strings like '2026-10-17 01:23:45'."""
    if value is None:
        return None
    dt = datetime.fromisoformat(str(value))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def read_sqlite(path: str) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    games = db.execute("SELECT * FROM games ORDER BY id").fetchall()
    sessions = db.execute("SELECT * FROM sessions ORDER BY id").fetchall()
    db.close()
    return games, sessions


async def migrate(sqlite_path: str, force: bool):
    games, sessions = read_sqlite(sqlite_path)
    game_ids = {g["id"] for g in games}
    orphans = [s for s in sessions if s["game_id"] not in game_ids]
    sessions = [s for s in sessions if s["game_id"] in game_ids]

    conn = await asyncpg.connect(_dsn(os.environ["DATABASE_URL"]))
    try:
        await conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
        existing = await conn.fetchval("SELECT COUNT(*) FROM games")
        if existing and not force:
            sys.exit(f"Postgres already has {existing} games. Re-run with --force to add to them.")

        async with conn.transaction():
            await conn.executemany(
                """INSERT INTO games
                   (id, guild_id, name, rawg_id, rawg_slug, cover_url, genre_tags, added_by, added_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9)""",
                [
                    (
                        g["id"],
                        int(g["guild_id"]),
                        g["name"],
                        g["rawg_id"],
                        g["rawg_slug"],
                        g["cover_url"] or "",
                        json.dumps(json.loads(g["genre_tags"] or "[]")),
                        g["added_by"],
                        _utc(g["added_at"]) or datetime.now(timezone.utc),
                    )
                    for g in games
                ],
            )
            await conn.executemany(
                """INSERT INTO sessions (id, game_id, played_on, logged_by, notes)
                   VALUES ($1, $2, $3, $4, $5)""",
                [
                    (
                        s["id"],
                        s["game_id"],
                        _utc(s["played_on"]) or datetime.now(timezone.utc),
                        s["logged_by"],
                        s["notes"],
                    )
                    for s in sessions
                ],
            )
            for table in ("games", "sessions"):
                await conn.execute(
                    f"""SELECT setval(pg_get_serial_sequence('{table}', 'id'),
                                      COALESCE(MAX(id), 1), MAX(id) IS NOT NULL)
                        FROM {table}"""
                )

        pg_games = await conn.fetchval("SELECT COUNT(*) FROM games")
        pg_sessions = await conn.fetchval("SELECT COUNT(*) FROM sessions")
    finally:
        await conn.close()

    print(f"SQLite:   {len(games)} games, {len(sessions) + len(orphans)} sessions")
    print(f"Postgres: {pg_games} games, {pg_sessions} sessions")
    if orphans:
        ids = ", ".join(str(s["id"]) for s in orphans)
        print(f"Skipped {len(orphans)} sessions whose game no longer exists (ids: {ids})")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sqlite_path", help="Path to the old rotation.db")
    parser.add_argument("--force", action="store_true", help="Add to a non-empty database")
    args = parser.parse_args()
    asyncio.run(migrate(args.sqlite_path, args.force))


if __name__ == "__main__":
    main()
