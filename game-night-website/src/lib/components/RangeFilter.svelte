<script lang="ts">
	import { page } from '$app/state';
	import { copy } from '#lib/copy.ts';
	import { RANGES, type Range } from '#lib/types.ts';

	let { range }: { range: Range } = $props();

	function href(r: Range) {
		const url = new URL(page.url.href);
		if (r === 'all') url.searchParams.delete('range');
		else url.searchParams.set('range', r);
		return url.pathname + url.search;
	}
</script>

<div class="flex flex-wrap items-center gap-2" role="group" aria-label={copy.range.label}>
	<span class="text-sm text-ink-2">{copy.range.label}</span>
	{#each RANGES as r (r)}
		<a
			href={href(r)}
			data-sveltekit-reset="false"
			aria-current={r === range ? 'true' : undefined}
			class={[
				'rounded-full border-2 border-outline px-3 py-0.5 text-sm font-semibold no-underline',
				r === range ? 'bg-ink text-paper' : 'bg-paper text-ink hover:bg-paper-2'
			]}
		>
			{#if r === range}<span aria-hidden="true">✓ </span>{/if}{copy.range[r]}
		</a>
	{/each}
</div>
