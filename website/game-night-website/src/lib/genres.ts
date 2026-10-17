// Ported from the bot's bot/utils/embeds.py so the site picks the same emoji and
// "primary" genre the Discord embeds do.

export const GENRE_EMOJIS: Record<string, string> = {
	shooter: '🔫',
	horror: '👻',
	simulation: '🔬',
	automation: '🔬',
	action: '⚔️',
	rpg: '🎭',
	strategy: '♟️',
	sports: '⚽',
	racing: '🏎️',
	puzzle: '🧩',
	adventure: '🗺️',
	survival: '🏕️',
	indie: '🎨',
	arcade: '🕹️',
	fighting: '🥊',
	platformer: '🦘',
	card: '🃏',
	'sci-fi': '🚀',
	'co-op': '🤝',
	'massively multiplayer': '🌐',
	casual: '🎲'
};

/** Tags that are too broad to be useful as a primary identifier */
export const GENERIC_TAGS = new Set(['action', 'adventure', 'indie']);

/** Per-game overrides for games RAWG doesn't tag specifically enough */
export const GAME_OVERRIDES: Record<string, string> = {
	phasmophobia: '👻',
	'content warning': '📹',
	'helldivers 2': '🪖',
	'warhammer 40,000: space marine ii': '🪖',
	'toxic commando': '☣️',
	'diablo iv': '😈',
	'abiotic factor': '🧪',
	'roadside research': '🗺️',
	'halo infinite': '🔫',
	'the first descendant': '🔫'
};

export const UNTAGGED = 'Untagged';
export const OTHER = 'Other';

export function primaryEmoji(tags: string[], name = ''): string {
	const override = name ? GAME_OVERRIDES[name.toLowerCase()] : undefined;
	if (override) return override;
	for (const tag of tags) {
		const emoji = GENRE_EMOJIS[tag.toLowerCase()];
		if (emoji && !GENERIC_TAGS.has(tag.toLowerCase())) return emoji;
	}
	for (const tag of tags) {
		const emoji = GENRE_EMOJIS[tag.toLowerCase()];
		if (emoji) return emoji;
	}
	return '🎮';
}

/** First specific tag, else first tag, else "Untagged" (manual adds have no tags). */
export function primaryGenre(tags: string[]): string {
	return tags.find((t) => !GENERIC_TAGS.has(t.toLowerCase())) ?? tags[0] ?? UNTAGGED;
}

/** Tags worth scoring on: specific ones if any, otherwise whatever is there. */
export function specificTags(tags: string[]): string[] {
	const specific = tags.filter((t) => !GENERIC_TAGS.has(t.toLowerCase()));
	return specific.length ? specific : tags;
}

// Categorical chart slots, validated with the dataviz palette validator against both
// card surfaces (see src/routes/layout.css). Order is the CVD-safety mechanism.
export const SERIES_SLOTS = 8;
export const seriesVar = (slot: number) => `var(--series-${slot + 1})`;
export const OTHER_COLOR = 'var(--series-other)';
