<script lang="ts">
	import { copy } from '#lib/copy.ts';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const tiles = $derived([
		{ href: '/admin/games', label: copy.admin.games, n: data.counts.games },
		{ href: '/admin/sessions', label: copy.admin.sessions, n: data.counts.sessions },
		{ href: '/admin/patch-notes', label: copy.admin.patchNotes, n: data.counts.patch_notes },
		{ href: '/admin/suggestions', label: copy.admin.suggestions, n: data.counts.suggestions }
	]);
</script>

<svelte:head>
	<title>{copy.admin.title} · {copy.site.name}</title>
</svelte:head>

<PageHeader title={copy.admin.title} intro={copy.admin.intro} />

<ul class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
	{#each tiles as tile (tile.href)}
		<li>
			<a href={tile.href} class="cutout block p-4 no-underline hover:-rotate-1">
				<span class="display tnum block text-3xl text-ink">{tile.n}</span>
				<span class="font-semibold text-ink-2">{tile.label}</span>
			</a>
		</li>
	{/each}
</ul>
<p class="mt-6 text-sm text-muted">Guild {data.guild}</p>
