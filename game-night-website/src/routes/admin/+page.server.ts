import { counts } from '#lib/server/db/admin.ts';
import { DEFAULT_GUILD_ID } from '#lib/server/data/index.ts';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => ({
	counts: await counts(DEFAULT_GUILD_ID),
	guild: DEFAULT_GUILD_ID
});
