// Admin page reads and writes, scoped to one guild. Times are shown and entered as wall
// time in GAME_NIGHT_TZ; Postgres does the zone math (DST-safe) via AT TIME ZONE.

import type { GameForm, PatchNoteForm, SessionForm, SuggestionForm } from '../admin/forms';
import { db } from './pool';

const LOCAL = `'YYYY-MM-DD"T"HH24:MI'`;
export const SESSIONS_PER_PAGE = 50;

export async function counts(guild: string) {
	const { rows } = await db().query<
		Record<'games' | 'sessions' | 'patch_notes' | 'suggestions', number>
	>(
		`SELECT (SELECT COUNT(*) FROM games WHERE guild_id = $1)::int AS games,
		        (SELECT COUNT(*) FROM sessions s JOIN games g ON g.id = s.game_id WHERE g.guild_id = $1)::int AS sessions,
		        (SELECT COUNT(*) FROM patch_notes WHERE guild_id = $1)::int AS patch_notes,
		        (SELECT COUNT(*) FROM suggestions WHERE guild_id = $1)::int AS suggestions`,
		[guild]
	);
	return rows[0];
}

// --- games ---------------------------------------------------------------------------

export async function listGames(guild: string) {
	const { rows } = await db().query<{
		id: number;
		name: string;
		rawg_id: number | null;
		rawg_slug: string | null;
		cover_url: string;
		genre_tags: string[];
		added_by: string;
		added_at: Date;
		sessions: number;
	}>(
		`SELECT g.id, g.name, g.rawg_id, g.rawg_slug, g.cover_url, g.genre_tags, g.added_by, g.added_at,
		        COUNT(s.id)::int AS sessions
		 FROM games g LEFT JOIN sessions s ON s.game_id = g.id
		 WHERE g.guild_id = $1 GROUP BY g.id ORDER BY lower(g.name)`,
		[guild]
	);
	return rows;
}

export async function createGame(guild: string, f: GameForm) {
	await db().query(
		`INSERT INTO games (guild_id, name, rawg_id, rawg_slug, cover_url, genre_tags, added_by)
		 VALUES ($1, $2, $3, $4, $5, $6, $7)`,
		[guild, f.name, f.rawg_id, f.rawg_slug, f.cover_url, JSON.stringify(f.genre_tags), f.added_by]
	);
}

export async function updateGame(guild: string, id: number, f: GameForm) {
	const { rowCount } = await db().query(
		`UPDATE games SET name = $3, rawg_id = $4, rawg_slug = $5, cover_url = $6, genre_tags = $7, added_by = $8
		 WHERE id = $1 AND guild_id = $2`,
		[
			id,
			guild,
			f.name,
			f.rawg_id,
			f.rawg_slug,
			f.cover_url,
			JSON.stringify(f.genre_tags),
			f.added_by
		]
	);
	return rowCount === 1;
}

/** Sessions and patch notes for the game go with it (ON DELETE CASCADE). */
export async function deleteGame(guild: string, id: number) {
	const { rowCount } = await db().query(`DELETE FROM games WHERE id = $1 AND guild_id = $2`, [
		id,
		guild
	]);
	return rowCount === 1;
}

// --- sessions ------------------------------------------------------------------------

export async function listSessions(
	guild: string,
	tz: string,
	{ gameId, page }: { gameId: number | null; page: number }
) {
	const { rows } = await db().query<{
		id: number;
		game_id: number;
		game_name: string;
		played_on: string;
		logged_by: string | null;
		notes: string | null;
		total: number;
	}>(
		`SELECT s.id, s.game_id, g.name AS game_name,
		        to_char(s.played_on AT TIME ZONE $2, ${LOCAL}) AS played_on,
		        s.logged_by, s.notes, COUNT(*) OVER ()::int AS total
		 FROM sessions s JOIN games g ON g.id = s.game_id
		 WHERE g.guild_id = $1 AND ($3::int IS NULL OR s.game_id = $3)
		 ORDER BY s.played_on DESC, s.id DESC
		 LIMIT ${SESSIONS_PER_PAGE} OFFSET $4`,
		[guild, tz, gameId, (page - 1) * SESSIONS_PER_PAGE]
	);
	return { rows, total: rows[0]?.total ?? 0 };
}

export async function createSession(guild: string, tz: string, f: SessionForm) {
	const { rowCount } = await db().query(
		`INSERT INTO sessions (game_id, played_on, logged_by, notes)
		 SELECT id, $3::timestamp AT TIME ZONE $4, $5, $6 FROM games WHERE id = $1 AND guild_id = $2`,
		[f.game_id, guild, f.played_on, tz, f.logged_by, f.notes]
	);
	return rowCount === 1;
}

export async function updateSession(guild: string, tz: string, id: number, f: SessionForm) {
	const { rowCount } = await db().query(
		`UPDATE sessions SET game_id = $3, played_on = $4::timestamp AT TIME ZONE $5, logged_by = $6, notes = $7
		 WHERE id = $1
		   AND game_id IN (SELECT id FROM games WHERE guild_id = $2)
		   AND $3 IN (SELECT id FROM games WHERE guild_id = $2)`,
		[id, guild, f.game_id, f.played_on, tz, f.logged_by, f.notes]
	);
	return rowCount === 1;
}

export async function deleteSession(guild: string, id: number) {
	const { rowCount } = await db().query(
		`DELETE FROM sessions WHERE id = $1 AND game_id IN (SELECT id FROM games WHERE guild_id = $2)`,
		[id, guild]
	);
	return rowCount === 1;
}

// --- patch notes ---------------------------------------------------------------------

export async function listPatchNotes(guild: string, tz: string) {
	const { rows } = await db().query<{
		id: string;
		game_name: string;
		title: string;
		version: string | null;
		summary: string;
		highlights: string[];
		url: string | null;
		published_at: string;
		source: string;
	}>(
		`SELECT p.id, g.name AS game_name, p.title, p.version, p.summary, p.highlights, p.url,
		        to_char(p.published_at AT TIME ZONE $2, ${LOCAL}) AS published_at, p.source
		 FROM patch_notes p JOIN games g ON g.id = p.game_id
		 WHERE p.guild_id = $1 ORDER BY p.published_at DESC`,
		[guild, tz]
	);
	return rows;
}

export async function updatePatchNote(guild: string, tz: string, id: string, f: PatchNoteForm) {
	const { rowCount } = await db().query(
		`UPDATE patch_notes SET title = $3, version = $4, summary = $5, highlights = $6, url = $7,
		        published_at = $8::timestamp AT TIME ZONE $9
		 WHERE id = $1 AND guild_id = $2`,
		[
			id,
			guild,
			f.title,
			f.version,
			f.summary,
			JSON.stringify(f.highlights),
			f.url,
			f.published_at,
			tz
		]
	);
	return rowCount === 1;
}

export async function deletePatchNote(guild: string, id: string) {
	const { rowCount } = await db().query(`DELETE FROM patch_notes WHERE id = $1 AND guild_id = $2`, [
		id,
		guild
	]);
	return rowCount === 1;
}

// --- suggestions ---------------------------------------------------------------------

export async function listSuggestions(guild: string) {
	const { rows } = await db().query<{
		id: string;
		name: string;
		rawg_slug: string | null;
		genres: string[];
		reason: string;
		similar_to: string[];
		platforms: string[];
		release_date: string | null;
		url: string | null;
		suggested_at: Date;
		source: string;
	}>(
		`SELECT id, name, rawg_slug, genres, reason, similar_to, platforms, release_date, url,
		        suggested_at, source
		 FROM suggestions WHERE guild_id = $1 ORDER BY suggested_at DESC`,
		[guild]
	);
	return rows;
}

export async function updateSuggestion(guild: string, id: string, f: SuggestionForm) {
	const { rowCount } = await db().query(
		`UPDATE suggestions SET name = $3, rawg_slug = $4, genres = $5, reason = $6, similar_to = $7,
		        platforms = $8, release_date = $9, url = $10
		 WHERE id = $1 AND guild_id = $2`,
		[
			id,
			guild,
			f.name,
			f.rawg_slug,
			JSON.stringify(f.genres),
			f.reason,
			JSON.stringify(f.similar_to),
			JSON.stringify(f.platforms),
			f.release_date,
			f.url
		]
	);
	return rowCount === 1;
}

export async function deleteSuggestion(guild: string, id: string) {
	const { rowCount } = await db().query(`DELETE FROM suggestions WHERE id = $1 AND guild_id = $2`, [
		id,
		guild
	]);
	return rowCount === 1;
}
