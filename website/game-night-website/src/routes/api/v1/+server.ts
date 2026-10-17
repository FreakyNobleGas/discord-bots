import { handler } from '#lib/server/api.ts';

export const GET = handler('read', async ({ url }) =>
	Response.json({
		name: "Cartman's Basement Crew API",
		version: 'v1',
		openapi: new URL('/api/v1/openapi.json', url).href,
		endpoints: [
			'GET /api/v1/rotation',
			'GET /api/v1/stats/genres?range=all|12m|90d',
			'GET /api/v1/stats/games?range=all|12m|90d&limit=',
			'GET /api/v1/profile',
			'GET /api/v1/patch-notes?game=&limit=',
			'POST /api/v1/patch-notes',
			'GET /api/v1/suggestions',
			'POST /api/v1/suggestions'
		]
	})
);
