import { genreFit } from '#lib/analytics.ts';
import { apiParams, handler, readJson, ApiError } from '#lib/server/api.ts';
import { getDataSource, loadAnalysis } from '#lib/server/data/index.ts';
import { suggestionInput } from '#lib/server/feed/schema.ts';
import { addSuggestion, newestFirst } from '#lib/server/feed/service.ts';
import { parseLimit, validationError } from '#lib/server/serialize.ts';

export const GET = handler('read', async ({ url }) => {
	const { guildId } = apiParams(url);
	const { feed, analysis } = await loadAnalysis('12m', guildId);
	const suggestions = [...feed.suggestions]
		.sort(newestFirst)
		.slice(0, parseLimit(url, 50))
		.map((s) => ({
			...s,
			genre_fit: Math.round(genreFit(s.genres, analysis.tag_reach) * 100) / 100
		}));
	return Response.json({ guild_id: guildId, suggestions });
});

export const POST = handler('write', async ({ url, request }) => {
	const { guildId } = apiParams(url);
	const parsed = suggestionInput.safeParse(await readJson(request));
	if (!parsed.success) throw validationError(parsed.error);
	const games = await getDataSource().getGames(guildId);
	if (!games.length) throw new ApiError(404, 'unknown_guild', 'No rotation found for that guild.');
	const { created, entry } = await addSuggestion(guildId, games, parsed.data);
	return Response.json({ created, suggestion: entry }, { status: created ? 201 : 200 });
});
