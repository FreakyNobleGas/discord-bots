import { genreFit } from '#lib/analytics.ts';
import { loadAnalysis } from '#lib/server/data/index.ts';
import { newestFirst } from '#lib/server/feed/service.ts';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	// Fit is scored against the last 12 months — current tastes, not ancient history
	const { analysis, feed } = await loadAnalysis('12m');
	const rotation = new Map(
		analysis.games.map((g) => [
			g.game.name.toLowerCase(),
			{ id: g.game.id, name: g.game.name, emoji: g.emoji }
		])
	);
	return {
		suggestions: [...feed.suggestions].sort(newestFirst).map((s) => ({
			...s,
			fit: genreFit(s.genres, analysis.tag_reach),
			similar: s.similar_to.map(
				(name) => rotation.get(name.toLowerCase()) ?? { id: null, name, emoji: '🎮' }
			)
		})),
		topTags: analysis.tag_reach.slice(0, 5).map((t) => t.tag)
	};
};
