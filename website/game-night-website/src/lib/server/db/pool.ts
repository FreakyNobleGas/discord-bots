// One pg Pool per function instance, shared across concurrent requests (Fluid compute).
// The database is shared with the game night bot; the schema is bot/game-night-bot/schema.sql.

import pg from 'pg';
import { attachDatabasePool } from '@vercel/functions';
import { DATABASE_URL } from '$app/env/private';

// Keep DATE columns as "YYYY-MM-DD" strings instead of local-midnight Date objects.
const types = {
	getTypeParser: ((oid: number, format?: 'text' | 'binary') =>
		oid === pg.types.builtins.DATE
			? (v: string) => v
			: pg.types.getTypeParser(oid, format)) as typeof pg.types.getTypeParser
};

let pool: pg.Pool | undefined;

export const dbEnabled = () => Boolean(DATABASE_URL);

export function db(): pg.Pool {
	if (!DATABASE_URL) throw new Error('DATABASE_URL is not set');
	if (!pool) {
		pool = new pg.Pool({ connectionString: DATABASE_URL, idleTimeoutMillis: 5_000, max: 5, types });
		attachDatabasePool(pool);
	}
	return pool;
}
