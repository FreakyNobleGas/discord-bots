<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		subtitle?: string;
		actions?: Snippet;
		children: Snippet;
		class?: string;
	}

	let { title, subtitle, actions, children, class: klass = '' }: Props = $props();
</script>

<section class={['cutout p-4 sm:p-5', klass]}>
	<div class="mb-4 flex flex-wrap items-start justify-between gap-2">
		<div>
			<h2 class="display text-xl text-ink">{title}</h2>
			{#if subtitle}<p class="mt-0.5 text-sm text-ink-2">{subtitle}</p>{/if}
		</div>
		{@render actions?.()}
	</div>
	{@render children()}
</section>
