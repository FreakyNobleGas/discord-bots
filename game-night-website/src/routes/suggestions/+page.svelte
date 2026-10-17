<script lang="ts">
	import { copy } from '#lib/copy.ts';
	import { formatDay, nightKey } from '#lib/dates.ts';
	import { pct } from '#lib/view.ts';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let sort = $state<'newest' | 'fit'>('newest');
	const list = $derived(
		sort === 'fit' ? [...data.suggestions].sort((a, b) => b.fit - a.fit) : data.suggestions
	);
	const fitWord = (f: number) => (f >= 0.7 ? 'Strong fit' : f >= 0.4 ? 'Decent fit' : 'Wildcard');
</script>

<svelte:head>
	<title>{copy.suggestions.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader title={copy.suggestions.title} intro={copy.suggestions.intro}>
	<div
		class="flex rounded-full border-2 border-outline bg-paper p-0.5 text-sm"
		role="group"
		aria-label="Sort"
	>
		{#each [['newest', copy.suggestions.sortNewest], ['fit', copy.suggestions.sortFit]] as [key, label] (key)}
			<button
				type="button"
				aria-pressed={sort === key}
				class={[
					'rounded-full px-3 py-0.5 font-semibold',
					sort === key ? 'bg-ink text-paper' : 'text-ink'
				]}
				onclick={() => (sort = key as 'newest' | 'fit')}
			>
				{label}
			</button>
		{/each}
	</div>
</PageHeader>

{#if list.length === 0}
	<p class="cutout p-6 text-center text-ink-2">{copy.suggestions.empty}</p>
{:else}
	<ul class="grid grid-cols-1 gap-6 md:grid-cols-2">
		{#each list as s, i (s.id)}
			<li
				class="cutout flex flex-col p-4 sm:p-5"
				style:transform="rotate({[-0.5, 0.4, 0.2, -0.3][i % 4]}deg)"
			>
				<div class="flex items-start justify-between gap-3">
					<h2 class="display text-2xl text-ink">{s.name}</h2>
					<span class="text-xs whitespace-nowrap text-muted"
						>{formatDay(nightKey(s.suggested_at, 'UTC'))}</span
					>
				</div>

				<div class="mt-2 flex flex-wrap gap-1">
					{#each s.genres as g (g)}
						<span class={['chip', data.topTags.includes(g) && 'font-semibold text-ink']}>{g}</span>
					{/each}
				</div>

				<div class="mt-4">
					<div class="flex items-baseline justify-between text-sm">
						<span class="text-ink-2" title={copy.suggestions.fitNote}>{copy.suggestions.fit}</span>
						<span
							><strong>{fitWord(s.fit)}</strong>
							<span class="tnum text-ink-2">{pct(s.fit)}</span></span
						>
					</div>
					<div
						class="mt-1 h-2.5 overflow-hidden rounded-full"
						style:background="color-mix(in oklab, var(--series-1) 18%, var(--paper))"
						role="meter"
						aria-label={copy.suggestions.fit}
						aria-valuemin={0}
						aria-valuemax={100}
						aria-valuenow={Math.round(s.fit * 100)}
					>
						<div
							class="h-full rounded-full"
							style:width={pct(s.fit)}
							style:background="var(--series-1)"
						></div>
					</div>
				</div>

				<p class="mt-4 flex-1">{s.reason}</p>

				{#if s.similar.length}
					<div class="mt-4 flex flex-wrap items-center gap-1.5 text-sm">
						<span class="text-ink-2">{copy.suggestions.similar}</span>
						{#each s.similar as sim (sim.name)}
							{#if sim.id}
								<a href="/games" class="chip no-underline hover:underline"
									><span aria-hidden="true">{sim.emoji}</span>{sim.name}</a
								>
							{:else}
								<span class="chip">{sim.name}</span>
							{/if}
						{/each}
					</div>
				{/if}

				<footer
					class="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-grid pt-3 text-xs text-muted"
				>
					{#if s.platforms.length}<span>{s.platforms.join(' · ')}</span>{/if}
					{#if s.release_date}<span>Released {formatDay(s.release_date)}</span>{/if}
					<span
						>{s.source === 'grok'
							? 'Suggested by Grok'
							: s.source === 'mock-seed'
								? 'Mock entry'
								: s.source}</span
					>
					{#if s.url}
						<a
							href={s.url}
							target="_blank"
							rel="noopener noreferrer nofollow"
							class="font-semibold text-ink underline">More ↗</a
						>
					{/if}
				</footer>
			</li>
		{/each}
	</ul>
{/if}
