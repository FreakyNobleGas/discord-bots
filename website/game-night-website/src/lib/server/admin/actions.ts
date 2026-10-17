import { fail, type RequestEvent } from '@sveltejs/kit';
import { DEFAULT_GUILD_ID, TIMEZONE } from '../data';
import { requireAdmin } from './auth';
import { FormError } from './forms';

type Ctx = { form: FormData; guild: string; tz: string };

/**
 * Wraps an admin form action: checks the session, hands over the form data, and turns
 * expected failures into `fail()` so the page can show them. Returns `{ ok: message }`.
 */
export function adminAction(fn: (ctx: Ctx) => Promise<string>) {
	return async ({ locals, request }: RequestEvent) => {
		requireAdmin(locals);
		try {
			const ok = await fn({
				form: await request.formData(),
				guild: DEFAULT_GUILD_ID,
				tz: TIMEZONE
			});
			return { ok };
		} catch (err) {
			if (err instanceof FormError) return fail(err.status, { error: err.message });
			if ((err as { code?: string }).code === '23505') {
				return fail(409, { error: 'That game is already in the rotation (same RAWG id).' });
			}
			throw err;
		}
	};
}

/** For update/delete helpers that return false when the row isn't in this guild. */
export function found(ok: boolean, what: string) {
	if (!ok) throw new FormError(404, `${what} not found. It may have just been deleted.`);
}
