// Database chores for the Postgres shared with the game night bot.
//   npm run db:init   apply bot/game-night-bot/schema.sql (idempotent; the bot also runs it)
//   npm run db:seed   fill an EMPTY database (e.g. the Neon dev branch) with the mock data
// Reads DATABASE_URL (and DISCORD_GUILD_ID) from the environment or .env.

import { readFileSync } from 'node:fs';
import pg from 'pg';
import { MOCK_GUILD_ID, mockSource } from '../src/lib/server/data/mock.ts';
import { seedFeed } from '../src/lib/server/feed/seed.ts';
import { parseSqlTimestamp } from '../src/lib/dates.ts';

const SCHEMA = new URL('../../../bot/game-night-bot/schema.sql', import.meta.url);

try {
	process.loadEnvFile();
} catch {
	// no .env; rely on the real environment
}

const url = process.env.DATABASE_URL;
if (!url) {
	console.error('DATABASE_URL is not set.');
	process.exit(1);
}
const client = new pg.Client({ connectionString: url });

async function init() {
	await client.query(readFileSync(SCHEMA, 'utf8'));
	console.log('Schema applied.');
}

async function seed() {
	await init();
	const { rows } = await client.query<{ n: number }>('SELECT COUNT(*)::int AS n FROM games');
	if (rows[0].n > 0) {
		console.error(`Refusing to seed: the database already has ${rows[0].n} games.`);
		process.exit(1);
	}

	const guild = process.env.DISCORD_GUILD_ID || MOCK_GUILD_ID;
	const games = await mockSource.getGames(MOCK_GUILD_ID);
	const sessions = await mockSource.getSessions(MOCK_GUILD_ID);
	const feed = (await seedFeed()).guilds[MOCK_GUILD_ID];

	await client.query('BEGIN');
	for (const g of games) {
		await client.query(
			`INSERT INTO games (id, guild_id, name, rawg_id, rawg_slug, cover_url, genre_tags, added_by, added_at)
			 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
			[
				g.id,
				guild,
				g.name,
				g.rawg_id,
				g.rawg_slug,
				g.cover_url,
				JSON.stringify(g.genre_tags),
				g.added_by,
				parseSqlTimestamp(g.added_at)
			]
		);
	}
	for (const s of sessions) {
		await client.query(
			`INSERT INTO sessions (id, game_id, played_on, logged_by, notes) VALUES ($1, $2, $3, $4, $5)`,
			[s.id, s.game_id, parseSqlTimestamp(s.played_on), s.logged_by, s.notes]
		);
	}
	for (const n of feed.patch_notes) {
		await client.query(
			`INSERT INTO patch_notes (id, guild_id, game_id, title, version, summary, highlights, url,
			                          published_at, posted_at, source)
			 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
			[
				n.id,
				guild,
				n.game_id,
				n.title,
				n.version,
				n.summary,
				JSON.stringify(n.highlights),
				n.url,
				parseSqlTimestamp(n.published_at),
				parseSqlTimestamp(n.posted_at),
				n.source
			]
		);
	}
	for (const s of feed.suggestions) {
		await client.query(
			`INSERT INTO suggestions (id, guild_id, name, rawg_slug, rawg_id, genres, reason, similar_to,
			                          platforms, release_date, url, suggested_at, source)
			 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
			[
				s.id,
				guild,
				s.name,
				s.rawg_slug,
				s.rawg_id,
				JSON.stringify(s.genres),
				s.reason,
				JSON.stringify(s.similar_to),
				JSON.stringify(s.platforms),
				s.release_date,
				s.url,
				parseSqlTimestamp(s.suggested_at),
				s.source
			]
		);
	}
	// Explicit ids were inserted, so move the identity sequences past them.
	for (const table of ['games', 'sessions']) {
		await client.query(
			`SELECT setval(pg_get_serial_sequence('${table}', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM ${table}`
		);
	}
	await client.query('COMMIT');
	console.log(
		`Seeded guild ${guild}: ${games.length} games, ${sessions.length} sessions, ` +
			`${feed.patch_notes.length} patch notes, ${feed.suggestions.length} suggestions.`
	);
}

const commands: Record<string, () => Promise<void>> = { init, seed };
const command = commands[process.argv[2]];
if (!command) {
	console.error('Usage: tsx scripts/db.ts <init|seed>');
	process.exit(1);
}
await client.connect();
try {
	await command();
} finally {
	await client.end();
}
