import { adminAction, found } from '#lib/server/admin/actions.ts';
import { parseForm, suggestionForm, uuidForm } from '#lib/server/admin/forms.ts';
import { deleteSuggestion, listSuggestions, updateSuggestion } from '#lib/server/db/admin.ts';
import { DEFAULT_GUILD_ID } from '#lib/server/data/index.ts';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async () => ({
	suggestions: await listSuggestions(DEFAULT_GUILD_ID)
});

export const actions: Actions = {
	update: adminAction(async ({ form, guild }) => {
		const { id } = parseForm(uuidForm, form);
		const f = parseForm(suggestionForm, form);
		found(await updateSuggestion(guild, id, f), 'Suggestion');
		return `Saved ${f.name}.`;
	}),
	delete: adminAction(async ({ form, guild }) => {
		const { id } = parseForm(uuidForm, form);
		found(await deleteSuggestion(guild, id), 'Suggestion');
		return 'Suggestion deleted.';
	})
};
