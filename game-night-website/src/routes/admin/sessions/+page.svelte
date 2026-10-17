<script lang="ts">
	import { enhance } from '$app/forms';
	import { copy } from '#lib/copy.ts';
	import Card from '#lib/components/Card.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import DeleteForm from '#lib/components/admin/DeleteForm.svelte';
	import FormStatus from '#lib/components/admin/FormStatus.svelte';
	import SubmitButton from '#lib/components/admin/SubmitButton.svelte';
	import SessionFields from './SessionFields.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const pageHref = (page: number) => {
		const params = new URLSearchParams();
		if (data.gameId) params.set('game', String(data.gameId));
		if (page > 1) params.set('page', String(page));
		const qs = params.toString();
		return qs ? `?${qs}` : '?';
	};
	const shown = (played: string) => played.replace('T', ' ');
</script>

<svelte:head>
	<title>{copy.admin.sessions} · {copy.admin.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader
	title={copy.admin.sessions}
	intro="Fix a mislogged session, or add one somebody forgot."
>
	<form method="GET" class="flex items-center gap-2 text-sm">
		<label for="session-game" class="text-ink-2">Game</label>
		<select
			id="session-game"
			name="game"
			class="rounded-md border-2 border-outline bg-paper px-2 py-1 font-semibold"
			onchange={(e) => e.currentTarget.form?.requestSubmit()}
		>
			<option value="">All games</option>
			{#each data.games as game (game.id)}
				<option value={game.id} selected={game.id === data.gameId}>{game.name}</option>
			{/each}
		</select>
		<noscript><button class="underline">Filter</button></noscript>
	</form>
</PageHeader>
<FormStatus />

<Card title="Log a session" subtitle="Backdate it to the night you played." class="mb-6">
	<form method="POST" action="?/create" use:enhance class="flex flex-col gap-3">
		<SessionFields games={data.games} tz={data.tz} />
		<SubmitButton>{copy.admin.add}</SubmitButton>
	</form>
</Card>

<p class="mb-3 text-sm text-ink-2">
	{data.total} sessions{#if data.pages > 1}, page {data.page} of {data.pages}{/if}. Times in {data.tz}.
</p>

<ul class="flex flex-col gap-3">
	{#each data.sessions as session (session.id)}
		<li class="cutout-sm p-3">
			<div class="flex flex-wrap items-center justify-between gap-2">
				<div>
					<span class="font-bold text-ink">{session.game_name}</span>
					<span class="tnum text-sm text-ink-2">
						· {[shown(session.played_on), session.logged_by].filter(Boolean).join(' · ')}
					</span>
					{#if session.notes}<p class="text-sm text-ink-2">“{session.notes}”</p>{/if}
				</div>
				<DeleteForm id={session.id} label="{session.game_name} on {shown(session.played_on)}" />
			</div>
			<details class="mt-2">
				<summary class="cursor-pointer text-sm font-semibold text-ink-2">{copy.admin.edit}</summary>
				<form method="POST" action="?/update" use:enhance class="mt-3 flex flex-col gap-3">
					<input type="hidden" name="id" value={session.id} />
					<SessionFields games={data.games} {session} tz={data.tz} />
					<SubmitButton>{copy.admin.save}</SubmitButton>
				</form>
			</details>
		</li>
	{/each}
</ul>

{#if data.pages > 1}
	<nav aria-label="Pages" class="mt-6 flex justify-between text-sm font-semibold">
		{#if data.page > 1}<a href={pageHref(data.page - 1)}>← Newer</a>{:else}<span></span>{/if}
		{#if data.page < data.pages}<a href={pageHref(data.page + 1)}>Older →</a>{/if}
	</nav>
{/if}
