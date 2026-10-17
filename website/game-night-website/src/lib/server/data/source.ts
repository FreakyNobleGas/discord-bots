import type { Game, Session } from '#lib/types.ts';

/**
 * The seam between the site and the bot's data: `postgres.ts` reads the Postgres database
 * the bot writes to; `mock.ts` is seeded fake data for local dev without a database.
 */
export interface DataSource {
	getGames(guildId: string): Promise<Game[]>;
	getSessions(guildId: string): Promise<Session[]>;
}
