<script lang="ts">
	import { copy } from '#lib/copy.ts';
	import { relativeDays } from '#lib/dates.ts';
	import { colorFor, genreColorMap, pct, plural } from '#lib/view.ts';
	import BarList from '#lib/components/BarList.svelte';
	import Card from '#lib/components/Card.svelte';
	import GameTile from '#lib/components/GameTile.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import RangeFilter from '#lib/components/RangeFilter.svelte';
	import StackedArea from '#lib/components/StackedArea.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const a = $derived(data.analysis);
	const colors = $derived(genreColorMap(a.genre_share));

	let mode = $state<'count' | 'share'>('count');
	// Seeded from ?genre= so a selection can be linked; then local to the page
	let picked = $state<string | null | undefined>(undefined);
	const selected = $derived(
		picked === undefined ? (data.genre ?? a.genre_share[0]?.genre ?? null) : picked
	);

	const shareRows = $derived(
		a.genre_share.map((g) => ({
			key: g.genre,
			label: g.genre,
			value: g.sessions,
			display: pct(g.share),
			detail: `${plural(g.sessions, 'session')} · ${plural(g.games, 'game')}`,
			color: g.color
		}))
	);
	const reachRows = $derived(
		a.tag_reach.map((t) => ({
			key: t.tag,
			label: t.tag,
			value: t.reach,
			display: pct(t.reach),
			detail: plural(t.sessions, 'session')
		}))
	);
	const genreGames = $derived(a.games.filter((g) => g.primary_genre === selected));
</script>

<svelte:head>
	<title>{copy.genres.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader title={copy.genres.title} intro={copy.genres.intro}>
	<RangeFilter range={a.range} />
</PageHeader>

{#if a.kpis.sessions === 0}
	<p class="cutout p-6 text-center text-ink-2">{copy.empty.sessions}</p>
{:else}
	<div class="grid grid-cols-1 gap-6 lg:grid-cols-[3fr_2fr]">
		<Card title={copy.genres.share} subtitle={copy.genres.shareNote}>
			<BarList
				rows={shareRows}
				label={copy.genres.share}
				{selected}
				onselect={(key) => (picked = key)}
			/>
			<p class="mt-3 text-xs text-muted">{copy.genres.pick}</p>
		</Card>

		<Card
			title={selected ?? 'Games'}
			subtitle={selected ? `${plural(genreGames.length, 'game')} in the rotation` : undefined}
		>
			<ul class="flex flex-col divide-y divide-grid">
				{#each genreGames as g (g.game.id)}
					<li class="flex items-center gap-3 py-2">
						<GameTile emoji={g.emoji} color={colorFor(colors, g)} name={g.game.name} size="sm" />
						<div class="min-w-0 flex-1">
							<div class="truncate font-semibold">{g.game.name}</div>
							<div class="text-xs text-ink-2">
								{plural(g.session_count, 'session')} · last {relativeDays(g.days_since_played)}
							</div>
						</div>
						<span class="tnum text-sm font-semibold">{pct(g.share)}</span>
					</li>
				{:else}
					<li class="py-2 text-ink-2">{copy.genres.pick}</li>
				{/each}
			</ul>
		</Card>
	</div>

	<div class="mt-6">
		<Card title={copy.genres.mix} subtitle="Sessions per month, by main genre">
			{#snippet actions()}
				<div
					class="flex rounded-full border-2 border-outline p-0.5 text-sm"
					role="group"
					aria-label="Scale"
				>
					{#each [['count', 'Sessions'], ['share', '100%']] as [m, text] (m)}
						<button
							type="button"
							aria-pressed={mode === m}
							class={[
								'rounded-full px-3 py-0.5 font-semibold',
								mode === m ? 'bg-ink text-paper' : 'text-ink'
							]}
							onclick={() => (mode = m as 'count' | 'share')}
						>
							{text}
						</button>
					{/each}
				</div>
			{/snippet}
			<StackedArea
				months={a.months}
				series={a.month_series}
				{mode}
				label="{copy.genres.mix}, {mode === 'share' ? 'percent' : 'session counts'} per month"
			/>
		</Card>
	</div>

	<div class="mt-6">
		<Card title={copy.genres.reach} subtitle={copy.genres.reachNote}>
			<BarList rows={reachRows} max={1} label={copy.genres.reach} />
		</Card>
	</div>
{/if}
