# Cartman's Basement Crew — Game Night Dashboard

A companion website for the [game night Discord bot](../../bot/game-night-bot). It charts what the crew plays (genre breakdown, leaderboard, games collecting dust) and exposes a JSON API so **Grok Bot** can read the crew's tastes and post patch notes and game suggestions back to the site. A password-protected admin page fixes records by hand.

The bot and the site share one Postgres database (Neon, connected through Vercel). The bot writes games and sessions, and the site reads them live. There's no sync between them. See [CLAUDE.md](CLAUDE.md) for how the two fit together.

## Running it

```sh
npm install
cp .env.example .env
npm run dev            # http://localhost:5173
```

With `DATABASE_URL` unset, the site runs on seeded mock data and keeps Grok's posts in `data/feed.json`. The admin page stays off in this mode.

To run against Postgres, use the Neon `dev` branch or a local database:

```sh
# in .env: DATABASE_URL=postgresql://localhost/game_night_dev
npm run db:init        # apply ../../bot/game-night-bot/schema.sql
npm run db:seed        # load the mock data (only into an empty database)
```

| Command           | What it does                                       |
| ----------------- | -------------------------------------------------- |
| `npm run dev`     | Dev server                                         |
| `npm run check`   | svelte-check / TypeScript                          |
| `npm run build`   | Production build (adapter-vercel, Node 24 runtime) |
| `npm run db:init` | Create missing tables from the shared schema       |
| `npm run db:seed` | Fill an empty database with mock data              |
| `npm run format`  | Prettier                                           |

Requires Node 22+. SvelteKit 3, Svelte 5, Tailwind v4.

## Pages

| Route          | What's on it                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------- |
| `/`            | KPIs, genre mix, most played, "Forgotten in the basement", latest patch notes                           |
| `/genres`      | Share of sessions by genre (click a genre for its games), genre mix over time (count / 100%), tag reach |
| `/games`       | Sortable leaderboard with monthly sparklines and "new patch" badges, plus the dust pile                 |
| `/patch-notes` | Grok's patch notes, filterable by game                                                                  |
| `/suggestions` | Grok's game picks, with a genre-fit score against the crew's last 12 months                             |
| `/admin`       | Password-protected CRUD for games, sessions, patch notes and suggestions                                |

The analytics pages take `?range=all|12m|90d`.

### How the numbers work

- **Game night**: all sessions that start on the same evening in `GAME_NIGHT_TZ`. Sessions before 6am count toward the previous night.
- **Main genre**: the first specific RAWG genre, skipping Action/Adventure/Indie. This is the same rule `embeds.py` uses to pick an emoji. Genre share uses main genre, so it sums to 100%.
- **Tag reach**: the share of sessions whose game carries a tag. Games have several tags, so these add up past 100%.
- **Genre colors**: assigned by all-time rank, so switching the time range never repaints a genre. The palette is validated for color-vision deficiency in both themes.
- **Genre fit**: the average tag reach of a suggestion's specific genres, scaled so that matching the crew's #1 genre scores 100%.

## API for Grok Bot

Base path: `/api/v1`. The OpenAPI 3.1 spec is at **`/api/v1/openapi.json`** (no auth), so you can generate Grok tool definitions from it.

**Auth**

- Send `Authorization: Bearer $API_TOKEN`.
- POSTs always need the token; if `API_TOKEN` isn't set, POSTs return `503`.
- GETs need the token only once `API_TOKEN` is set.
- POSTs must also send `Content-Type: application/json`. In production, a POST with no content type is rejected with `403` by SvelteKit's CSRF check before it reaches the API.

All endpoints take an optional `?guild=<discord guild id>`, which defaults to the configured guild. Errors look like `{ "error": { "code", "message", "details" } }`.

### Read

| Endpoint                         | Use it for                                                                                                                                                           |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /rotation`                  | Every game, with `rawg_slug`, genres, and play recency. Look up updates by slug.                                                                                     |
| `GET /stats/genres?range=`       | Genre share, tag reach, monthly mix                                                                                                                                  |
| `GET /stats/games?range=&limit=` | Leaderboard and collecting-dust lists                                                                                                                                |
| `GET /profile`                   | Taste summary for "what should we play next": top genres, favorites, games that fell off, recent adds, `exclude`, `already_suggested`, and a one-paragraph `summary` |
| `GET /patch-notes?game=&limit=`  | What's already been posted (`game` = id, slug, or name)                                                                                                              |
| `GET /suggestions`               | Current picks with `genre_fit`                                                                                                                                       |

### Write

```sh
# Patch notes for a rotation game (matched by rawg_slug → game_id → name)
curl -X POST localhost:5173/api/v1/patch-notes \
  -H "Authorization: Bearer dev-grok-token" -H "Content-Type: application/json" \
  -d '{
    "game": { "rawg_slug": "helldivers-2" },
    "title": "Escalation of Freedom",
    "version": "1.5.0",
    "summary": "New enemy faction and difficulty level.",
    "highlights": ["Super Helldive difficulty", "New missions"],
    "url": "https://example.com/patch-notes",
    "published_at": "2026-10-16"
  }'

# Suggest a new game
curl -X POST localhost:5173/api/v1/suggestions \
  -H "Authorization: Bearer dev-grok-token" -H "Content-Type: application/json" \
  -d '{
    "name": "Barotrauma",
    "rawg_slug": "barotrauma",
    "genres": ["Simulation", "Indie"],
    "reason": "Co-op submarine chaos for Lethal Company fans.",
    "similar_to": ["Lethal Company"],
    "platforms": ["PC"]
  }'
```

| Status | Meaning                                                                                                                         |
| ------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `201`  | Created                                                                                                                         |
| `200`  | Duplicate. The existing entry is returned. Patch notes dedupe on game + version (or title); suggestions dedupe on slug or name. |
| `400`  | Validation failed: field length caps, `http(s)` URLs only. `details` lists each issue.                                          |
| `401`  | Missing or wrong token                                                                                                          |
| `409`  | That suggestion is already in the rotation                                                                                      |
| `415`  | Not JSON                                                                                                                        |
| `422`  | Patch note for a game that isn't in the rotation. `details.rotation` lists the valid games.                                     |

Everything Grok sends is rendered as plain text, never as HTML.

## Admin

`/admin` has a single shared password, `ADMIN_PASSWORD`.

- Signing in sets a signed, httpOnly cookie (scoped to `/admin`, valid for 7 days).
- Changing `ADMIN_PASSWORD` or `ADMIN_SESSION_SECRET` signs everyone out.
- A wrong password waits a second before answering. Use a long random password, because nothing else limits guessing.
- Admin turns itself off unless `DATABASE_URL`, `ADMIN_PASSWORD` and `ADMIN_SESSION_SECRET` are all set.

What it can do:

- **Games**: add (for games RAWG doesn't have), rename, retag, delete. Deleting a game also deletes its sessions and patch notes.
- **Sessions**: filter by game, add a backdated session, edit, delete. Times are entered in `GAME_NIGHT_TZ`.
- **Patch notes and Grok's picks**: edit and delete. New ones come in through the API.

## Code map

```
src/env.ts                       env vars (DATABASE_URL, API_TOKEN, ADMIN_*, GAME_NIGHT_TZ…)
src/lib/types.ts                 row types mirroring bot/game-night-bot/schema.sql
src/lib/genres.ts                port of the bot's embeds.py: emojis, generic tags, main genre
src/lib/analytics.ts             analyze(): every stat the pages and API show
src/lib/copy.ts                  all themed UI strings (the site's locale.json)
src/lib/server/db/pool.ts        pg Pool for Fluid compute
src/lib/server/data/             DataSource: postgres.ts (real) or mock.ts (no DATABASE_URL)
src/lib/server/feed/             FeedStore: postgres.ts (real) or file.ts; service.ts = Grok write rules
src/lib/server/db/admin.ts       admin queries
src/lib/server/admin/            admin auth, form parsing, action wrapper
src/hooks.server.ts              guards /admin
src/routes/api/v1/               API endpoints + openapi.json
src/routes/admin/                admin pages
scripts/db.ts                    db:init / db:seed
```

## Deploying (Vercel)

Pushes to `master` deploy automatically. The Vercel project's **Root Directory** is `website/game-night-website`. Commits that only touch other folders skip the build, via `ignoreCommand` in `vercel.json`.

One-time setup:

1. Import the `discord-bots` repo in Vercel and set Root Directory to `website/game-night-website`.
2. Under Storage, add **Neon** from the Marketplace. It sets `DATABASE_URL` (pooled) for the site.
   - Give the bot the **direct** connection string, not the pooled one.
   - Point Preview and Development at a Neon `dev` branch so previews never touch real data.
3. Set the environment variables:
   - `API_TOKEN`: give the same value to Grok
   - `ADMIN_PASSWORD` and `ADMIN_SESSION_SECRET`: mark both sensitive; generate each with `openssl rand -base64 32`
   - `DISCORD_GUILD_ID`
   - `GAME_NIGHT_TZ`
4. Run `npm run db:init` against production. The bot also creates the tables on startup.
5. Move the bot's SQLite data over with the migration script (see the bot README), then set the bot's `SITE_URL`.
6. Point Grok at `https://<site>/api/v1/openapi.json`.

Discord guild ids are 64-bit, so they're `bigint` in Postgres and strings in JSON.
