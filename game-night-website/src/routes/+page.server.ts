import { parseRange } from '#lib/analytics.ts';
import { loadAnalysis } from '#lib/server/data/index.ts';
import { newestFirst } from '#lib/server/feed/service.ts';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ url }) => {
	const range = parseRange(url.searchParams.get('range'));
	const { analysis, feed } = await loadAnalysis(range);
	return {
		analysis,
		latestPatches: [...feed.patch_notes].sort(newestFirst).slice(0, 3)
	};
};
