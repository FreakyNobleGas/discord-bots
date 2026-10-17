<script lang="ts">
	import type { Snippet } from 'svelte';

	let { title, intro, children }: { title: string; intro: string; children?: Snippet } = $props();
</script>

<div class="mb-6 flex flex-wrap items-end justify-between gap-4">
	<div>
		<h1 class="display text-3xl text-ink sm:text-4xl">{title}</h1>
		<p class="mt-1 text-ink-2">{intro}</p>
	</div>
	{@render children?.()}
</div>
