import { toSqlTimestamp } from '#lib/dates.ts';
import type { Game, PatchNote, Suggestion } from '#lib/types.ts';
import { ApiError } from '../api';
import type { PatchNoteInput, SuggestionInput } from './schema';
import { getFeedStore } from './store';

const norm = (s: string) => s.trim().toLowerCase();

function matchGame(games: Game[], ref: PatchNoteInput['game']): Game | undefined {
	return (
		(ref.rawg_slug && games.find((g) => g.rawg_slug === norm(ref.rawg_slug!))) ||
		(ref.game_id && games.find((g) => g.id === ref.game_id)) ||
		(ref.name ? games.find((g) => norm(g.name) === norm(ref.name!)) : undefined)
	);
}

export async function addPatchNote(guildId: string, games: Game[], input: PatchNoteInput) {
	const game = matchGame(games, input.game);
	if (!game) {
		throw new ApiError(422, 'unknown_game', 'That game is not in the rotation.', {
			rotation: games.map((g) => ({ game_id: g.id, name: g.name, rawg_slug: g.rawg_slug }))
		});
	}

	const store = getFeedStore();
	const feed = await store.read(guildId);
	const dedupeKey = norm(input.version ?? input.title);
	const existing = feed.patch_notes.find(
		(p) => p.game_id === game.id && norm(p.version ?? p.title) === dedupeKey
	);
	if (existing) return { created: false, entry: existing };

	const now = toSqlTimestamp(new Date());
	const note: PatchNote = {
		id: crypto.randomUUID(),
		guild_id: guildId,
		game_id: game.id,
		game_name: game.name,
		title: input.title,
		version: input.version,
		summary: input.summary,
		highlights: input.highlights,
		url: input.url,
		published_at: input.published_at ? toSqlTimestamp(new Date(input.published_at)) : now,
		posted_at: now,
		source: 'grok'
	};
	await store.addPatchNote(note);
	return { created: true, entry: note };
}

export async function addSuggestion(guildId: string, games: Game[], input: SuggestionInput) {
	const inRotation = games.find(
		(g) => norm(g.name) === norm(input.name) || (input.rawg_slug && g.rawg_slug === input.rawg_slug)
	);
	if (inRotation) {
		throw new ApiError(
			409,
			'already_in_rotation',
			`${inRotation.name} is already in the rotation.`,
			{
				game_id: inRotation.id
			}
		);
	}

	const store = getFeedStore();
	const feed = await store.read(guildId);
	const existing = feed.suggestions.find(
		(s) => norm(s.name) === norm(input.name) || (input.rawg_slug && s.rawg_slug === input.rawg_slug)
	);
	if (existing) return { created: false, entry: existing };

	const suggestion: Suggestion = {
		id: crypto.randomUUID(),
		guild_id: guildId,
		...input,
		suggested_at: toSqlTimestamp(new Date()),
		source: 'grok'
	};
	await store.addSuggestion(suggestion);
	return { created: true, entry: suggestion };
}

export const newestFirst = <
	T extends { posted_at?: string; suggested_at?: string; published_at?: string }
>(
	a: T,
	b: T
) => (b.published_at ?? b.suggested_at ?? '').localeCompare(a.published_at ?? a.suggested_at ?? '');
