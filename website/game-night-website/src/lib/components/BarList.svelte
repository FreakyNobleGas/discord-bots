<script module lang="ts">
	export interface BarRow {
		key: string;
		label: string;
		value: number;
		/** Text at the bar tip */
		display: string;
		/** Tooltip detail line */
		detail?: string;
		color?: string;
		emoji?: string;
	}
</script>

<script lang="ts">
	import Tooltip from './Tooltip.svelte';

	interface Props {
		rows: BarRow[];
		/** Fixed max so several lists can share a scale; defaults to the largest value */
		max?: number;
		label: string;
		selected?: string | null;
		onselect?: (key: string) => void;
	}

	let { rows, max, label, selected = null, onselect }: Props = $props();

	const scaleMax = $derived(max ?? Math.max(1, ...rows.map((r) => r.value)));

	let width = $state(0);
	let hover = $state<{ row: BarRow; x: number; y: number } | null>(null);

	function show(row: BarRow, el: HTMLElement) {
		const box = el.closest('[data-barlist]')!.getBoundingClientRect();
		const bar = el.querySelector('[data-bar]')!.getBoundingClientRect();
		hover = { row, x: bar.right - box.left, y: bar.top - box.top };
	}
</script>

{#snippet rowBody(row: BarRow)}
	<span class="flex min-w-0 items-center gap-1.5 truncate text-sm text-ink-2">
		{#if row.emoji}<span aria-hidden="true">{row.emoji}</span>{/if}
		<span class="truncate">{row.label}</span>
	</span>
	<span class="flex items-center gap-2">
		<span
			data-bar
			class="h-[18px] rounded-r-[4px] transition-[filter]"
			style:width="max(3px, calc((100% - 4.5rem) * {row.value / scaleMax}))"
			style:background={row.color ?? 'var(--series-neutral)'}
		></span>
		<span class="tnum text-sm font-semibold whitespace-nowrap">{row.display}</span>
	</span>
{/snippet}

<div class="relative" data-barlist bind:clientWidth={width}>
	<ul class="flex flex-col gap-1" aria-label={label}>
		{#each rows as row (row.key)}
			<li>
				{#if onselect}
					<button
						type="button"
						class={[
							'grid w-full grid-cols-[minmax(6rem,10rem)_1fr] items-center gap-3 rounded-md px-1.5 py-1 text-left hover:bg-paper-2 [&:hover_[data-bar]]:brightness-110',
							selected === row.key && 'bg-paper-2 ring-2 ring-outline'
						]}
						aria-pressed={selected === row.key}
						onclick={() => onselect(row.key)}
						onpointerenter={(e) => show(row, e.currentTarget)}
						onpointerleave={() => (hover = null)}
						onfocus={(e) => show(row, e.currentTarget)}
						onblur={() => (hover = null)}
					>
						{@render rowBody(row)}
					</button>
				{:else}
					<div
						class="grid grid-cols-[minmax(6rem,10rem)_1fr] items-center gap-3 px-1.5 py-1 [&:hover_[data-bar]]:brightness-110"
						role="group"
						aria-label="{row.label}: {row.display}"
						onpointerenter={(e) => show(row, e.currentTarget)}
						onpointerleave={() => (hover = null)}
					>
						{@render rowBody(row)}
					</div>
				{/if}
			</li>
		{/each}
	</ul>
	{#if hover?.row.detail}
		<Tooltip x={hover.x} y={hover.y} bound={width}>
			<div class="font-semibold">{hover.row.detail}</div>
			<div class="text-ink-2">{hover.row.label}</div>
		</Tooltip>
	{/if}
</div>
