<script lang="ts">
	import { enhance } from '$app/forms';
	import { copy } from '#lib/copy.ts';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import DeleteForm from '#lib/components/admin/DeleteForm.svelte';
	import Field from '#lib/components/admin/Field.svelte';
	import FormStatus from '#lib/components/admin/FormStatus.svelte';
	import SubmitButton from '#lib/components/admin/SubmitButton.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<svelte:head>
	<title>{copy.admin.patchNotes} · {copy.admin.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader
	title={copy.admin.patchNotes}
	intro="Clean up what Grok posted. New patch notes come in through the API."
/>
<FormStatus />

{#if data.notes.length === 0}
	<p class="cutout p-5 text-ink-2">{copy.patchNotes.empty}</p>
{/if}

<ul class="flex flex-col gap-3">
	{#each data.notes as note (note.id)}
		<li class="cutout-sm p-3">
			<div class="flex flex-wrap items-center justify-between gap-2">
				<div>
					<span class="font-bold text-ink">{note.game_name}</span>
					<span class="text-sm text-ink-2">
						· {note.version ?? note.title} · {note.published_at.slice(0, 10)} · {note.source}
					</span>
				</div>
				<DeleteForm id={note.id} label="{note.game_name} {note.version ?? note.title}" />
			</div>
			<details class="mt-2">
				<summary class="cursor-pointer text-sm font-semibold text-ink-2">{copy.admin.edit}</summary>
				<form method="POST" action="?/update" use:enhance class="mt-3 flex flex-col gap-3">
					<input type="hidden" name="id" value={note.id} />
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
						<Field label="Title" name="title" value={note.title} required maxlength={200} />
						<Field label="Version" name="version" value={note.version} maxlength={50} />
						<Field
							label="Summary"
							name="summary"
							value={note.summary}
							rows={3}
							required
							maxlength={2000}
							class="sm:col-span-2"
						/>
						<Field
							label="Highlights"
							name="highlights"
							value={note.highlights.join('\n')}
							rows={4}
							hint="One per line"
							class="sm:col-span-2"
						/>
						<Field label="Link" name="url" type="url" value={note.url} />
						<Field
							label="Published"
							name="published_at"
							type="datetime-local"
							value={note.published_at}
							required
							hint="Local time in {data.tz}"
						/>
					</div>
					<SubmitButton>{copy.admin.save}</SubmitButton>
				</form>
			</details>
		</li>
	{/each}
</ul>
