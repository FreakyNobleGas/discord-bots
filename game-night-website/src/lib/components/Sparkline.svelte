<script lang="ts">
	let { values, label }: { values: number[]; label: string } = $props();

	const W = 96;
	const H = 24;
	const PAD = 3;

	const max = $derived(Math.max(1, ...values));
	const pts = $derived(
		values.map((v, i) => [
			PAD + (values.length > 1 ? (i / (values.length - 1)) * (W - PAD * 2) : (W - PAD * 2) / 2),
			H - PAD - (v / max) * (H - PAD * 2)
		])
	);
	const d = $derived(
		pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join('')
	);
	const last = $derived(pts.at(-1));
</script>

<svg
	width={W}
	height={H}
	viewBox="0 0 {W} {H}"
	role="img"
	aria-label={label}
	class="overflow-visible"
>
	<line x1={PAD} x2={W - PAD} y1={H - PAD} y2={H - PAD} stroke="var(--grid)" stroke-width="1" />
	<path
		{d}
		fill="none"
		stroke="var(--series-neutral)"
		stroke-width="2"
		stroke-linejoin="round"
		stroke-linecap="round"
	/>
	{#if last}
		<circle
			cx={last[0]}
			cy={last[1]}
			r="3.5"
			fill="var(--accent)"
			stroke="var(--paper)"
			stroke-width="2"
		/>
	{/if}
</svg>
