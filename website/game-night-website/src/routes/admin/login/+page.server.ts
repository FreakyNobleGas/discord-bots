import { fail, redirect } from '@sveltejs/kit';
import { copy } from '#lib/copy.ts';
import {
	ADMIN_COOKIE,
	adminConfigured,
	cookieOptions,
	createSessionToken,
	passwordMatches
} from '#lib/server/admin/auth.ts';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = ({ locals }) => {
	if (locals.admin) redirect(303, '/admin');
	return { configured: adminConfigured() };
};

export const actions: Actions = {
	default: async ({ request, cookies }) => {
		if (!adminConfigured()) return fail(503, { error: copy.admin.disabled });
		const password = String((await request.formData()).get('password') ?? '');
		if (!passwordMatches(password)) {
			// Slow down guessing. Use a long random ADMIN_PASSWORD; this is the only lock.
			await new Promise((r) => setTimeout(r, 1000));
			return fail(401, { error: copy.admin.wrongPassword });
		}
		cookies.set(ADMIN_COOKIE, createSessionToken(), cookieOptions);
		redirect(303, '/admin');
	}
};
