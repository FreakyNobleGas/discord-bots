import { DISCORD_GUILD_ID, GAME_NIGHT_TZ } from '$app/env/private';
import { analyze } from '#lib/analytics.ts';
import type { Range } from '#lib/types.ts';
import { dbEnabled } from '../db/pool';
import { getFeedStore } from '../feed/store';
import { MOCK_GUILD_ID, mockSource } from './mock';
import { postgresSource } from './postgres';
import type { DataSource } from './source';

export const DEFAULT_GUILD_ID = DISCORD_GUILD_ID || MOCK_GUILD_ID;
export const TIMEZONE = GAME_NIGHT_TZ || 'America/New_York';

/** The bot's shared Postgres when DATABASE_URL is set; otherwise seeded mock data. */
export function getDataSource(): DataSource {
	return dbEnabled() ? postgresSource : mockSource;
}

/** Load the guild's rows plus Grok's feed, and run the shared analytics. */
export async function loadAnalysis(range: Range, guildId = DEFAULT_GUILD_ID) {
	const source = getDataSource();
	const [games, sessions, feed] = await Promise.all([
		source.getGames(guildId),
		source.getSessions(guildId),
		getFeedStore().read(guildId)
	]);
	const analysis = analyze({
		games,
		sessions,
		range,
		tz: TIMEZONE,
		patchNotes: feed.patch_notes.filter((p) => games.some((g) => g.id === p.game_id))
	});
	return { games, sessions, feed, analysis };
}
