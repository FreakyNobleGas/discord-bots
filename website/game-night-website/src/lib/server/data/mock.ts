// Deterministic mock of the bot's SQLite data: ~14 months of Friday/Saturday game nights
// for Cartman's Basement Crew. Seeded per day, so reloads are stable and "days since"
// stays realistic relative to today.

import { addDays, toSqlTimestamp } from '#lib/dates.ts';
import type { Game, Session } from '#lib/types.ts';
import type { DataSource } from './source';

export const MOCK_GUILD_ID = '1187654321098765432';

const CREW = ['freakynoblegas', 'stanmarsh_irl', 'kyle_brof', 'mysterion', 'butters_stotch'];
const LOGGER_WEIGHTS = [5, 3, 3, 1, 2];

interface MockGame {
	name: string;
	rawg_id: number | null;
	rawg_slug: string | null;
	genres: string[];
	added_by: string;
	/** Days after the start of the timeline the game was added */
	added: number;
	/** Base pick weight */
	weight: number;
	/** Stops being picked after this many days (goes stale) */
	until?: number;
	/** Extra weight in October/early November */
	spooky?: boolean;
	/** Multiplier for the first N days after being added */
	surge?: { days: number; mult: number };
	/** Multiplier inside a window of days */
	phase?: { from: number; to: number; mult: number };
}

// RAWG ids/slugs here are illustrative placeholders for the mock, not verified lookups.
const MOCK_GAMES: MockGame[] = [
	{
		name: 'Deep Rock Galactic',
		rawg_id: 58753,
		rawg_slug: 'deep-rock-galactic',
		genres: ['Action', 'Shooter', 'Indie'],
		added_by: 'freakynoblegas',
		added: 0,
		weight: 6
	},
	{
		name: 'Phasmophobia',
		rawg_id: 422856,
		rawg_slug: 'phasmophobia',
		genres: ['Action', 'Indie', 'Simulation'],
		added_by: 'mysterion',
		added: 0,
		weight: 1.5,
		spooky: true
	},
	{
		name: 'Lethal Company',
		rawg_id: 927424,
		rawg_slug: 'lethal-company',
		genres: ['Adventure', 'Indie', 'Simulation'],
		added_by: 'kyle_brof',
		added: 0,
		weight: 2,
		spooky: true
	},
	{
		name: 'Content Warning',
		rawg_id: 989501,
		rawg_slug: 'content-warning',
		genres: ['Indie', 'Simulation', 'Casual'],
		added_by: 'butters_stotch',
		added: 20,
		weight: 1,
		spooky: true
	},
	{
		name: 'Halo Infinite',
		rawg_id: 43252,
		rawg_slug: 'halo-infinite',
		genres: ['Action', 'Shooter'],
		added_by: 'stanmarsh_irl',
		added: 0,
		weight: 4,
		until: 120
	},
	{
		name: 'Age of Empires II: Definitive Edition',
		rawg_id: 50734,
		rawg_slug: 'age-of-empires-ii-definitive-edition',
		genres: ['Strategy'],
		added_by: 'kyle_brof',
		added: 0,
		weight: 3,
		until: 95
	},
	{
		name: 'Jackbox Party Pack 9',
		rawg_id: 872311,
		rawg_slug: 'the-jackbox-party-pack-9',
		genres: ['Casual'],
		added_by: 'butters_stotch',
		added: 0,
		weight: 3
	},
	{
		name: 'Rocket League',
		rawg_id: 2593,
		rawg_slug: 'rocket-league',
		genres: ['Sports', 'Racing'],
		added_by: 'stanmarsh_irl',
		added: 0,
		weight: 1.5
	},
	{
		name: 'Final Fantasy XIV Online',
		rawg_id: 24888,
		rawg_slug: 'final-fantasy-xiv-online',
		genres: ['RPG', 'Massively Multiplayer'],
		added_by: 'kyle_brof',
		added: 35,
		weight: 1.5,
		until: 110
	},
	{
		name: 'Helldivers 2',
		rawg_id: 846352,
		rawg_slug: 'helldivers-2',
		genres: ['Action', 'Shooter'],
		added_by: 'freakynoblegas',
		added: 120,
		weight: 4,
		surge: { days: 60, mult: 3 }
	},
	{
		name: 'Diablo IV',
		rawg_id: 452638,
		rawg_slug: 'diablo-iv',
		genres: ['Action', 'RPG'],
		added_by: 'mysterion',
		added: 40,
		weight: 2.5
	},
	{
		name: "Baldur's Gate 3",
		rawg_id: 324997,
		rawg_slug: 'baldurs-gate-3',
		genres: ['Adventure', 'RPG', 'Strategy'],
		added_by: 'kyle_brof',
		added: 150,
		weight: 1,
		phase: { from: 170, to: 260, mult: 5 }
	},
	{
		name: 'Sid Meier’s Civilization VI',
		rawg_id: 10243,
		rawg_slug: 'sid-meiers-civilization-vi',
		genres: ['Strategy', 'Simulation'],
		added_by: 'kyle_brof',
		added: 60,
		weight: 1.5,
		until: 280
	},
	{
		name: 'Warhammer 40,000: Space Marine II',
		rawg_id: 795632,
		rawg_slug: 'warhammer-40000-space-marine-2',
		genres: ['Action', 'Shooter'],
		added_by: 'stanmarsh_irl',
		added: 200,
		weight: 2.5
	},
	{
		name: 'The First Descendant',
		rawg_id: 846361,
		rawg_slug: 'the-first-descendant',
		genres: ['Action', 'Shooter', 'RPG', 'Massively Multiplayer'],
		added_by: 'mysterion',
		added: 230,
		weight: 1,
		until: 330
	},
	{
		name: 'Abiotic Factor',
		rawg_id: 916347,
		rawg_slug: 'abiotic-factor',
		genres: ['Adventure', 'Indie', 'Simulation'],
		added_by: 'freakynoblegas',
		added: 300,
		weight: 3,
		surge: { days: 40, mult: 2 }
	},
	{
		name: 'Golf With Your Friends',
		rawg_id: 41494,
		rawg_slug: 'golf-with-your-friends',
		genres: ['Sports', 'Casual', 'Indie'],
		added_by: 'butters_stotch',
		added: 90,
		weight: 1
	},
	{
		name: 'Keep Talking and Nobody Explodes',
		rawg_id: 11936,
		rawg_slug: 'keep-talking-and-nobody-explodes',
		genres: ['Puzzle', 'Indie', 'Casual'],
		added_by: 'butters_stotch',
		added: 250,
		weight: 0.8
	},
	{
		name: 'Toxic Commando',
		rawg_id: 914263,
		rawg_slug: 'john-carpenters-toxic-commando',
		genres: ['Action', 'Shooter'],
		added_by: 'stanmarsh_irl',
		added: 405,
		weight: 3,
		surge: { days: 30, mult: 3 }
	},
	{
		name: 'Roadside Research',
		rawg_id: null,
		rawg_slug: null,
		genres: [],
		added_by: 'mysterion',
		added: 340,
		weight: 1.5
	},
	{
		name: 'Basement Poker Night',
		rawg_id: null,
		rawg_slug: null,
		genres: [],
		added_by: 'freakynoblegas',
		added: 10,
		weight: 0.6
	},
	{
		name: 'Overcooked! 2',
		rawg_id: 28154,
		rawg_slug: 'overcooked-2',
		genres: ['Casual', 'Arcade', 'Simulation'],
		added_by: 'butters_stotch',
		added: 420,
		weight: 0
	}
];

const NOTES = [
	'Kenny died first. Again.',
	'Somebody forgot to bring the drill.',
	'Ran it back three times. Worth it.',
	'Stan rage-quit at 2am.',
	'Butters carried. Nobody saw it coming.',
	'Friendly fire was not friendly.',
	'New personal best, then immediately lost it all.',
	'Kyle read the patch notes out loud. All of them.',
	'Snacks ran out before the final round.',
	'Mic check took 20 minutes.'
];

function mulberry32(seed: number) {
	return () => {
		seed |= 0;
		seed = (seed + 0x6d2b79f5) | 0;
		let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

function pickWeighted<T>(rand: () => number, items: T[], weights: number[]): T {
	const total = weights.reduce((a, b) => a + b, 0);
	let r = rand() * total;
	for (let i = 0; i < items.length; i++) {
		r -= weights[i];
		if (r <= 0) return items[i];
	}
	return items[items.length - 1];
}

function weightOn(g: MockGame, day: number, month: number): number {
	if (day < g.added || (g.until !== undefined && day > g.until)) return 0;
	let w = g.weight;
	if (g.spooky && (month === 10 || month === 11)) w *= month === 10 ? 6 : 2;
	if (g.surge && day - g.added < g.surge.days) w *= g.surge.mult;
	if (g.phase && day >= g.phase.from && day <= g.phase.to) w *= g.phase.mult;
	return w;
}

/** Evening US-Eastern start time → UTC timestamp the bot would have stored */
function eveningUtc(nightKey: string, rand: () => number): string {
	const start = Date.parse(nightKey + 'T00:00:00Z') + (24 + Math.floor(rand() * 4)) * 3_600_000;
	return toSqlTimestamp(new Date(start + Math.floor(rand() * 60) * 60_000));
}

function build(now: Date) {
	const today = now.toISOString().slice(0, 10);
	const seed = Number(today.replaceAll('-', ''));
	const rand = mulberry32(seed);
	const TIMELINE_DAYS = 425; // ~14 months
	const start = addDays(today, -TIMELINE_DAYS);

	const games: Game[] = MOCK_GAMES.map((g, i) => ({
		id: i + 1,
		guild_id: MOCK_GUILD_ID,
		name: g.name,
		rawg_id: g.rawg_id,
		rawg_slug: g.rawg_slug,
		cover_url: '',
		genre_tags: g.genres,
		added_by: g.added_by,
		added_at: toSqlTimestamp(new Date(Date.parse(addDays(start, g.added) + 'T22:00:00Z')))
	}));

	const sessions: Session[] = [];
	for (let day = 0; day <= TIMELINE_DAYS; day++) {
		const key = addDays(start, day);
		const date = new Date(key + 'T12:00:00Z');
		const dow = date.getUTCDay();
		const month = date.getUTCMonth() + 1;
		// Friday is game night; Saturday sometimes; the odd weeknight
		const odds = dow === 5 ? 0.85 : dow === 6 ? 0.45 : dow === 3 ? 0.15 : 0;
		// Leave tonight's session unplayed if it's still daytime
		if (key === today || rand() >= odds) continue;

		const games_tonight = 2 + (rand() < 0.5 ? 1 : 0) + (rand() < 0.15 ? 1 : 0);
		const pool = MOCK_GAMES.map((g, i) => ({ i, w: weightOn(g, day, month) })).filter(
			(p) => p.w > 0
		);
		for (let n = 0; n < games_tonight && pool.length; n++) {
			const pick = pickWeighted(
				rand,
				pool,
				pool.map((p) => p.w)
			);
			pool.splice(pool.indexOf(pick), 1);
			sessions.push({
				id: sessions.length + 1,
				game_id: pick.i + 1,
				played_on: eveningUtc(key, rand),
				logged_by: pickWeighted(rand, CREW, LOGGER_WEIGHTS),
				notes: rand() < 0.12 ? NOTES[Math.floor(rand() * NOTES.length)] : null
			});
		}
	}
	return { games, sessions };
}

let cache: { day: string; data: ReturnType<typeof build> } | null = null;

function data() {
	const now = new Date();
	const day = now.toISOString().slice(0, 10);
	if (cache?.day !== day) cache = { day, data: build(now) };
	return cache.data;
}

export const mockSource: DataSource = {
	async getGames(guildId) {
		return guildId === MOCK_GUILD_ID ? data().games : [];
	},
	async getSessions(guildId) {
		return guildId === MOCK_GUILD_ID ? data().sessions : [];
	}
};
