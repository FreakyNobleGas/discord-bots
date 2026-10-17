import { timingSafeEqual } from 'node:crypto';
import type { RequestEvent } from '@sveltejs/kit';
import { API_TOKEN } from '$app/env/private';
import { copy } from '#lib/copy.ts';
import { parseRange } from '#lib/analytics.ts';
import { DEFAULT_GUILD_ID } from './data';

export class ApiError extends Error {
	constructor(
		public status: number,
		public code: string,
		message: string,
		public details?: unknown
	) {
		super(message);
	}
}

export function errorResponse(err: ApiError) {
	return Response.json(
		{ error: { code: err.code, message: err.message, details: err.details } },
		{ status: err.status }
	);
}

function tokenMatches(header: string | null, token: string) {
	const given = header?.match(/^Bearer\s+(.+)$/i)?.[1] ?? '';
	const a = Buffer.from(given);
	const b = Buffer.from(token);
	return a.length === b.length && timingSafeEqual(a, b);
}

/** Writes always need the token; reads only once API_TOKEN is configured. */
export function authorize(request: Request, mode: 'read' | 'write') {
	if (!API_TOKEN) {
		if (mode === 'write') {
			throw new ApiError(503, 'writes_disabled', 'Set API_TOKEN to enable POST endpoints.');
		}
		return;
	}
	if (!tokenMatches(request.headers.get('authorization'), API_TOKEN)) {
		throw new ApiError(401, 'unauthorized', copy.api.unauthorized);
	}
}

export function apiParams(url: URL) {
	const guildId = url.searchParams.get('guild') || DEFAULT_GUILD_ID;
	// Discord snowflakes; anything else would fail the bigint cast in Postgres.
	if (!/^\d{1,20}$/.test(guildId)) {
		throw new ApiError(400, 'invalid_guild', 'guild must be a numeric Discord guild id.');
	}
	return {
		guildId,
		range: parseRange(url.searchParams.get('range'))
	};
}

/** Wrap a handler with auth + JSON error handling. */
export function handler(
	mode: 'read' | 'write',
	fn: (event: RequestEvent) => Promise<Response>
): (event: RequestEvent) => Promise<Response> {
	return async (event) => {
		try {
			authorize(event.request, mode);
			return await fn(event);
		} catch (err) {
			if (err instanceof ApiError) return errorResponse(err);
			throw err;
		}
	};
}

export async function readJson(request: Request): Promise<unknown> {
	if (!request.headers.get('content-type')?.includes('application/json')) {
		throw new ApiError(415, 'unsupported_media_type', 'Send Content-Type: application/json.');
	}
	try {
		return await request.json();
	} catch {
		throw new ApiError(400, 'invalid_json', 'Request body is not valid JSON.');
	}
}
