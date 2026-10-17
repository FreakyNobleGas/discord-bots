<script lang="ts">
	interface Props {
		emoji: string;
		color: string;
		cover?: string;
		name: string;
		size?: 'sm' | 'md';
	}

	let { emoji, color, cover = '', name, size = 'md' }: Props = $props();
</script>

<span
	class={[
		'inline-grid shrink-0 place-items-center overflow-hidden border-2 border-outline',
		size === 'sm' ? 'size-8 rounded-md text-base' : 'size-11 rounded-lg text-xl'
	]}
	style:background="color-mix(in oklab, {color} 28%, var(--paper))"
>
	{#if cover}
		<img src={cover} alt="" class="size-full object-cover" loading="lazy" />
	{:else}
		<span role="img" aria-label="{name} icon">{emoji}</span>
	{/if}
</span>
