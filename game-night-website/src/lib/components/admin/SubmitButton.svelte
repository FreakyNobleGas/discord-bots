<script lang="ts">
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<button
	class="cutout-sm self-end px-3 py-1.5 font-bold text-ink hover:-rotate-1 focus-visible:-rotate-1"
>
	{@render children()}
</button>
