<script lang="ts">
	import { pct } from '#lib/view.ts';
	import Tooltip from './Tooltip.svelte';

	interface Segment {
		key: string;
		label: string;
		value: number;
		share: number;
		color: string;
	}

	let { segments, unit = 'sessions' }: { segments: Segment[]; unit?: string } = $props();

	const visible = $derived(segments.filter((s) => s.value > 0));

	let width = $state(0);
	let hover = $state<{ seg: Segment; x: number } | null>(null);

	function show(seg: Segment, el: HTMLElement) {
		const parent = el.parentElement!.getBoundingClientRect();
		const r = el.getBoundingClientRect();
		hover = { seg, x: r.left - parent.left + r.width / 2 };
	}
</script>

<div class="relative" bind:clientWidth={width}>
	<div class="flex h-7 gap-[2px] overflow-hidden rounded-[4px] bg-paper" role="list">
		{#each visible as seg (seg.key)}
			<div
				role="listitem"
				aria-label="{seg.label}: {seg.value} {unit}, {pct(seg.share)}"
				class="h-full min-w-[3px] transition-[filter] hover:brightness-110"
				style:flex-grow={seg.share}
				style:flex-basis="0"
				style:background={seg.color}
				onpointerenter={(e) => show(seg, e.currentTarget)}
				onpointerleave={() => (hover = null)}
			></div>
		{/each}
	</div>
	{#if hover}
		<Tooltip x={hover.x} y={0} bound={width}>
			<div class="font-semibold">{pct(hover.seg.share)} · {hover.seg.value} {unit}</div>
			<div class="text-ink-2">{hover.seg.label}</div>
		</Tooltip>
	{/if}
</div>

<ul class="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-sm" aria-label="Legend">
	{#each visible as seg (seg.key)}
		<li class="flex items-center gap-1.5">
			<span
				class="inline-block size-3 rounded-[3px]"
				style:background={seg.color}
				aria-hidden="true"
			></span>
			<span class="text-ink-2">{seg.label}</span>
			<span class="tnum font-semibold">{pct(seg.share)}</span>
		</li>
	{/each}
</ul>
