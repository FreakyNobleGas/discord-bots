import { defineEnvVars } from '@sveltejs/kit/env';
import { z } from 'zod';

export const variables = defineEnvVars({
	DATABASE_URL: {
		description:
			'Neon Postgres (pooled) shared with the game night bot. Unset = mock data + file feed.',
		schema: z.string().optional()
	},
	DISCORD_GUILD_ID: {
		description: 'Discord guild the site shows by default (and the admin page edits).',
		schema: z
			.string()
			.regex(/^\d{1,20}$/)
			.optional()
	},
	API_TOKEN: {
		description:
			'Bearer token Grok Bot sends to /api/v1. Required for POSTs; when set, also required for GETs.',
		schema: z.string().optional()
	},
	ADMIN_PASSWORD: {
		description: 'Password for /admin. Admin is disabled while unset.',
		schema: z.string().optional()
	},
	ADMIN_SESSION_SECRET: {
		description: 'Random secret (32+ chars) that signs the admin session cookie.',
		schema: z.string().min(32).optional()
	},
	GAME_NIGHT_TZ: {
		description:
			'IANA timezone used to bucket sessions into game nights (default America/New_York).',
		schema: z.string().optional()
	},
	FEED_PATH: {
		description: 'Mock mode only: where the file feed store keeps patch notes and suggestions.',
		schema: z.string().optional()
	}
});
