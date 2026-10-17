import { loadAnalysis } from '#lib/server/data/index.ts';
import { newestFirst } from '#lib/server/feed/service.ts';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ url }) => {
	const { analysis, feed } = await loadAnalysis('all');
	const gameId = Number(url.searchParams.get('game')) || null;
	const notes = [...feed.patch_notes]
		.sort(newestFirst)
		.filter((n) => gameId === null || n.game_id === gameId);
	const patched = new Set(feed.patch_notes.map((n) => n.game_id));
	return {
		notes,
		gameId,
		games: analysis.games
			.filter((g) => patched.has(g.game.id))
			.map((g) => ({
				id: g.game.id,
				name: g.game.name,
				emoji: g.emoji,
				genre: g.primary_genre,
				days: g.days_since_played
			}))
			.sort((x, y) => x.name.localeCompare(y.name)),
		colors: Object.fromEntries(analysis.genre_share.map((s) => [s.genre, s.color]))
	};
};
