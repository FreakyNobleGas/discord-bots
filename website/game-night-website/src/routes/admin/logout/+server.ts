import { redirect } from '@sveltejs/kit';
import { ADMIN_COOKIE, cookieOptions } from '#lib/server/admin/auth.ts';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = ({ cookies }) => {
	cookies.delete(ADMIN_COOKIE, { path: cookieOptions.path });
	redirect(303, '/admin/login');
};
