<script lang="ts">
	import { scaleLinear } from 'd3-scale';
	import { area, curveMonotoneX, stack, stackOffsetExpand, stackOffsetNone } from 'd3-shape';
	import { formatMonth } from '#lib/dates.ts';
	import type { MonthBucket } from '#lib/types.ts';
	import Tooltip from './Tooltip.svelte';

	interface Props {
		months: MonthBucket[];
		series: { key: string; color: string }[];
		mode: 'count' | 'share';
		label: string;
	}

	let { months, series, mode, label }: Props = $props();

	const HEIGHT = 260;
	const M = { top: 12, right: 12, bottom: 28, left: 40 };

	let width = $state(640);
	let active = $state<number | null>(null);

	const innerW = $derived(Math.max(0, width - M.left - M.right));
	const innerH = HEIGHT - M.top - M.bottom;
	const keys = $derived(series.map((s) => s.key));

	const layers = $derived(
		stack<MonthBucket, string>()
			.keys(keys)
			.value((d, key) => d.counts[key] ?? 0)
			.offset(mode === 'share' ? stackOffsetExpand : stackOffsetNone)(months)
	);

	const x = $derived(
		scaleLinear()
			.domain([0, Math.max(1, months.length - 1)])
			.range([0, innerW])
	);
	const y = $derived(
		scaleLinear()
			.domain([0, mode === 'share' ? 1 : Math.max(1, ...months.map((m) => m.total))])
			.nice()
			.range([innerH, 0])
	);

	const areaGen = $derived(
		area<[number, number] & { data: MonthBucket }>()
			.x((_, i) => x(i))
			// stackOffsetExpand yields NaN for empty months; treat them as zero height
			.y0((d) => y(Number.isFinite(d[0]) ? d[0] : 0))
			.y1((d) => y(Number.isFinite(d[1]) ? d[1] : 0))
			.curve(curveMonotoneX)
	);

	const yTicks = $derived(y.ticks(4));
	const xEvery = $derived(
		Math.max(1, Math.ceil(months.length / Math.max(1, Math.floor(innerW / 60))))
	);
	const fmtY = (v: number) => (mode === 'share' ? `${Math.round(v * 100)}%` : String(v));

	const colorOf = $derived(new Map(series.map((s) => [s.key, s.color])));

	function nearest(clientX: number, rect: DOMRect) {
		const i = Math.round(x.invert(clientX - rect.left));
		return Math.min(months.length - 1, Math.max(0, i));
	}

	function onkeydown(e: KeyboardEvent) {
		if (!months.length) return;
		if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
			e.preventDefault();
			const step = e.key === 'ArrowRight' ? 1 : -1;
			active = Math.min(
				months.length - 1,
				Math.max(0, (active ?? (step > 0 ? -1 : months.length)) + step)
			);
		} else if (e.key === 'Escape') {
			active = null;
		}
	}

	const activeMonth = $derived(active === null ? null : months[active]);
	const rows = $derived(
		activeMonth
			? [...series]
					.reverse()
					.map((s) => ({
						key: s.key,
						color: s.color,
						value: activeMonth.counts[s.key] ?? 0
					}))
					.filter((r) => r.value > 0)
			: []
	);
</script>

<ul class="mb-3 flex flex-wrap gap-x-4 gap-y-1.5 text-sm" aria-label="Legend">
	{#each series as s (s.key)}
		<li class="flex items-center gap-1.5">
			<span class="inline-block size-3 rounded-[3px]" style:background={s.color} aria-hidden="true"
			></span>
			<span class="text-ink-2">{s.key}</span>
		</li>
	{/each}
</ul>

<div class="relative" bind:clientWidth={width}>
	<svg {width} height={HEIGHT} role="img" aria-label={label} class="block overflow-visible">
		<g transform="translate({M.left},{M.top})">
			{#each yTicks as t (t)}
				<line x1="0" x2={innerW} y1={y(t)} y2={y(t)} stroke="var(--grid)" stroke-width="1" />
				<text x="-8" y={y(t)} dy="0.32em" text-anchor="end" class="tnum fill-muted text-[11px]">
					{fmtY(t)}
				</text>
			{/each}

			{#each layers as layer (layer.key)}
				<path
					d={areaGen(layer as never) ?? ''}
					fill={colorOf.get(layer.key)}
					stroke="var(--paper)"
					stroke-width="2"
					stroke-linejoin="round"
				/>
			{/each}

			<line x1="0" x2={innerW} y1={innerH} y2={innerH} stroke="var(--axis)" stroke-width="1" />
			{#each months as m, i (m.month)}
				{#if i % xEvery === 0 || i === months.length - 1}
					<text
						x={x(i)}
						y={innerH + 18}
						text-anchor={i === 0 ? 'start' : i === months.length - 1 ? 'end' : 'middle'}
						class="fill-muted text-[11px]"
					>
						{formatMonth(m.month)}
					</text>
				{/if}
			{/each}

			{#if active !== null}
				<line
					x1={x(active)}
					x2={x(active)}
					y1="0"
					y2={innerH}
					stroke="var(--ink)"
					stroke-width="1"
				/>
			{/if}

			<rect
				width={innerW}
				height={innerH}
				fill="transparent"
				tabindex="0"
				role="slider"
				aria-label="Month — use arrow keys to read values"
				aria-valuemin={0}
				aria-valuemax={months.length - 1}
				aria-valuenow={active ?? 0}
				aria-valuetext={activeMonth ? formatMonth(activeMonth.month, 'long') : 'none'}
				class="outline-none focus-visible:stroke-[var(--focus)] focus-visible:stroke-2"
				onpointermove={(e) =>
					(active = nearest(e.clientX, e.currentTarget.getBoundingClientRect()))}
				onpointerleave={() => (active = null)}
				{onkeydown}
				onblur={() => (active = null)}
			/>
		</g>
	</svg>

	{#if activeMonth && active !== null}
		<Tooltip x={M.left + x(active)} y={M.top + 4} bound={width}>
			<div class="mb-1 text-xs font-semibold text-ink-2">
				{formatMonth(activeMonth.month, 'long')} · {activeMonth.total} sessions
			</div>
			{#if rows.length}
				<ul class="flex flex-col gap-0.5">
					{#each rows as r (r.key)}
						<li class="flex items-center gap-2 whitespace-nowrap">
							<span
								class="inline-block h-0.5 w-3 rounded"
								style:background={r.color}
								aria-hidden="true"
							></span>
							<span class="tnum font-semibold">
								{mode === 'share' ? `${Math.round((r.value / activeMonth.total) * 100)}%` : r.value}
							</span>
							<span class="text-ink-2">{r.key}</span>
						</li>
					{/each}
				</ul>
			{:else}
				<div class="text-ink-2">No sessions</div>
			{/if}
		</Tooltip>
	{/if}
</div>

<details class="mt-4 text-sm">
	<summary class="cursor-pointer text-ink-2 select-none">Show as table</summary>
	<div class="mt-2 overflow-x-auto">
		<table class="tnum w-full text-left">
			<thead class="text-xs text-muted">
				<tr>
					<th class="py-1 pr-3 font-medium">Month</th>
					{#each series as s (s.key)}
						<th class="py-1 pr-3 font-medium whitespace-nowrap">{s.key}</th>
					{/each}
					<th class="py-1 font-medium">Total</th>
				</tr>
			</thead>
			<tbody>
				{#each months as m (m.month)}
					<tr class="border-t border-grid">
						<td class="py-1 pr-3 whitespace-nowrap">{formatMonth(m.month, 'long')}</td>
						{#each series as s (s.key)}
							<td class="py-1 pr-3">{m.counts[s.key] ?? 0}</td>
						{/each}
						<td class="py-1 font-semibold">{m.total}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</details>
