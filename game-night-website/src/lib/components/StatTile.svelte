<script lang="ts">
	let {
		label,
		value,
		note,
		tilt = 0
	}: { label: string; value: string; note?: string; tilt?: number } = $props();
</script>

<div class="cutout px-4 py-3" style:transform="rotate({tilt}deg)">
	<div class="text-sm text-ink-2">{label}</div>
	<div class="mt-0.5 text-3xl font-bold text-ink">{value}</div>
	{#if note}<div class="mt-0.5 text-xs text-muted">{note}</div>{/if}
</div>
