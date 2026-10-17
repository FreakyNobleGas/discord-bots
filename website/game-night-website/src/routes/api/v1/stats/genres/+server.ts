import { apiParams, handler } from '#lib/server/api.ts';
import { loadAnalysis } from '#lib/server/data/index.ts';
import { genreStats } from '#lib/server/serialize.ts';

export const GET = handler('read', async ({ url }) => {
	const { guildId, range } = apiParams(url);
	const { analysis } = await loadAnalysis(range, guildId);
	return Response.json({ guild_id: guildId, ...genreStats(analysis) });
});
