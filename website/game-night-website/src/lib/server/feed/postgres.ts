import { parseSqlTimestamp, toSqlTimestamp } from '#lib/dates.ts';
import type { PatchNote, Suggestion } from '#lib/types.ts';
import { db } from '../db/pool';
import type { FeedStore } from './store';

type Dated<T, K extends keyof T> = Omit<T, K> & { [P in K]: Date };

export const postgresFeedStore: FeedStore = {
	async read(guildId) {
		const [notes, suggestions] = await Promise.all([
			db().query<Dated<PatchNote, 'published_at' | 'posted_at'>>(
				`SELECT p.id, p.guild_id::text, p.game_id, g.name AS game_name, p.title, p.version,
				        p.summary, p.highlights, p.url, p.published_at, p.posted_at, p.source
				 FROM patch_notes p JOIN games g ON g.id = p.game_id
				 WHERE p.guild_id = $1 ORDER BY p.published_at DESC`,
				[guildId]
			),
			db().query<Dated<Suggestion, 'suggested_at'>>(
				`SELECT id, guild_id::text, name, rawg_slug, rawg_id, genres, reason, similar_to,
				        platforms, release_date, url, suggested_at, source
				 FROM suggestions WHERE guild_id = $1 ORDER BY suggested_at DESC`,
				[guildId]
			)
		]);
		return {
			patch_notes: notes.rows.map((n) => ({
				...n,
				published_at: toSqlTimestamp(n.published_at),
				posted_at: toSqlTimestamp(n.posted_at)
			})),
			suggestions: suggestions.rows.map((s) => ({
				...s,
				suggested_at: toSqlTimestamp(s.suggested_at)
			}))
		};
	},

	async addPatchNote(n) {
		await db().query(
			`INSERT INTO patch_notes (id, guild_id, game_id, title, version, summary, highlights, url,
			                          published_at, posted_at, source)
			 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
			[
				n.id,
				n.guild_id,
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
	},

	async addSuggestion(s) {
		await db().query(
			`INSERT INTO suggestions (id, guild_id, name, rawg_slug, rawg_id, genres, reason, similar_to,
			                          platforms, release_date, url, suggested_at, source)
			 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
			[
				s.id,
				s.guild_id,
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
};
