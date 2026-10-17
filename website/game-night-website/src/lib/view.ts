// Small view helpers shared by pages (client-safe).

import { OTHER, OTHER_COLOR } from './genres';
import type { GameStats, GenreShare } from './types';

export const pct = (n: number) => (n > 0 && n < 0.005 ? '<1%' : `${Math.round(n * 100)}%`);
export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;

/** Collapse folded genres (all painted OTHER_COLOR) into one "Other" segment. */
export function foldShares(shares: GenreShare[]) {
	const out: GenreShare[] = [];
	let other: GenreShare | null = null;
	for (const s of shares) {
		if (s.color === OTHER_COLOR) {
			other ??= { genre: OTHER, sessions: 0, share: 0, games: 0, color: OTHER_COLOR };
			other.sessions += s.sessions;
			other.share += s.share;
			other.games += s.games;
		} else out.push(s);
	}
	if (other) out.push(other);
	return out;
}

export function genreColorMap(shares: GenreShare[]) {
	return new Map(shares.map((s) => [s.genre, s.color]));
}

export const colorFor = (colors: Map<string, string>, st: GameStats) =>
	colors.get(st.primary_genre) ?? OTHER_COLOR;
