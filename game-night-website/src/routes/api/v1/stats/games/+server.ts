import { apiParams, handler } from '#lib/server/api.ts';
import { loadAnalysis } from '#lib/server/data/index.ts';
import { parseLimit, rankedGame } from '#lib/server/serialize.ts';

export const GET = handler('read', async ({ url }) => {
	const { guildId, range } = apiParams(url);
	const limit = parseLimit(url, 25);
	const { analysis } = await loadAnalysis(range, guildId);
	return Response.json({
		guild_id: guildId,
		range,
		total_sessions: analysis.kpis.sessions,
		leaderboard: analysis.games.slice(0, limit).map(rankedGame),
		collecting_dust: analysis.collecting_dust.slice(0, limit).map(rankedGame)
	});
});
