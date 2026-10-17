// A few example posts so /patch-notes and /suggestions aren't empty on first run.
// These are mock entries, marked with source "mock-seed" — not real patch notes.

import { toSqlTimestamp } from '#lib/dates.ts';
import type { Feed, PatchNote, Suggestion } from '#lib/types.ts';
import { MOCK_GUILD_ID, mockSource } from '../data/mock';

const daysAgo = (n: number) => toSqlTimestamp(new Date(Date.now() - n * 86_400_000));

export async function seedFeed() {
	const games = await mockSource.getGames(MOCK_GUILD_ID);
	const byName = (name: string) => games.find((g) => g.name === name)!;

	const note = (
		name: string,
		ago: number,
		fields: Pick<PatchNote, 'title' | 'version' | 'summary' | 'highlights'>
	): PatchNote => {
		const g = byName(name);
		return {
			id: crypto.randomUUID(),
			guild_id: MOCK_GUILD_ID,
			game_id: g.id,
			game_name: g.name,
			url: null,
			published_at: daysAgo(ago),
			posted_at: daysAgo(ago),
			source: 'mock-seed',
			...fields
		};
	};

	const patch_notes: PatchNote[] = [
		note('Halo Infinite', 3, {
			title: 'Winter operation and custom games browser refresh',
			version: null,
			summary:
				'Mock entry: a new seasonal operation with a free reward track, plus a rebuilt custom games browser.',
			highlights: [
				'New 4-player co-op playlist',
				'Custom games browser filters',
				'Weapon tuning pass'
			]
		}),
		note('Helldivers 2', 9, {
			title: 'Major order update',
			version: '1.4.2',
			summary: 'Mock entry: balance changes to support weapons and a new mission modifier.',
			highlights: ['Support weapon reload speeds adjusted', 'New "Blackout" mission modifier']
		}),
		note('Age of Empires II: Definitive Edition', 12, {
			title: 'Ranked season reset',
			version: null,
			summary: 'Mock entry: ranked ladder reset and a new co-op campaign scenario.',
			highlights: ['Co-op scenario pack', 'Map pool rotation']
		}),
		note('Deep Rock Galactic', 41, {
			title: 'Season patch',
			version: '1.39.2',
			summary: 'Mock entry: stability fixes and cosmetic drops for the current season.',
			highlights: ['Crash fixes on host migration', 'Seasonal cosmetics']
		})
	];

	const suggestion = (
		ago: number,
		fields: Omit<Suggestion, 'id' | 'guild_id' | 'suggested_at' | 'source'>
	): Suggestion => ({
		id: crypto.randomUUID(),
		guild_id: MOCK_GUILD_ID,
		suggested_at: daysAgo(ago),
		source: 'mock-seed',
		...fields
	});

	const suggestions: Suggestion[] = [
		suggestion(2, {
			name: 'R.E.P.O.',
			rawg_slug: null,
			rawg_id: null,
			genres: ['Indie', 'Simulation', 'Action'],
			reason:
				'Mock entry: physics-based co-op horror in the same vein as Lethal Company and Content Warning.',
			similar_to: ['Lethal Company', 'Content Warning'],
			platforms: ['PC'],
			release_date: null,
			url: null
		}),
		suggestion(6, {
			name: 'Risk of Rain 2',
			rawg_slug: 'risk-of-rain-2',
			rawg_id: null,
			genres: ['Action', 'Shooter', 'Indie'],
			reason: 'Mock entry: 4-player co-op shooter runs, scratching the Deep Rock Galactic itch.',
			similar_to: ['Deep Rock Galactic', 'Helldivers 2'],
			platforms: ['PC', 'PlayStation', 'Xbox', 'Nintendo Switch'],
			release_date: '2020-08-11',
			url: null
		}),
		suggestion(15, {
			name: 'Divinity: Original Sin 2',
			rawg_slug: 'divinity-original-sin-2',
			rawg_id: null,
			genres: ['RPG', 'Strategy'],
			reason: "Mock entry: co-op tactical RPG for when the crew misses Baldur's Gate 3.",
			similar_to: ["Baldur's Gate 3"],
			platforms: ['PC', 'PlayStation', 'Xbox'],
			release_date: '2017-09-14',
			url: null
		})
	];

	const feed: Feed = { patch_notes, suggestions };
	return { version: 1 as const, guilds: { [MOCK_GUILD_ID]: feed } };
}
