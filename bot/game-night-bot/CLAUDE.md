# CLAUDE.md

Discord bot that tracks a friend group's game night rotation ("Cartman's Basement Crew"). Slash commands add games (enriched from the RAWG API), log sessions, and show the rotation. It runs in Docker on a home host.

## Related project: the website (`../../website/game-night-website`)

A SvelteKit site on Vercel charts this bot's data, gives Grok Bot an API, and has a password-protected `/admin` page. Both live in the `discord-bots` monorepo (bots under `bot/`, websites under `website/`) and **share one Neon Postgres database**. Nothing syncs or pushes between them. Each one reads and writes the same rows.

- **Who writes what**
  - This bot writes `games` and `sessions`.
  - The website writes `patch_notes` and `suggestions` (from Grok).
  - The website's `/admin` can edit all four tables, so expect rows the bot didn't create: backdated sessions, manually added games.
- **One schema:** `schema.sql` in this folder. `init_db()` runs it on startup, and the website's `npm run db:init` runs it too.
  - A schema change means updating `schema.sql`, `bot/database.py`, and the website's `src/lib/types.ts` plus its `postgres.ts` files in `src/lib/server/data` and `src/lib/server/feed`.
  - Keep the schema idempotent (`IF NOT EXISTS`).
  - Deleting a game cascades to its sessions and patch notes.
- **Data contracts both sides depend on**
  - `guild_id` is `BIGINT`. The website treats it as a string.
  - Timestamps are UTC `timestamptz`.
  - `genre_tags` is a jsonb list of RAWG genre names; manual games have `[]`. asyncpg returns it as a Python list because of the codec in `_init_connection`.
  - The genre/emoji rules in `bot/utils/embeds.py` (`GENRE_EMOJIS`, `_GENERIC_TAGS`, `GAME_OVERRIDES`) are **duplicated** in the website's `src/lib/genres.ts`. Change both together.
- **Site links:** `bot/utils/links.py` adds a "See the stats" link button (`SITE_URL` + `/games` or `/`) to the `/add-game` and `/log-session` replies. No button appears when `SITE_URL` is unset. discord.py 2.4 rejects `view=None` on `followup.send`, so use `with_site_link(...)`.
- **Neon free plan:** 100 CU-hours/month, scales to zero after 5 idle minutes. Use the **direct** connection string, not `-pooler`. Keep the pool at `min_size=0` with a short `max_inactive_connection_lifetime`, so idle connections don't keep the database awake. Don't add background polling.

## Commands

- `uv sync`, then `uv run python -m bot.main`: run locally. Needs a `.env`; see `.env.example`.
- `docker compose up --build -d`: production on the home host. The Dockerfile installs with `uv sync --frozen` and copies only `bot/`, `scripts/`, `schema.sql` and the locale files.
- Change dependencies with `uv add` / `uv remove`, which keeps `uv.lock` in sync. There is no `requirements.txt`.
- `uv run python -m compileall -q bot scripts`: quick syntax check. There's no test suite yet.
- `scripts/migrate_sqlite_to_postgres.py`: one-time copy of the old SQLite `data/rotation.db`. It refuses to run on a non-empty database.

## Architecture

- `bot/main.py`: `RotationBot`. Opens the DB pool, loads the cogs, syncs slash commands to `DISCORD_GUILD_IDS`, and closes the pool on shutdown.
- `bot/database.py`: every query, through one asyncpg pool. Function signatures are what the cogs depend on.
- `bot/commands/`: the `games.py` (rotation, add, remove), `sessions.py` (log) and `help.py` cogs.
- `bot/enrichment.py`: RAWG search and lookup.
- `bot/utils/embeds.py`: embed builders and genre emoji rules.
- `bot/locale.py`: `t(key)`. `locale.example.json` provides the defaults, and a gitignored `locale.json` overrides them. When you add a user-facing string, add its key to `locale.example.json`.

## Guardrails

- `.env` holds real secrets (Discord token, RAWG key, database URL). Never commit, print, or copy it.
- `data/rotation.db` is the pre-Postgres backup. Don't delete it.
