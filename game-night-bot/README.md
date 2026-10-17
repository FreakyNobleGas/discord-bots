Game Night Bot
==============
A Discord bot for tracking your group's game rotation. Add games, log sessions, and see what's up next — all via slash commands. Game metadata (cover art, genres) is pulled automatically from the RAWG API.

> This bot was built almost entirely using [Claude Code](https://claude.ai/code) by Anthropic.

Commands
--------
`/rotation` — Show the full game rotation ranked by last played date

`/add-game` — Add a game to the rotation (searches RAWG with autocomplete)

`/remove-game` — Remove a game from the rotation

`/log-session` — Log a gaming session for a game

`/help` — Show all available commands

Website
-------
The bot shares its database with the [game night website](../game-night-website): charts of what the crew plays, an API for Grok Bot, and an admin page. When `SITE_URL` is set, the bot adds a "See the stats" button to its replies after `/add-game` and `/log-session`.

Setup
-----
**1. Prerequisites**

- Docker and Docker Compose (or [uv](https://docs.astral.sh/uv/) to run it directly)
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- A RAWG API key ([rawg.io/apidocs](https://rawg.io/apidocs))
- A Postgres database. Production uses Neon, connected to the website's Vercel project.

**2. Configure environment**

Copy `.env.example` to `.env` and fill in your values:

```
cp .env.example .env
```

```
DISCORD_TOKEN=        # Your bot token
DISCORD_GUILD_IDS=    # Comma-separated server IDs, e.g. 123456789,987654321
RAWG_API_KEY=         # Your RAWG API key
DATABASE_URL=         # Neon's DIRECT connection string (host without "-pooler")
SITE_URL=             # Optional: the website URL, adds a link button to replies
```

The bot creates any missing tables on startup from `schema.sql`.

**3. Customize personality (optional)**

Copy `locale.example.json` to `locale.json` and edit the strings to give your bot its own personality. `locale.json` is gitignored so your customizations stay private. Keys you leave out fall back to `locale.example.json`.

```
cp locale.example.json locale.json
```

**4. Run**

```
docker compose up --build -d
```

Or without Docker:

```
uv sync
uv run python -m bot.main
```

Moving from SQLite
------------------
Older versions stored everything in `data/rotation.db`. To copy it into Postgres once:

```
docker compose stop
cp data/rotation.db data/rotation.db.bak
docker compose run --rm bot uv run python -m scripts.migrate_sqlite_to_postgres /app/data/rotation.db
docker compose up --build -d
```

The script keeps the original ids, skips sessions whose game was deleted, and refuses to run if Postgres already has games. Set `DATABASE_URL` in `.env` before running it.
