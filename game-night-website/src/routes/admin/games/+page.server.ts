import { adminAction, found } from '#lib/server/admin/actions.ts';
import { gameForm, idForm, parseForm } from '#lib/server/admin/forms.ts';
import { createGame, deleteGame, listGames, updateGame } from '#lib/server/db/admin.ts';
import { DEFAULT_GUILD_ID } from '#lib/server/data/index.ts';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async () => ({ games: await listGames(DEFAULT_GUILD_ID) });

export const actions: Actions = {
	create: adminAction(async ({ form, guild }) => {
		const f = parseForm(gameForm, form);
		await createGame(guild, f);
		return `Added ${f.name}.`;
	}),
	update: adminAction(async ({ form, guild }) => {
		const { id } = parseForm(idForm, form);
		const f = parseForm(gameForm, form);
		found(await updateGame(guild, id, f), 'Game');
		return `Saved ${f.name}.`;
	}),
	delete: adminAction(async ({ form, guild }) => {
		const { id } = parseForm(idForm, form);
		found(await deleteGame(guild, id), 'Game');
		return 'Game deleted.';
	})
};
