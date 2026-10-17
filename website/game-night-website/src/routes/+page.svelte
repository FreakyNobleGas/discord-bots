<script lang="ts">
	import { copy } from '#lib/copy.ts';
	import { relativeDays } from '#lib/dates.ts';
	import { colorFor, foldShares, genreColorMap, pct, plural } from '#lib/view.ts';
	import BarList from '#lib/components/BarList.svelte';
	import Card from '#lib/components/Card.svelte';
	import GameTile from '#lib/components/GameTile.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import RangeFilter from '#lib/components/RangeFilter.svelte';
	import ShareStackBar from '#lib/components/ShareStackBar.svelte';
	import StatTile from '#lib/components/StatTile.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const a = $derived(data.analysis);
	const colors = $derived(genreColorMap(a.genre_share));
	const segments = $derived(
		foldShares(a.genre_share).map((s) => ({
			key: s.genre,
			label: s.genre,
			value: s.sessions,
			share: s.share,
			color: s.color
		}))
	);
	const top = $derived(
		a.games
			.filter((g) => g.session_count > 0)
			.slice(0, 5)
			.map((g) => ({
				key: String(g.game.id),
				label: g.game.name,
				emoji: g.emoji,
				value: g.session_count,
				display: String(g.session_count),
				detail: `${plural(g.session_count, 'session')} · ${pct(g.share)}`,
				color: colorFor(colors, g)
			}))
	);
	const dust = $derived(a.collecting_dust.slice(0, 5));
	const dustedOffPatch = $derived(a.collecting_dust.find((g) => g.has_recent_patch));
</script>

<svelte:head>
	<title>{copy.site.name}</title>
</svelte:head>

<PageHeader title={copy.overview.title} intro={copy.overview.intro}>
	<RangeFilter range={a.range} />
</PageHeader>

<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
	<StatTile label={copy.kpis.sessions} value={a.kpis.sessions.toLocaleString()} tilt={-0.8} />
	<StatTile label={copy.kpis.nights} value={a.kpis.game_nights.toLocaleString()} tilt={0.6} />
	<StatTile label={copy.kpis.rotation} value={String(a.kpis.games_in_rotation)} tilt={-0.4} />
	<StatTile
		label={copy.kpis.streak}
		value={plural(a.kpis.weekly_streak, 'week')}
		note={a.kpis.weekly_streak >= 4 ? 'Mom says it’s a problem.' : undefined}
		tilt={0.9}
	/>
</div>

{#if a.kpis.sessions === 0}
	<p class="cutout mt-6 p-6 text-center text-ink-2">{copy.empty.sessions}</p>
{:else}
	<div class="mt-6">
		<Card
			title={copy.overview.genreMix}
			subtitle={a.kpis.top_genre
				? `${a.kpis.top_genre} runs the basement — ${pct(a.genre_share[0].share)} of sessions.`
				: undefined}
		>
			<ShareStackBar {segments} />
			<a
				href="/genres{a.range === 'all' ? '' : `?range=${a.range}`}"
				class="mt-4 inline-block text-sm font-semibold underline"
			>
				Genre breakdown →
			</a>
		</Card>
	</div>

	<div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
		<Card
			title={copy.overview.topGames}
			subtitle="Sessions in this range · bars colored by main genre"
		>
			<BarList rows={top} label={copy.overview.topGames} />
			<a
				href="/games{a.range === 'all' ? '' : `?range=${a.range}`}"
				class="mt-4 inline-block text-sm font-semibold underline"
			>
				Full leaderboard →
			</a>
		</Card>

		<Card title={copy.overview.dust} subtitle={copy.overview.dustIntro}>
			{#if dustedOffPatch}
				<p class="mb-3 rounded-lg bg-accent-soft px-3 py-2 text-sm">
					<span aria-hidden="true">📜</span>
					<strong>{dustedOffPatch.game.name}</strong> just got a patch. Dust it off?
					<a class="underline" href="/patch-notes?game={dustedOffPatch.game.id}">Read it</a>
				</p>
			{/if}
			<ul class="flex flex-col divide-y divide-grid">
				{#each dust as g (g.game.id)}
					<li class="flex items-center gap-3 py-2">
						<GameTile emoji={g.emoji} color={colorFor(colors, g)} name={g.game.name} size="sm" />
						<span class="min-w-0 flex-1 truncate">{g.game.name}</span>
						{#if g.has_recent_patch}<span class="badge-patch">📜 {copy.games.newPatch}</span>{/if}
						<span class="text-sm whitespace-nowrap text-ink-2">
							{g.days_since_played === null
								? copy.games.neverPlayed
								: relativeDays(g.days_since_played)}
						</span>
					</li>
				{:else}
					<li class="py-2 text-ink-2">Everything's been played recently. Nice.</li>
				{/each}
			</ul>
		</Card>
	</div>

	{#if data.latestPatches.length}
		<div class="mt-6">
			<Card title="Latest from Grok" subtitle="Recent patch notes for the rotation">
				<ul class="flex flex-col gap-2">
					{#each data.latestPatches as p (p.id)}
						<li class="flex flex-wrap items-baseline gap-x-2">
							<strong>{p.game_name}</strong>
							<span class="text-ink-2">{p.title}{p.version ? ` (${p.version})` : ''}</span>
						</li>
					{/each}
				</ul>
				<a href="/patch-notes" class="mt-4 inline-block text-sm font-semibold underline"
					>All patch notes →</a
				>
			</Card>
		</div>
	{/if}
{/if}
