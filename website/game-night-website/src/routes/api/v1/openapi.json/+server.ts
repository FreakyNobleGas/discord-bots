// Hand-written OpenAPI 3.1 spec so Grok Bot can be configured with tool definitions.
// Served without auth — it describes the API, it doesn't expose data.

const rangeParam = {
	name: 'range',
	in: 'query',
	schema: { type: 'string', enum: ['all', '12m', '90d'], default: 'all' }
};
const guildParam = {
	name: 'guild',
	in: 'query',
	description: 'Discord guild id (string). Defaults to the configured guild.',
	schema: { type: 'string' }
};
const limitParam = {
	name: 'limit',
	in: 'query',
	schema: { type: 'integer', minimum: 1, maximum: 100 }
};
const error = {
	description: 'Error',
	content: {
		'application/json': {
			schema: {
				type: 'object',
				properties: {
					error: {
						type: 'object',
						properties: {
							code: { type: 'string' },
							message: { type: 'string' },
							details: {}
						}
					}
				}
			}
		}
	}
};
const json = (description: string, schema: object = { type: 'object' }) => ({
	description,
	content: { 'application/json': { schema } }
});

const patchNoteInput = {
	type: 'object',
	required: ['game', 'title', 'summary'],
	properties: {
		game: {
			type: 'object',
			description:
				'Which rotation game this is for. Matched by rawg_slug, then game_id, then name (case-insensitive).',
			properties: {
				rawg_slug: { type: 'string' },
				game_id: { type: 'integer' },
				name: { type: 'string' }
			}
		},
		title: { type: 'string', maxLength: 200 },
		version: {
			type: 'string',
			maxLength: 50,
			description: 'Used with the game to de-duplicate posts.'
		},
		summary: { type: 'string', maxLength: 2000, description: 'Plain text; rendered as-is.' },
		highlights: { type: 'array', maxItems: 15, items: { type: 'string', maxLength: 300 } },
		url: { type: 'string', format: 'uri', description: 'http(s) link to the official notes.' },
		published_at: { type: 'string', description: 'ISO date or datetime with offset.' }
	}
};

const suggestionInput = {
	type: 'object',
	required: ['name', 'genres', 'reason'],
	properties: {
		name: { type: 'string', maxLength: 200 },
		rawg_slug: { type: 'string', pattern: '^[a-z0-9-]+$' },
		rawg_id: { type: 'integer' },
		genres: {
			type: 'array',
			minItems: 1,
			maxItems: 10,
			items: { type: 'string' },
			description: 'RAWG genre names (e.g. Shooter, RPG, Simulation) so genre fit can be scored.'
		},
		reason: { type: 'string', maxLength: 1000 },
		similar_to: {
			type: 'array',
			maxItems: 10,
			items: { type: 'string' },
			description: 'Rotation game names.'
		},
		platforms: { type: 'array', maxItems: 15, items: { type: 'string' } },
		release_date: { type: 'string', format: 'date' },
		url: { type: 'string', format: 'uri' }
	}
};

const spec = {
	openapi: '3.1.0',
	info: {
		title: "Cartman's Basement Crew — Game Night API",
		version: '1.0.0',
		description:
			'Read the crew’s rotation and tastes; post patch notes for rotation games and suggest new games. ' +
			'Send `Authorization: Bearer <API_TOKEN>`. POSTs need `Content-Type: application/json`.'
	},
	servers: [{ url: '/' }],
	components: {
		securitySchemes: { bearer: { type: 'http', scheme: 'bearer' } },
		schemas: { PatchNoteInput: patchNoteInput, SuggestionInput: suggestionInput }
	},
	security: [{ bearer: [] }],
	paths: {
		'/api/v1/rotation': {
			get: {
				operationId: 'getRotation',
				summary:
					'Every game in the rotation with RAWG ids, genres and play recency. Use rawg_slug to look up updates.',
				parameters: [guildParam],
				responses: { '200': json('Rotation'), '401': error }
			}
		},
		'/api/v1/stats/genres': {
			get: {
				operationId: 'getGenreStats',
				summary: 'Genre share (sums to 1), tag reach (multi-tag), and monthly genre mix.',
				parameters: [guildParam, rangeParam],
				responses: { '200': json('Genre stats'), '401': error }
			}
		},
		'/api/v1/stats/games': {
			get: {
				operationId: 'getGameStats',
				summary:
					'Most-played leaderboard and games collecting dust (30+ days idle or never played).',
				parameters: [guildParam, rangeParam, limitParam],
				responses: { '200': json('Game stats'), '401': error }
			}
		},
		'/api/v1/profile': {
			get: {
				operationId: 'getTasteProfile',
				summary:
					'LLM-ready taste summary for suggesting new games: top genres, favorites, games that fell off, recent adds, and an exclude list.',
				parameters: [guildParam],
				responses: { '200': json('Taste profile'), '401': error }
			}
		},
		'/api/v1/patch-notes': {
			get: {
				operationId: 'listPatchNotes',
				summary: 'Recent patch notes, newest first. Check before posting to avoid duplicates.',
				parameters: [
					guildParam,
					{
						name: 'game',
						in: 'query',
						description: 'game_id, rawg_slug or name',
						schema: { type: 'string' }
					},
					limitParam
				],
				responses: { '200': json('Patch notes'), '401': error }
			},
			post: {
				operationId: 'postPatchNote',
				summary: 'Post patch notes for a game in the rotation.',
				parameters: [guildParam],
				requestBody: {
					required: true,
					content: {
						'application/json': { schema: { $ref: '#/components/schemas/PatchNoteInput' } }
					}
				},
				responses: {
					'201': json('Created'),
					'200': json('Duplicate — returns the existing entry'),
					'400': error,
					'401': error,
					'415': error,
					'422': {
						...error,
						description: 'Game not in rotation; details.rotation lists valid games'
					}
				}
			}
		},
		'/api/v1/suggestions': {
			get: {
				operationId: 'listSuggestions',
				summary: 'Game suggestions with a genre_fit score (0–1).',
				parameters: [guildParam, limitParam],
				responses: { '200': json('Suggestions'), '401': error }
			},
			post: {
				operationId: 'postSuggestion',
				summary: 'Suggest a new game for the crew. Rejected with 409 if already in the rotation.',
				parameters: [guildParam],
				requestBody: {
					required: true,
					content: {
						'application/json': { schema: { $ref: '#/components/schemas/SuggestionInput' } }
					}
				},
				responses: {
					'201': json('Created'),
					'200': json('Duplicate — returns the existing entry'),
					'400': error,
					'401': error,
					'409': error,
					'415': error
				}
			}
		}
	}
};

export const GET = () => Response.json(spec);
