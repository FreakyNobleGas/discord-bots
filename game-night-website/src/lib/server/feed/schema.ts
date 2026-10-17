import { z } from 'zod';

export const text = (max: number) => z.string().trim().min(1).max(max);
export const optionalText = (max: number) =>
	z
		.string()
		.trim()
		.max(max)
		.nullish()
		.transform((v) => v || null);
export const httpUrlValue = z
	.url({ protocol: /^https?$/, error: 'must be an http(s) URL' })
	.max(500);
const httpUrl = httpUrlValue.nullish().transform((v) => v ?? null);
const list = (itemMax: number, max: number) => z.array(text(itemMax)).max(max).default([]);

export const patchNoteInput = z.object({
	game: z
		.object({
			rawg_slug: z.string().trim().max(200).optional(),
			game_id: z.number().int().positive().optional(),
			name: z.string().trim().max(200).optional()
		})
		.refine((g) => g.rawg_slug || g.game_id || g.name, {
			error: 'game needs at least one of rawg_slug, game_id, or name'
		}),
	title: text(200),
	version: optionalText(50),
	summary: text(2000),
	highlights: list(300, 15),
	url: httpUrl,
	published_at: z.union([z.iso.datetime({ offset: true }), z.iso.date()]).optional()
});

export const suggestionInput = z.object({
	name: text(200),
	rawg_slug: z
		.string()
		.trim()
		.max(200)
		.regex(/^[a-z0-9-]+$/, 'must be a RAWG slug (lowercase letters, digits, dashes)')
		.nullish()
		.transform((v) => v ?? null),
	rawg_id: z
		.number()
		.int()
		.positive()
		.nullish()
		.transform((v) => v ?? null),
	genres: z.array(text(50)).min(1).max(10),
	reason: text(1000),
	similar_to: list(200, 10),
	platforms: list(50, 15),
	release_date: z.iso
		.date()
		.nullish()
		.transform((v) => v ?? null),
	url: httpUrl
});

export type PatchNoteInput = z.infer<typeof patchNoteInput>;
export type SuggestionInput = z.infer<typeof suggestionInput>;
