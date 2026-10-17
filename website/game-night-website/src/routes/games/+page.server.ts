import { parseRange } from '#lib/analytics.ts';
import { loadAnalysis } from '#lib/server/data/index.ts';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ url }) => {
	const range = parseRange(url.searchParams.get('range'));
	const { analysis } = await loadAnalysis(range);
	return { analysis };
};
