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

Setup
-----
**1. Prerequisites**

- Docker and Docker Compose
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- A RAWG API key ([rawg.io/apidocs](https://rawg.io/apidocs))

**2. Configure environment**

Copy `.env.example` to `.env` and fill in your values:

```
cp .env.example .env
```

```
DISCORD_TOKEN=        # Your bot token
DISCORD_GUILD_IDS=    # Comma-separated server IDs, e.g. 123456789,987654321
RAWG_API_KEY=         # Your RAWG API key
DB_PATH=              # Optional, defaults to /app/data/rotation.db
```

**3. Customize personality (optional)**

Copy `locale.example.json` to `locale.json` and edit the strings to give your bot its own personality. `locale.json` is gitignored so your customizations stay private.

```
cp locale.example.json locale.json
```

**4. Run**

```
docker compose up --build -d
```

The SQLite database is persisted in the `data/` directory via a Docker volume.
