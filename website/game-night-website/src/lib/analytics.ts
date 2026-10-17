// Pure analytics over the bot's rows. Pages and the API both go through analyze(), so the
// numbers on the site and the numbers Grok sees always agree.

import {
	addDays,
	daysBetween,
	monthKey,
	monthRange,
	nightKey,
	parseSqlTimestamp,
	weekKey
} from './dates';
import {
	GENERIC_TAGS,
	OTHER,
	OTHER_COLOR,
	SERIES_SLOTS,
	primaryEmoji,
	primaryGenre,
	seriesVar,
	specificTags
} from './genres';
import type {
	Analysis,
	Game,
	GameStats,
	GenreShare,
	MonthBucket,
	PatchNote,
	Range,
	Session,
	TagReach
} from './types';

export const RECENT_PATCH_DAYS = 14;
export const DUST_MIN_DAYS = 30;

const RANGE_DAYS: Record<Range, number | null> = { all: null, '12m': 365, '90d': 90 };

export function parseRange(value: string | null | undefined): Range {
	return value === '12m' || value === '90d' ? value : 'all';
}

interface AnalyzeInput {
	games: Game[];
	sessions: Session[];
	range: Range;
	tz: string;
	now?: Date;
	patchNotes?: PatchNote[];
}

/**
 * Colors follow the genre, never its rank in the current range: slots are assigned from
 * all-time play counts so filtering never repaints a genre.
 */
function genreColors(games: Game[], sessions: Session[]) {
	const genreOf = new Map(games.map((g) => [g.id, primaryGenre(g.genre_tags)]));
	const counts = new Map<string, number>();
	for (const g of games) counts.set(genreOf.get(g.id)!, 0);
	for (const s of sessions) {
		const genre = genreOf.get(s.game_id);
		if (genre) counts.set(genre, (counts.get(genre) ?? 0) + 1);
	}
	const ranked = [...counts.entries()]
		.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
		.map(([genre]) => genre);

	const fold = ranked.length > SERIES_SLOTS;
	const kept = fold ? ranked.slice(0, SERIES_SLOTS - 1) : ranked;
	const color = new Map<string, string>();
	const seriesKey = new Map<string, string>();
	kept.forEach((genre, i) => {
		color.set(genre, seriesVar(i));
		seriesKey.set(genre, genre);
	});
	for (const genre of ranked.slice(kept.length)) {
		color.set(genre, OTHER_COLOR);
		seriesKey.set(genre, OTHER);
	}
	const series = kept.map((key, i) => ({ key, color: seriesVar(i) }));
	if (fold) series.push({ key: OTHER, color: OTHER_COLOR });
	return { color, seriesKey, series };
}

export function analyze({
	games,
	sessions,
	range,
	tz,
	now = new Date(),
	patchNotes = []
}: AnalyzeInput): Analysis {
	const today = nightKey(now, tz);
	const rangeDays = RANGE_DAYS[range];
	const since = rangeDays === null ? null : addDays(today, -rangeDays);

	const gameById = new Map(games.map((g) => [g.id, g]));
	const keyed = sessions
		.filter((s) => gameById.has(s.game_id))
		.map((s) => ({ s, night: nightKey(s.played_on, tz) }))
		.sort((a, b) => a.night.localeCompare(b.night));
	const inRange = since ? keyed.filter((k) => k.night >= since) : keyed;
	const total = inRange.length;

	const { color, seriesKey, series } = genreColors(
		games,
		keyed.map((k) => k.s)
	);
	const genreOf = (g: Game) => primaryGenre(g.genre_tags);

	// Months covered by the range (or by the data, for "all")
	const firstMonth = monthKey(since ?? keyed[0]?.night ?? today);
	const monthList = monthRange(firstMonth, monthKey(today));
	const monthIndex = new Map(monthList.map((m, i) => [m, i]));

	// Patch badges
	const patchCutoff = now.getTime() - RECENT_PATCH_DAYS * 86_400_000;
	const patchedGames = new Set(
		patchNotes
			.filter((p) => parseSqlTimestamp(p.published_at).getTime() >= patchCutoff)
			.map((p) => p.game_id)
	);

	// Per-game stats
	const statsById = new Map<number, GameStats>();
	for (const g of games) {
		statsById.set(g.id, {
			game: g,
			primary_genre: genreOf(g),
			emoji: primaryEmoji(g.genre_tags, g.name),
			session_count: 0,
			share: 0,
			total_sessions: 0,
			first_played: null,
			last_played: null,
			days_since_played: null,
			monthly: monthList.map(() => 0),
			has_recent_patch: patchedGames.has(g.id)
		});
	}
	for (const { s, night } of keyed) {
		const st = statsById.get(s.game_id)!;
		st.total_sessions++;
		st.first_played ??= night;
		st.last_played = night;
	}
	for (const { s, night } of inRange) {
		const st = statsById.get(s.game_id)!;
		st.session_count++;
		const mi = monthIndex.get(monthKey(night));
		if (mi !== undefined) st.monthly[mi]++;
	}
	const stats = [...statsById.values()];
	for (const st of stats) {
		st.share = total ? st.session_count / total : 0;
		st.days_since_played = st.last_played ? daysBetween(st.last_played, today) : null;
	}
	stats.sort(
		(a, b) =>
			b.session_count - a.session_count ||
			b.total_sessions - a.total_sessions ||
			a.game.name.localeCompare(b.game.name)
	);

	// Genre share (primary genre — sums to 100%)
	const shareMap = new Map<string, GenreShare>();
	for (const g of games) {
		const genre = genreOf(g);
		const row = shareMap.get(genre) ?? {
			genre,
			sessions: 0,
			share: 0,
			games: 0,
			color: color.get(genre) ?? OTHER_COLOR
		};
		row.games++;
		shareMap.set(genre, row);
	}
	for (const { s } of inRange) shareMap.get(genreOf(gameById.get(s.game_id)!))!.sessions++;
	const genre_share = [...shareMap.values()]
		.map((r) => ({ ...r, share: total ? r.sessions / total : 0 }))
		.sort((a, b) => b.sessions - a.sessions || a.genre.localeCompare(b.genre));

	// Tag reach (multi-tag — a session counts toward every tag on its game)
	const tagMap = new Map<string, number>();
	for (const { s } of inRange) {
		for (const tag of gameById.get(s.game_id)!.genre_tags) {
			tagMap.set(tag, (tagMap.get(tag) ?? 0) + 1);
		}
	}
	const tag_reach: TagReach[] = [...tagMap.entries()]
		.map(([tag, n]) => ({ tag, sessions: n, reach: total ? n / total : 0 }))
		.sort((a, b) => b.sessions - a.sessions || a.tag.localeCompare(b.tag));

	// Monthly genre mix
	const months: MonthBucket[] = monthList.map((month) => ({
		month,
		counts: Object.fromEntries(series.map((sr) => [sr.key, 0])),
		total: 0
	}));
	for (const { s, night } of inRange) {
		const bucket = months[monthIndex.get(monthKey(night))!];
		if (!bucket) continue;
		const key = seriesKey.get(genreOf(gameById.get(s.game_id)!)) ?? OTHER;
		bucket.counts[key] = (bucket.counts[key] ?? 0) + 1;
		bucket.total++;
	}

	// Weekly streak: consecutive weeks with a game night, counting back from this week
	// (or last week, if this week's night hasn't happened yet).
	const weeks = new Set(keyed.map((k) => weekKey(k.night)));
	let cursor = weekKey(today);
	if (!weeks.has(cursor)) cursor = addDays(cursor, -7);
	let weekly_streak = 0;
	while (weeks.has(cursor)) {
		weekly_streak++;
		cursor = addDays(cursor, -7);
	}

	const collecting_dust = stats
		.filter((st) => st.days_since_played === null || st.days_since_played >= DUST_MIN_DAYS)
		.sort((a, b) => (b.days_since_played ?? Infinity) - (a.days_since_played ?? Infinity));

	return {
		range,
		generated_at: now.toISOString(),
		kpis: {
			sessions: total,
			game_nights: new Set(inRange.map((k) => k.night)).size,
			games_in_rotation: games.length,
			top_genre: genre_share[0]?.sessions ? genre_share[0].genre : null,
			weekly_streak
		},
		games: stats,
		genre_share,
		tag_reach,
		months,
		month_series: series,
		collecting_dust
	};
}

/**
 * How well a suggested game's genres match what the crew actually plays (0–1): the mean
 * tag reach of its specific genres, relative to the crew's most-played specific tag — so
 * matching their #1 genre scores 1, and "Action" doesn't inflate every score.
 */
export function genreFit(genres: string[], tagReach: TagReach[]): number {
	const tags = specificTags(genres);
	const best = Math.max(
		0,
		...tagReach.filter((t) => !GENERIC_TAGS.has(t.tag.toLowerCase())).map((t) => t.reach)
	);
	if (!tags.length || !best) return 0;
	const reach = new Map(tagReach.map((t) => [t.tag.toLowerCase(), t.reach]));
	const mean = tags.reduce((sum, t) => sum + (reach.get(t.toLowerCase()) ?? 0), 0) / tags.length;
	return Math.min(1, mean / best);
}
