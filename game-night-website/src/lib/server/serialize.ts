// Public JSON shapes for /api/v1. Kept separate from the internal Analysis type so the
// API contract (and Grok's tool definitions) don't shift when the UI needs change.

import type { Analysis, GameStats } from '#lib/types.ts';
import type { ZodError } from 'zod';
import { ApiError } from './api';

const round = (n: number) => Math.round(n * 1000) / 1000;

export function gameSummary(st: GameStats) {
	return {
		game_id: st.game.id,
		name: st.game.name,
		rawg_id: st.game.rawg_id,
		rawg_slug: st.game.rawg_slug,
		genres: st.game.genre_tags,
		primary_genre: st.primary_genre,
		added_by: st.game.added_by,
		added_at: st.game.added_at,
		total_sessions: st.total_sessions,
		last_played: st.last_played,
		days_since_played: st.days_since_played,
		has_recent_patch: st.has_recent_patch
	};
}

export function rankedGame(st: GameStats) {
	return {
		game_id: st.game.id,
		name: st.game.name,
		rawg_slug: st.game.rawg_slug,
		primary_genre: st.primary_genre,
		sessions: st.session_count,
		share: round(st.share),
		last_played: st.last_played,
		days_since_played: st.days_since_played
	};
}

export function genreStats(a: Analysis) {
	return {
		range: a.range,
		total_sessions: a.kpis.sessions,
		genre_share: a.genre_share.map(({ genre, sessions, share, games }) => ({
			genre,
			sessions,
			share: round(share),
			games
		})),
		tag_reach: a.tag_reach.map((t) => ({ ...t, reach: round(t.reach) })),
		monthly: a.months
	};
}

export function validationError(err: ZodError) {
	return new ApiError(
		400,
		'invalid_body',
		'Request body failed validation.',
		err.issues.map((i) => ({ path: i.path.join('.'), message: i.message }))
	);
}

export function parseLimit(url: URL, fallback: number, max = 100) {
	const n = Number(url.searchParams.get('limit'));
	return Number.isInteger(n) && n > 0 ? Math.min(n, max) : fallback;
}
