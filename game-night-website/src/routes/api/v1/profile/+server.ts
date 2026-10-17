import { apiParams, handler } from '#lib/server/api.ts';
import { loadAnalysis } from '#lib/server/data/index.ts';
import { daysBetween, nightKey } from '#lib/dates.ts';
import { TIMEZONE } from '#lib/server/data/index.ts';

const pct = (n: number) => `${Math.round(n * 100)}%`;

/** Taste summary shaped for an LLM prompt: "what should this crew play next?" */
export const GET = handler('read', async ({ url }) => {
	const { guildId } = apiParams(url);
	const { analysis: year, feed, games } = await loadAnalysis('12m', guildId);
	const today = nightKey(new Date(), TIMEZONE);

	const top_genres = year.genre_share
		.filter((g) => g.sessions > 0)
		.slice(0, 6)
		.map((g) => ({ genre: g.genre, weight: Math.round(g.share * 1000) / 1000 }));
	const favorite_games = year.games
		.filter((g) => g.session_count > 0)
		.slice(0, 5)
		.map((g) => ({
			name: g.game.name,
			rawg_slug: g.game.rawg_slug,
			sessions: g.session_count,
			genres: g.game.genre_tags
		}));
	const fell_off = year.collecting_dust
		.filter((g) => g.total_sessions >= 3)
		.slice(0, 5)
		.map((g) => ({
			name: g.game.name,
			rawg_slug: g.game.rawg_slug,
			days_since_played: g.days_since_played
		}));
	const recently_added = games
		.filter((g) => daysBetween(nightKey(g.added_at, TIMEZONE), today) <= 60)
		.map((g) => ({ name: g.name, rawg_slug: g.rawg_slug, added_at: g.added_at }));

	const summary =
		`Over the last 12 months the crew logged ${year.kpis.sessions} sessions across ${year.kpis.game_nights} game nights. ` +
		(top_genres.length
			? `They lean ${top_genres
					.slice(0, 3)
					.map((g) => `${g.genre} (${pct(g.weight)})`)
					.join(', ')}. `
			: '') +
		(favorite_games.length
			? `Favorites: ${favorite_games
					.slice(0, 3)
					.map((g) => g.name)
					.join(', ')}. `
			: '') +
		'Suggest co-op/multiplayer games not in the exclude list.';

	return Response.json({
		guild_id: guildId,
		window: '12m',
		summary,
		top_genres,
		tag_reach: year.tag_reach
			.slice(0, 10)
			.map((t) => ({ tag: t.tag, reach: Math.round(t.reach * 1000) / 1000 })),
		favorite_games,
		fell_off,
		recently_added,
		exclude: games.map((g) => g.name).sort(),
		already_suggested: feed.suggestions.map((s) => s.name)
	});
});
