// Row shapes mirror the bot's SQLite schema (bot/database.py).
// Discord snowflakes exceed Number.MAX_SAFE_INTEGER, so guild ids are strings here.

export interface Game {
	id: number;
	guild_id: string;
	name: string;
	rawg_id: number | null;
	rawg_slug: string | null;
	cover_url: string;
	genre_tags: string[];
	added_by: string;
	/** SQLite CURRENT_TIMESTAMP format, UTC: "YYYY-MM-DD HH:MM:SS" */
	added_at: string;
}

export interface Session {
	id: number;
	game_id: number;
	/** SQLite CURRENT_TIMESTAMP format, UTC: "YYYY-MM-DD HH:MM:SS" */
	played_on: string;
	logged_by: string | null;
	notes: string | null;
}

export type Range = 'all' | '12m' | '90d';
export const RANGES: Range[] = ['all', '12m', '90d'];

export interface GameStats {
	game: Game;
	primary_genre: string;
	emoji: string;
	/** Sessions inside the selected range */
	session_count: number;
	/** Share of all sessions inside the selected range (0–1) */
	share: number;
	/** All-time, independent of range */
	total_sessions: number;
	first_played: string | null;
	last_played: string | null;
	days_since_played: number | null;
	/** Sessions per month over the range's months, oldest first */
	monthly: number[];
	has_recent_patch: boolean;
}

export interface GenreShare {
	genre: string;
	sessions: number;
	share: number;
	games: number;
	color: string;
}

export interface TagReach {
	tag: string;
	sessions: number;
	reach: number;
}

export interface MonthBucket {
	/** "YYYY-MM" */
	month: string;
	counts: Record<string, number>;
	total: number;
}

export interface Kpis {
	sessions: number;
	game_nights: number;
	games_in_rotation: number;
	top_genre: string | null;
	weekly_streak: number;
}

export interface Analysis {
	range: Range;
	generated_at: string;
	kpis: Kpis;
	games: GameStats[];
	genre_share: GenreShare[];
	tag_reach: TagReach[];
	months: MonthBucket[];
	/** Series keys for `months`, in fixed color order (folded genres become "Other") */
	month_series: { key: string; color: string }[];
	collecting_dust: GameStats[];
}

export interface PatchNote {
	id: string;
	guild_id: string;
	game_id: number;
	game_name: string;
	title: string;
	version: string | null;
	summary: string;
	highlights: string[];
	url: string | null;
	published_at: string;
	posted_at: string;
	source: string;
}

export interface Suggestion {
	id: string;
	guild_id: string;
	name: string;
	rawg_slug: string | null;
	rawg_id: number | null;
	genres: string[];
	reason: string;
	similar_to: string[];
	platforms: string[];
	release_date: string | null;
	url: string | null;
	suggested_at: string;
	source: string;
}

export interface Feed {
	patch_notes: PatchNote[];
	suggestions: Suggestion[];
}
