import type { Feed, PatchNote, Suggestion } from '#lib/types.ts';
import { dbEnabled } from '../db/pool';
import { fileFeedStore } from './file';
import { postgresFeedStore } from './postgres';

/** Where Grok's posts live: the shared Postgres in production, a local JSON file in mock mode. */
export interface FeedStore {
	read(guildId: string): Promise<Feed>;
	addPatchNote(note: PatchNote): Promise<void>;
	addSuggestion(suggestion: Suggestion): Promise<void>;
}

export function getFeedStore(): FeedStore {
	return dbEnabled() ? postgresFeedStore : fileFeedStore;
}
