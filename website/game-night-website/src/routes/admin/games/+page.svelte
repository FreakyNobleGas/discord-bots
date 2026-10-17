<script lang="ts">
	import { enhance } from '$app/forms';
	import { copy } from '#lib/copy.ts';
	import { formatDay, nightKey } from '#lib/dates.ts';
	import Card from '#lib/components/Card.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import DeleteForm from '#lib/components/admin/DeleteForm.svelte';
	import FormStatus from '#lib/components/admin/FormStatus.svelte';
	import SubmitButton from '#lib/components/admin/SubmitButton.svelte';
	import GameFields from './GameFields.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<svelte:head>
	<title>{copy.admin.games} · {copy.admin.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader title={copy.admin.games} intro="Rename, retag, add or remove games in the rotation." />
<FormStatus />

<Card title="Add a game" subtitle="For games the bot couldn't find on RAWG." class="mb-6">
	<form method="POST" action="?/create" use:enhance class="flex flex-col gap-3">
		<GameFields />
		<SubmitButton>{copy.admin.add}</SubmitButton>
	</form>
</Card>

<ul class="flex flex-col gap-3">
	{#each data.games as game (game.id)}
		<li class="cutout-sm p-3">
			<div class="flex flex-wrap items-center justify-between gap-2">
				<div>
					<span class="font-bold text-ink">{game.name}</span>
					<span class="text-sm text-ink-2">
						· {game.sessions} sessions · added by {game.added_by}
						{formatDay(nightKey(game.added_at, 'UTC'))}
					</span>
				</div>
				<DeleteForm id={game.id} label={game.name} note={copy.admin.gameDeleteNote} />
			</div>
			<details class="mt-2">
				<summary class="cursor-pointer text-sm font-semibold text-ink-2">{copy.admin.edit}</summary>
				<form method="POST" action="?/update" use:enhance class="mt-3 flex flex-col gap-3">
					<input type="hidden" name="id" value={game.id} />
					<GameFields {game} />
					<SubmitButton>{copy.admin.save}</SubmitButton>
				</form>
			</details>
		</li>
	{/each}
</ul>
