import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { FEED_PATH } from '$app/env/private';
import type { Feed, PatchNote, Suggestion } from '#lib/types.ts';
import { seedFeed } from './seed';
import type { FeedStore } from './store';

type FeedFile = { version: 1; guilds: Record<string, Feed> };

const path = resolve(FEED_PATH || 'data/feed.json');

async function load(): Promise<FeedFile> {
	try {
		return JSON.parse(await readFile(path, 'utf8')) as FeedFile;
	} catch (err) {
		if ((err as NodeJS.ErrnoException).code !== 'ENOENT') throw err;
		const seeded = await seedFeed();
		await save(seeded);
		return seeded;
	}
}

async function save(file: FeedFile) {
	await mkdir(dirname(path), { recursive: true });
	const tmp = `${path}.${process.pid}.tmp`;
	await writeFile(tmp, JSON.stringify(file, null, '\t'));
	await rename(tmp, path);
}

// Serialize writes so concurrent POSTs can't clobber each other within this process.
let queue: Promise<unknown> = Promise.resolve();
function mutate(fn: (file: FeedFile) => void): Promise<void> {
	const next = queue.then(async () => {
		const file = await load();
		fn(file);
		await save(file);
	});
	queue = next.catch(() => {});
	return next;
}

const empty = (): Feed => ({ patch_notes: [], suggestions: [] });

export const fileFeedStore: FeedStore = {
	async read(guildId) {
		await queue;
		return (await load()).guilds[guildId] ?? empty();
	},
	addPatchNote(note: PatchNote) {
		return mutate((file) => {
			(file.guilds[note.guild_id] ??= empty()).patch_notes.push(note);
		});
	},
	addSuggestion(suggestion: Suggestion) {
		return mutate((file) => {
			(file.guilds[suggestion.guild_id] ??= empty()).suggestions.push(suggestion);
		});
	}
};
