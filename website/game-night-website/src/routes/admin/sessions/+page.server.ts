import { adminAction, found } from '#lib/server/admin/actions.ts';
import { idForm, parseForm, sessionForm } from '#lib/server/admin/forms.ts';
import {
	SESSIONS_PER_PAGE,
	createSession,
	deleteSession,
	listGames,
	listSessions,
	updateSession
} from '#lib/server/db/admin.ts';
import { DEFAULT_GUILD_ID, TIMEZONE } from '#lib/server/data/index.ts';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ url }) => {
	const gameId = Number(url.searchParams.get('game')) || null;
	const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const [games, sessions] = await Promise.all([
		listGames(DEFAULT_GUILD_ID),
		listSessions(DEFAULT_GUILD_ID, TIMEZONE, { gameId, page })
	]);
	return {
		games: games.map((g) => ({ id: g.id, name: g.name })),
		sessions: sessions.rows,
		total: sessions.total,
		page,
		pages: Math.max(1, Math.ceil(sessions.total / SESSIONS_PER_PAGE)),
		gameId,
		tz: TIMEZONE
	};
};

export const actions: Actions = {
	create: adminAction(async ({ form, guild, tz }) => {
		const f = parseForm(sessionForm, form);
		found(await createSession(guild, tz, f), 'Game');
		return 'Session logged.';
	}),
	update: adminAction(async ({ form, guild, tz }) => {
		const { id } = parseForm(idForm, form);
		found(await updateSession(guild, tz, id, parseForm(sessionForm, form)), 'Session');
		return 'Session saved.';
	}),
	delete: adminAction(async ({ form, guild }) => {
		const { id } = parseForm(idForm, form);
		found(await deleteSession(guild, id), 'Session');
		return 'Session deleted.';
	})
};
