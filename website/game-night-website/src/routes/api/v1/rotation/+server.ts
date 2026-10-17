import { apiParams, handler } from '#lib/server/api.ts';
import { loadAnalysis } from '#lib/server/data/index.ts';
import { gameSummary } from '#lib/server/serialize.ts';

export const GET = handler('read', async ({ url }) => {
	const { guildId } = apiParams(url);
	const { analysis } = await loadAnalysis('all', guildId);
	const games = [...analysis.games].sort((a, b) => a.game.name.localeCompare(b.game.name));
	return Response.json({ guild_id: guildId, count: games.length, games: games.map(gameSummary) });
});
