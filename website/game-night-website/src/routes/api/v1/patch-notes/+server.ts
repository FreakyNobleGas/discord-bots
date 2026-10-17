import { apiParams, handler, readJson, ApiError } from '#lib/server/api.ts';
import { getDataSource } from '#lib/server/data/index.ts';
import { patchNoteInput } from '#lib/server/feed/schema.ts';
import { addPatchNote, newestFirst } from '#lib/server/feed/service.ts';
import { getFeedStore } from '#lib/server/feed/store.ts';
import { parseLimit, validationError } from '#lib/server/serialize.ts';

export const GET = handler('read', async ({ url }) => {
	const { guildId } = apiParams(url);
	const game = url.searchParams.get('game')?.toLowerCase();
	const feed = await getFeedStore().read(guildId);
	let notes = [...feed.patch_notes].sort(newestFirst);
	if (game) {
		const games = await getDataSource().getGames(guildId);
		const ids = new Set(
			games
				.filter(
					(g) => String(g.id) === game || g.rawg_slug === game || g.name.toLowerCase() === game
				)
				.map((g) => g.id)
		);
		notes = notes.filter((n) => ids.has(n.game_id));
	}
	return Response.json({ guild_id: guildId, patch_notes: notes.slice(0, parseLimit(url, 50)) });
});

export const POST = handler('write', async ({ url, request }) => {
	const { guildId } = apiParams(url);
	const parsed = patchNoteInput.safeParse(await readJson(request));
	if (!parsed.success) throw validationError(parsed.error);
	const games = await getDataSource().getGames(guildId);
	if (!games.length) throw new ApiError(404, 'unknown_guild', 'No rotation found for that guild.');
	const { created, entry } = await addPatchNote(guildId, games, parsed.data);
	return Response.json({ created, patch_note: entry }, { status: created ? 201 : 200 });
});
