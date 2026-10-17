import { redirect } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit/hooks';
import { ADMIN_COOKIE, verifySessionToken } from '#lib/server/admin/auth.ts';

const isAdminPath = (path: string) => path === '/admin' || path.startsWith('/admin/');

export const handle: Handle = async ({ event, resolve }) => {
	const path = event.url.pathname;
	if (!isAdminPath(path)) {
		event.locals.admin = false;
		return resolve(event);
	}

	event.locals.admin = verifySessionToken(event.cookies.get(ADMIN_COOKIE));
	if (!event.locals.admin && path !== '/admin/login') redirect(303, '/admin/login');

	const response = await resolve(event);
	response.headers.set('X-Robots-Tag', 'noindex, nofollow');
	response.headers.set('Cache-Control', 'private, no-store');
	return response;
};
