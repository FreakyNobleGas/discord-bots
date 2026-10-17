import { toSqlTimestamp } from '#lib/dates.ts';
import type { Game, Session } from '#lib/types.ts';
import { db } from '../db/pool';
import type { DataSource } from './source';

// Rows written by the game night bot (bot/database.py). Timestamps leave here in the
// same UTC "YYYY-MM-DD HH:MM:SS" shape the analytics were built on.

type GameRow = Omit<Game, 'added_at'> & { added_at: Date };
type SessionRow = Omit<Session, 'played_on'> & { played_on: Date };

export const postgresSource: DataSource = {
	async getGames(guildId) {
		const { rows } = await db().query<GameRow>(
			`SELECT id, guild_id::text, name, rawg_id, rawg_slug, cover_url, genre_tags, added_by, added_at
			 FROM games WHERE guild_id = $1 ORDER BY name`,
			[guildId]
		);
		return rows.map((r) => ({ ...r, added_at: toSqlTimestamp(r.added_at) }));
	},
	async getSessions(guildId) {
		const { rows } = await db().query<SessionRow>(
			`SELECT s.id, s.game_id, s.played_on, s.logged_by, s.notes
			 FROM sessions s JOIN games g ON g.id = s.game_id
			 WHERE g.guild_id = $1 ORDER BY s.played_on`,
			[guildId]
		);
		return rows.map((r) => ({ ...r, played_on: toSqlTimestamp(r.played_on) }));
	}
};
