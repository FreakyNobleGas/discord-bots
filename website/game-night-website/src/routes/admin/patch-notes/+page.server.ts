import { adminAction, found } from '#lib/server/admin/actions.ts';
import { parseForm, patchNoteForm, uuidForm } from '#lib/server/admin/forms.ts';
import { deletePatchNote, listPatchNotes, updatePatchNote } from '#lib/server/db/admin.ts';
import { DEFAULT_GUILD_ID, TIMEZONE } from '#lib/server/data/index.ts';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async () => ({
	notes: await listPatchNotes(DEFAULT_GUILD_ID, TIMEZONE),
	tz: TIMEZONE
});

export const actions: Actions = {
	update: adminAction(async ({ form, guild, tz }) => {
		const { id } = parseForm(uuidForm, form);
		found(await updatePatchNote(guild, tz, id, parseForm(patchNoteForm, form)), 'Patch note');
		return 'Patch note saved.';
	}),
	delete: adminAction(async ({ form, guild }) => {
		const { id } = parseForm(uuidForm, form);
		found(await deletePatchNote(guild, id), 'Patch note');
		return 'Patch note deleted.';
	})
};
