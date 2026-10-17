// Every themed string on the site, in one place — the website's version of the bot's
// locale.json. Tweak the voice here without touching components.

export const copy = {
	site: {
		name: "Cartman's Basement Crew",
		tagline: 'Game night stats from the basement. Respect the rotation.',
		footer: 'Built for the game night bot'
	},
	nav: {
		overview: 'The Basement',
		genres: 'Genres',
		games: 'Leaderboard',
		patchNotes: 'Patch Notes',
		suggestions: "Grok's Picks"
	},
	range: {
		label: 'Time range',
		all: 'All time',
		'12m': '12 months',
		'90d': '90 days'
	},
	overview: {
		title: 'The Basement',
		intro: "Here's what the crew has been playing. Mom, we're busy.",
		genreMix: 'Genre mix',
		topGames: 'Most played',
		dust: 'Forgotten in the basement',
		dustIntro: 'Still in the rotation, not touched in a while.'
	},
	kpis: {
		sessions: 'Sessions logged',
		nights: 'Game nights',
		rotation: 'Games in rotation',
		streak: 'Weekly streak'
	},
	genres: {
		title: 'Genres',
		intro: 'What kinds of games actually get played, not just added.',
		share: 'Share of sessions by genre',
		shareNote:
			"Each session counts once, under its game's main genre (same rule as the bot's emoji).",
		mix: 'Genre mix over time',
		reach: 'Tag reach',
		reachNote:
			'Share of sessions where the game carries the tag. Games have several tags, so these add up past 100%.',
		pick: 'Pick a genre to see its games.'
	},
	games: {
		title: 'Leaderboard',
		intro: 'Who gets played, and who gets left in the basement.',
		dust: 'Forgotten in the basement',
		dustIntro: "Games nobody has touched in 30+ days. Somebody's feelings are hurt.",
		newPatch: 'New patch',
		neverPlayed: 'Never played'
	},
	patchNotes: {
		title: 'Patch Notes',
		intro: 'Updates Grok spotted for games in the rotation.',
		empty: "No patch notes yet. Grok hasn't found anything. Screw it, play anyway.",
		allGames: 'All games',
		filter: 'Game'
	},
	suggestions: {
		title: "Grok's Picks",
		intro: 'New games Grok thinks the crew would actually play.',
		empty: "Grok hasn't suggested anything yet. Weak.",
		fit: 'Genre fit',
		fitNote: "How closely the game's genres match what the crew plays.",
		similar: 'Similar to',
		sortNewest: 'Newest',
		sortFit: 'Best fit'
	},
	admin: {
		title: 'Admin',
		intro: 'Fix the records by hand. Changes show up on the site and in the bot right away.',
		nav: 'Admin',
		login: 'Respect my authoritah',
		loginIntro: 'Admin only. Everyone else, go home.',
		password: 'Password',
		signIn: 'Sign in',
		signOut: 'Sign out',
		wrongPassword: "Nice try. That's not the password.",
		disabled:
			'Admin is turned off. Set DATABASE_URL, ADMIN_PASSWORD and ADMIN_SESSION_SECRET to enable it.',
		games: 'Games',
		sessions: 'Sessions',
		patchNotes: 'Patch notes',
		suggestions: "Grok's picks",
		save: 'Save',
		edit: 'Edit',
		add: 'Add',
		delete: 'Delete…',
		reallyDelete: 'Really delete',
		gameDeleteNote: 'Also deletes its sessions and patch notes.'
	},
	empty: {
		sessions: "Nobody's played anything in this range. Weak."
	},
	api: {
		unauthorized:
			"You're not on the list. Respect the basement's authoritah (send a valid bearer token)."
	}
} as const;
