// Password login for /admin. One shared password (ADMIN_PASSWORD); a signed, expiring
// cookie proves the login. Changing the password or secret signs everyone out.

import { createHash, createHmac, timingSafeEqual } from 'node:crypto';
import { error } from '@sveltejs/kit';
import { ADMIN_PASSWORD, ADMIN_SESSION_SECRET } from '$app/env/private';
import { dbEnabled } from '../db/pool';

export const ADMIN_COOKIE = 'admin_session';
const MAX_AGE = 7 * 24 * 60 * 60;

export const cookieOptions = {
	path: '/admin',
	httpOnly: true,
	secure: true,
	sameSite: 'strict',
	maxAge: MAX_AGE
} as const;

/** Admin needs a password, a signing secret, and a real database to edit. */
export const adminConfigured = () => Boolean(ADMIN_PASSWORD && ADMIN_SESSION_SECRET && dbEnabled());

const sha256 = (s: string) => createHash('sha256').update(s).digest();

/** Hashing both sides first gives equal-length buffers for the constant-time compare. */
export function passwordMatches(input: string) {
	return adminConfigured() && timingSafeEqual(sha256(input), sha256(ADMIN_PASSWORD!));
}

function sign(payload: string) {
	return createHmac('sha256', `${ADMIN_SESSION_SECRET}:${sha256(ADMIN_PASSWORD!).toString('hex')}`)
		.update(payload)
		.digest('base64url');
}

export function createSessionToken() {
	const payload = `v1.${Math.floor(Date.now() / 1000) + MAX_AGE}`;
	return `${payload}.${sign(payload)}`;
}

export function verifySessionToken(token: string | undefined) {
	if (!token || !adminConfigured()) return false;
	const cut = token.lastIndexOf('.');
	const payload = token.slice(0, cut);
	const given = Buffer.from(token.slice(cut + 1));
	const expected = Buffer.from(sign(payload));
	if (cut < 0 || given.length !== expected.length || !timingSafeEqual(given, expected))
		return false;
	const [version, exp] = payload.split('.');
	return version === 'v1' && Number(exp) * 1000 > Date.now();
}

/** Defense in depth: every admin action checks this, on top of the hook's redirect. */
export function requireAdmin(locals: App.Locals) {
	if (!locals.admin) error(401, 'Not signed in');
}
