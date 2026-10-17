<script lang="ts">
	import { copy } from '#lib/copy.ts';
	import { formatDay, formatMonth, relativeDays } from '#lib/dates.ts';
	import type { GameStats } from '#lib/types.ts';
	import { colorFor, genreColorMap, pct, plural } from '#lib/view.ts';
	import Card from '#lib/components/Card.svelte';
	import GameTile from '#lib/components/GameTile.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import RangeFilter from '#lib/components/RangeFilter.svelte';
	import Sparkline from '#lib/components/Sparkline.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const a = $derived(data.analysis);
	const colors = $derived(genreColorMap(a.genre_share));

	type SortKey = 'sessions' | 'last' | 'idle' | 'name';
	const sorts: { key: SortKey; label: string }[] = [
		{ key: 'sessions', label: 'Most played' },
		{ key: 'last', label: 'Recently played' },
		{ key: 'idle', label: 'Longest idle' },
		{ key: 'name', label: 'Name' }
	];
	let sort = $state<SortKey>('sessions');

	const idle = (g: GameStats) => g.days_since_played ?? Infinity;
	const compare: Record<SortKey, (x: GameStats, y: GameStats) => number> = {
		sessions: (x, y) => y.session_count - x.session_count || y.total_sessions - x.total_sessions,
		last: (x, y) => idle(x) - idle(y),
		idle: (x, y) => idle(y) - idle(x),
		name: (x, y) => x.game.name.localeCompare(y.game.name)
	};
	const rows = $derived(
		[...a.games].sort((x, y) => compare[sort](x, y) || x.game.name.localeCompare(y.game.name))
	);
	const rank = $derived(new Map(a.games.map((g, i) => [g.game.id, i + 1])));
	const monthSpan = $derived(
		a.months.length
			? `${formatMonth(a.months[0].month)}–${formatMonth(a.months.at(-1)!.month)}`
			: ''
	);
</script>

<svelte:head>
	<title>{copy.games.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader title={copy.games.title} intro={copy.games.intro}>
	<RangeFilter range={a.range} />
</PageHeader>

<Card
	title="The rotation"
	subtitle="{plural(a.games.length, 'game')} · {plural(a.kpis.sessions, 'session')} in this range"
>
	{#snippet actions()}
		<label class="flex items-center gap-2 text-sm">
			<span class="text-ink-2">Sort</span>
			<select
				bind:value={sort}
				class="rounded-md border-2 border-outline bg-paper px-2 py-1 font-semibold"
			>
				{#each sorts as s (s.key)}
					<option value={s.key}>{s.label}</option>
				{/each}
			</select>
		</label>
	{/snippet}

	<div class="-mx-4 overflow-x-auto sm:mx-0">
		<table class="w-full min-w-[20rem] text-left text-sm">
			<thead class="text-xs text-muted">
				<tr class="border-b-2 border-outline">
					<th scope="col" class="w-8 py-2 pr-2 pl-4 font-medium sm:pl-0">#</th>
					<th scope="col" class="py-2 pr-3 font-medium">Game</th>
					<th scope="col" class="hidden py-2 pr-3 font-medium md:table-cell">Genres</th>
					<th scope="col" class="py-2 pr-3 text-right font-medium">Sessions</th>
					<th scope="col" class="hidden py-2 pr-3 font-medium sm:table-cell">Last played</th>
					<th scope="col" class="hidden py-2 pr-3 font-medium lg:table-cell">
						Monthly <span class="font-normal">({monthSpan})</span>
					</th>
					<th scope="col" class="hidden py-2 pr-4 font-medium sm:pr-0 lg:table-cell">Added by</th>
				</tr>
			</thead>
			<tbody>
				{#each rows as g (g.game.id)}
					<tr class="border-b border-grid align-middle">
						<td class="tnum py-2.5 pr-2 pl-4 text-muted sm:pl-0">{rank.get(g.game.id)}</td>
						<td class="py-2.5 pr-3">
							<div class="flex items-center gap-3">
								<GameTile
									emoji={g.emoji}
									color={colorFor(colors, g)}
									cover={g.game.cover_url}
									name={g.game.name}
								/>
								<div class="min-w-0">
									<div class="flex flex-wrap items-center gap-x-2 gap-y-1">
										<span class="font-semibold">{g.game.name}</span>
										{#if g.has_recent_patch}
											<a href="/patch-notes?game={g.game.id}" class="badge-patch no-underline"
												>📜 {copy.games.newPatch}</a
											>
										{/if}
									</div>
									<div class="text-xs text-ink-2 md:hidden">{g.primary_genre}</div>
									<div class="text-xs text-ink-2 sm:hidden">
										last {relativeDays(g.days_since_played)}
									</div>
								</div>
							</div>
						</td>
						<td class="hidden py-2.5 pr-3 md:table-cell">
							<div class="flex flex-wrap gap-1">
								{#each g.game.genre_tags as tag (tag)}
									<span class="chip">{tag}</span>
								{:else}
									<span class="chip italic">untagged</span>
								{/each}
							</div>
						</td>
						<td class="tnum py-2.5 pr-3 text-right whitespace-nowrap">
							<span class="font-semibold">{g.session_count}</span>
							<span class="block text-xs text-ink-2">{pct(g.share)}</span>
						</td>
						<td class="hidden py-2.5 pr-3 whitespace-nowrap sm:table-cell">
							{#if g.last_played}
								<span>{relativeDays(g.days_since_played)}</span>
								<span class="block text-xs text-ink-2">{formatDay(g.last_played)}</span>
							{:else}
								<span class="text-ink-2">{copy.games.neverPlayed}</span>
							{/if}
						</td>
						<td class="hidden py-2.5 pr-3 lg:table-cell">
							<Sparkline
								values={g.monthly}
								label="{g.game.name}: {g.monthly.join(', ')} sessions per month"
							/>
						</td>
						<td class="hidden py-2.5 pr-4 text-ink-2 sm:pr-0 lg:table-cell">{g.game.added_by}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</Card>

<div class="mt-8">
	<h2 class="display text-2xl text-ink">{copy.games.dust}</h2>
	<p class="mt-1 text-ink-2">{copy.games.dustIntro}</p>
	<ul class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each a.collecting_dust as g, i (g.game.id)}
			<li
				class="cutout-sm flex items-center gap-3 p-3"
				style:transform="rotate({[-0.7, 0.5, -0.3, 0.8][i % 4]}deg)"
			>
				<GameTile
					emoji={g.emoji}
					color={colorFor(colors, g)}
					cover={g.game.cover_url}
					name={g.game.name}
				/>
				<div class="min-w-0 flex-1">
					<div class="truncate font-semibold">{g.game.name}</div>
					<div class="text-sm text-ink-2">
						{#if g.days_since_played === null}
							{copy.games.neverPlayed} · added by {g.game.added_by}
						{:else}
							{g.days_since_played} days idle · {plural(g.total_sessions, 'session')} all-time
						{/if}
					</div>
				</div>
				{#if g.has_recent_patch}
					<a href="/patch-notes?game={g.game.id}" class="badge-patch no-underline"
						>📜 {copy.games.newPatch}</a
					>
				{/if}
			</li>
		{:else}
			<li class="text-ink-2">Everything's been played recently. Nice.</li>
		{/each}
	</ul>
</div>
