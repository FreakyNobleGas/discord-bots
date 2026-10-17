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
	<title>{copy.admin.suggestions} · {copy.admin.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader
	title={copy.admin.suggestions}
	intro="Edit or toss Grok's game picks. New picks come in through the API."
/>
<FormStatus />

{#if data.suggestions.length === 0}
	<p class="cutout p-5 text-ink-2">{copy.suggestions.empty}</p>
{/if}

<ul class="flex flex-col gap-3">
	{#each data.suggestions as s (s.id)}
		<li class="cutout-sm p-3">
			<div class="flex flex-wrap items-center justify-between gap-2">
				<div>
					<span class="font-bold text-ink">{s.name}</span>
					<span class="text-sm text-ink-2">· {s.genres.join(', ')} · {s.source}</span>
				</div>
				<DeleteForm id={s.id} label={s.name} />
			</div>
			<details class="mt-2">
				<summary class="cursor-pointer text-sm font-semibold text-ink-2">{copy.admin.edit}</summary>
				<form method="POST" action="?/update" use:enhance class="mt-3 flex flex-col gap-3">
					<input type="hidden" name="id" value={s.id} />
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
						<Field label="Name" name="name" value={s.name} required maxlength={200} />
						<Field label="RAWG slug" name="rawg_slug" value={s.rawg_slug} />
						<Field
							label="Genres"
							name="genres"
							value={s.genres.join(', ')}
							required
							hint="RAWG genre names, comma-separated"
						/>
						<Field label="Platforms" name="platforms" value={s.platforms.join(', ')} />
						<Field
							label="Why Grok picked it"
							name="reason"
							value={s.reason}
							rows={3}
							required
							maxlength={1000}
							class="sm:col-span-2"
						/>
						<Field
							label="Similar to"
							name="similar_to"
							value={s.similar_to.join(', ')}
							hint="Rotation game names, comma-separated"
						/>
						<Field label="Release date" name="release_date" type="date" value={s.release_date} />
						<Field label="Link" name="url" type="url" value={s.url} class="sm:col-span-2" />
					</div>
					<SubmitButton>{copy.admin.save}</SubmitButton>
				</form>
			</details>
		</li>
	{/each}
</ul>
