<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		/** Anchor point, relative to the positioned parent */
		x: number;
		y: number;
		/** Parent width, used to keep the tooltip on-screen */
		bound?: number;
		children: Snippet;
	}

	let { x, y, bound, children }: Props = $props();

	let width = $state(0);
	const left = $derived(bound ? Math.min(Math.max(x, width / 2 + 4), bound - width / 2 - 4) : x);
</script>

<div
	bind:clientWidth={width}
	class="pointer-events-none absolute z-20 min-w-32 rounded-lg border-2 border-outline bg-paper px-3 py-2 text-sm shadow-[3px_3px_0_var(--outline)]"
	style:left="{left}px"
	style:top="{y}px"
	style:transform="translate(-50%, calc(-100% - 10px))"
	role="status"
>
	{@render children()}
</div>
