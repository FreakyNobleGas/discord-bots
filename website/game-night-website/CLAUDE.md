# CLAUDE.md

Website for the game night Discord bot, for "Cartman's Basement Crew" (a South Park-themed friend group). It charts which genres and games the crew plays, gives Grok Bot an API to read the crew's tastes and post patch notes and game suggestions, and has a password-protected `/admin` page for fixing data by hand.

## Related project: the bot (`../../bot/game-night-bot`)

This site and the Python bot live in the same `discord-bots` monorepo (bots under `bot/`, websites under `website/`) and **share one Neon Postgres database**. Nothing syncs or pushes between them. Each one reads and writes the same rows.

- **Who writes what**
  - The bot writes `games` (`/add-game`, `/remove-game`) and `sessions` (`/log-session`).
  - The site writes `patch_notes` and `suggestions` (Grok, via `POST /api/v1/*`).
  - `/admin` can edit all four tables.
- **One schema:** `../../bot/game-night-bot/schema.sql`. The bot runs it on startup, and `npm run db:init` runs it here.
  - Changing a table means updating `schema.sql`, the bot's `bot/database.py`, and this site's `src/lib/types.ts` plus the `postgres.ts` files in `src/lib/server/data` and `src/lib/server/feed`.
  - Keep the schema idempotent (`IF NOT EXISTS`). There is no migration tool.
- **Data contracts both sides depend on**
  - `guild_id` is `BIGINT` in Postgres and a **string** in JS. Discord snowflakes exceed `Number.MAX_SAFE_INTEGER`.
  - Timestamps are UTC `timestamptz`. The site turns them into `"YYYY-MM-DD HH:MM:SS"` UTC strings (`toSqlTimestamp`) before analytics.
  - `genre_tags` is a jsonb list of RAWG genre names. Manual games have `[]`.
  - Genre/emoji rules are **duplicated**: `src/lib/genres.ts` is a port of the bot's `bot/utils/embeds.py` (`GENRE_EMOJIS`, `_GENERIC_TAGS`, `GAME_OVERRIDES`). Change both together.
- **Bot links:** the bot links here from its replies using `SITE_URL` + `/` and `/games` (`bot/utils/links.py`). Don't remove or rename those routes without updating the bot.
- **Neon free plan:** 100 CU-hours/month, scales to zero after 5 idle minutes. The bot uses the direct connection and holds no idle connections. This site uses the pooled URL with a short idle timeout (`src/lib/server/db/pool.ts`). Don't add anything that keeps a connection open or polls the database.
- **Vercel deploys:** the project's Root Directory is `website/game-night-website`. `vercel.json` `ignoreCommand` skips builds for bot-only commits.

## Stack

- **SvelteKit 3** + Svelte 5 runes, TypeScript 6, Vite 8, Tailwind v4.
- `@sveltejs/adapter-vercel` is pinned to `runtime: 'nodejs24.x'` in `vite.config.ts`, because the local Node 25 isn't a Vercel runtime.
- `pg` Pool with `attachDatabasePool` (Fluid compute).
- d3-scale/d3-shape for chart math only; the charts are hand-written SVG.
- zod v4 for validation.

## SvelteKit 3 differences (from SvelteKit 2)

- There's no `svelte.config.js`. Config goes in `sveltekit({...})` in `vite.config.ts`.
- Import lib code as `#lib/foo.ts`, with the extension. These are package.json `imports`, not `$lib`.
- Private env vars come from `$app/env/private`, and must be declared in `src/env.ts` with `defineEnvVars`.
- Use `Response.json(...)`, not `json()`.
- Use `data-sveltekit-reset="false"`, not `data-sveltekit-noscroll`.
- The `Handle` type comes from `@sveltejs/kit/hooks`.
- The CSRF origin check only runs in production builds. Test it with `npm run build && npm run preview`, not with `dev`.

## Commands

- `npm run dev`: dev server. With no `DATABASE_URL`, it uses mock data plus `data/feed.json`.
- `npm run check`: svelte-check/TypeScript. **Run it, plus `npm run build`, before finishing a change.**
- `npm run db:init` and `npm run db:seed`: these run against whatever `DATABASE_URL` points to. **Never run them against production unless asked.** `db:seed` refuses to touch a non-empty database.

## Architecture

- `src/lib/analytics.ts`: `analyze()` is pure and computes every stat the pages and API show. Pages and API share it, so the numbers always match.
- `src/lib/server/data/`: the `DataSource` seam. `postgres.ts` is used when `DATABASE_URL` is set; otherwise `mock.ts` (seeded, deterministic).
- `src/lib/server/feed/`: the `FeedStore` seam. `postgres.ts` or `file.ts`. `service.ts` holds Grok's write rules: game matching by slug, then id, then name; dedupe; 409 when a suggestion is already in the rotation; 422 for an unknown game.
- `src/routes/api/v1/`: the Grok API. `openapi.json/+server.ts` is a hand-written spec that Grok's tool definitions come from. **Update it whenever an endpoint's shape changes**, and keep `src/lib/server/serialize.ts` stable.
- **Admin**
  - `src/hooks.server.ts` guards `/admin/**`.
  - `src/lib/server/admin/auth.ts` uses an HMAC-signed cookie keyed to `ADMIN_SESSION_SECRET` and the password hash.
  - `actions.ts` (`adminAction` re-checks `locals.admin`).
  - `forms.ts` (zod).
  - `src/lib/server/db/admin.ts`: guild-scoped queries. Admin times are wall time in `GAME_NIGHT_TZ`, converted by Postgres `AT TIME ZONE`.
- A "game night" is all sessions from the same evening in `GAME_NIGHT_TZ`, with a 6am cutoff (`nightKey` in `src/lib/dates.ts`).

## Look and voice

- All UI strings live in `src/lib/copy.ts`, in a playful Cartman-flavored voice. Use original fan-style art only: no copied South Park art or logos.
- Theme tokens are in `src/routes/layout.css`. Light is a snowy mountain town; dark is "the basement".
- Chart colors follow the dataviz rules:
  - a fixed categorical slot order
  - genre color assigned by all-time rank, so a range filter never repaints a genre
  - at most 8 series; the rest fold into "Other"
  - every chart has a legend, tooltips and a table view
- Grok's text renders as plain text only. Never use `{@html}`. Links use `rel="noopener noreferrer nofollow"`.

## Guardrails

- `.env` holds secrets. Never commit, print, or copy it.
- Never edit `.svelte-kit/` or `.vercel/`.
- Svelte questions: use the `svelte` MCP server (docs and `svelte-autofixer`).
