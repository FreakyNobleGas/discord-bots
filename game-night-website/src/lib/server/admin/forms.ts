// Admin form parsing. Same length caps as the Grok API (feed/schema.ts), adapted to
// FormData: empty inputs become null, lists are comma- or newline-separated text.

import { z } from 'zod';
import { httpUrlValue, optionalText, text } from '../feed/schema';

const id = z.coerce.number().int().positive();
const optionalInt = z
	.string()
	.trim()
	.transform((v) => (v === '' ? null : Number(v)))
	.pipe(z.number().int().positive().nullable());
const slug = z
	.string()
	.trim()
	.regex(/^[a-z0-9-]*$/, 'must be a RAWG slug (lowercase letters, digits, dashes)')
	.transform((v) => v || null);
const blankUrl = z
	.string()
	.trim()
	.transform((v) => v || null)
	.pipe(httpUrlValue.nullable());
const splitList = (sep: RegExp, itemMax: number, max: number) =>
	z
		.string()
		.transform((v) =>
			v
				.split(sep)
				.map((s) => s.trim())
				.filter(Boolean)
		)
		.pipe(z.array(z.string().max(itemMax)).max(max));
const commaList = (itemMax: number, max: number) => splitList(/,/, itemMax, max);
const lineList = (itemMax: number, max: number) => splitList(/\r?\n/, itemMax, max);
/** `<input type="datetime-local">` value, read as wall time in GAME_NIGHT_TZ. */
const localDateTime = z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'pick a date and time');
const isoDate = z
	.string()
	.trim()
	.transform((v) => v || null)
	.pipe(z.iso.date().nullable());

export const idForm = z.object({ id });
export const uuidForm = z.object({ id: z.uuid() });

export const gameForm = z.object({
	name: text(200),
	rawg_id: optionalInt,
	rawg_slug: slug,
	cover_url: blankUrl.transform((v) => v ?? ''),
	genre_tags: commaList(50, 10),
	added_by: text(100)
});

export const sessionForm = z.object({
	game_id: id,
	played_on: localDateTime,
	logged_by: optionalText(100),
	notes: optionalText(1000)
});

export const patchNoteForm = z.object({
	title: text(200),
	version: optionalText(50),
	summary: text(2000),
	highlights: lineList(300, 15),
	url: blankUrl,
	published_at: localDateTime
});

export const suggestionForm = z.object({
	name: text(200),
	rawg_slug: slug,
	genres: commaList(50, 10).refine((g) => g.length > 0, 'add at least one genre'),
	reason: text(1000),
	similar_to: commaList(200, 10),
	platforms: commaList(50, 15),
	release_date: isoDate,
	url: blankUrl
});

export type GameForm = z.infer<typeof gameForm>;
export type SessionForm = z.infer<typeof sessionForm>;
export type PatchNoteForm = z.infer<typeof patchNoteForm>;
export type SuggestionForm = z.infer<typeof suggestionForm>;

export class FormError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
	}
}

/** Parse a form post, or throw a FormError naming the first bad field. */
export function parseForm<T extends z.ZodType>(schema: T, data: FormData): z.infer<T> {
	const result = schema.safeParse(Object.fromEntries(data));
	if (result.success) return result.data;
	const issue = result.error.issues[0];
	throw new FormError(400, `${issue.path.join('.') || 'form'}: ${issue.message}`);
}
