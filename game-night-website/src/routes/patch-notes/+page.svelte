<script lang="ts">
	import { copy } from '#lib/copy.ts';
	import { formatDay, nightKey, parseSqlTimestamp, relativeDays } from '#lib/dates.ts';
	import Card from '#lib/components/Card.svelte';
	import GameTile from '#lib/components/GameTile.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const gameById = $derived(new Map(data.games.map((g) => [g.id, g])));
	const day = (ts: string) => nightKey(ts, 'UTC');
	const ago = (ts: string) => {
		const days = Math.floor((Date.now() - parseSqlTimestamp(ts).getTime()) / 86_400_000);
		return days <= 0 ? 'today' : relativeDays(days);
	};
</script>

<svelte:head>
	<title>{copy.patchNotes.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader title={copy.patchNotes.title} intro={copy.patchNotes.intro}>
	<form method="GET" class="flex items-center gap-2 text-sm">
		<label for="game-filter" class="text-ink-2">{copy.patchNotes.filter}</label>
		<select
			id="game-filter"
			name="game"
			class="rounded-md border-2 border-outline bg-paper px-2 py-1 font-semibold"
			onchange={(e) => e.currentTarget.form?.requestSubmit()}
		>
			<option value="" selected={data.gameId === null}>{copy.patchNotes.allGames}</option>
			{#each data.games as g (g.id)}
				<option value={g.id} selected={data.gameId === g.id}>{g.name}</option>
			{/each}
		</select>
		<noscript><button class="cutout-sm px-2 py-1">Filter</button></noscript>
	</form>
</PageHeader>

{#if data.notes.length === 0}
	<p class="cutout p-6 text-center text-ink-2">{copy.patchNotes.empty}</p>
{:else}
	<ol class="flex flex-col gap-5">
		{#each data.notes as n (n.id)}
			{@const g = gameById.get(n.game_id)}
			<li>
				<article class="cutout p-4 sm:p-5">
					<header class="flex flex-wrap items-start gap-3">
						{#if g}
							<GameTile
								emoji={g.emoji}
								color={data.colors[g.genre] ?? 'var(--series-other)'}
								name={g.name}
							/>
						{/if}
						<div class="min-w-0 flex-1">
							<div class="text-sm font-semibold text-ink-2">
								{n.game_name}
								{#if g && g.days !== null && g.days >= 30}
									<span class="chip ml-1">idle {g.days} days</span>
								{/if}
							</div>
							<h2 class="display text-lg text-ink sm:text-xl">
								{n.title}{#if n.version}<span
										class="ml-2 align-middle font-sans text-sm font-bold text-ink-2"
										>v{n.version}</span
									>{/if}
							</h2>
						</div>
						<div class="text-right text-xs text-ink-2">
							<time datetime={n.published_at}>{formatDay(day(n.published_at))}</time>
							<div>{ago(n.published_at)}</div>
						</div>
					</header>

					<p class="mt-3 whitespace-pre-line">{n.summary}</p>

					{#if n.highlights.length}
						<ul class="mt-3 flex flex-col gap-1 pl-1">
							{#each n.highlights as h, i (i)}
								<li class="flex gap-2"><span aria-hidden="true">•</span><span>{h}</span></li>
							{/each}
						</ul>
					{/if}

					<footer class="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted">
						<span
							>{n.source === 'grok'
								? 'Posted by Grok'
								: n.source === 'mock-seed'
									? 'Mock entry'
									: n.source}</span
						>
						{#if n.url}
							<a
								href={n.url}
								target="_blank"
								rel="noopener noreferrer nofollow"
								class="font-semibold text-ink underline"
							>
								Official notes ↗
							</a>
						{/if}
					</footer>
				</article>
			</li>
		{/each}
	</ol>
{/if}
