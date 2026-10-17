<script lang="ts">
	import { page } from '$app/state';
	import { copy } from '#lib/copy.ts';
	import type { LayoutProps } from './$types';

	let { data, children }: LayoutProps = $props();

	const links = [
		{ href: '/admin', label: copy.admin.title },
		{ href: '/admin/games', label: copy.admin.games },
		{ href: '/admin/sessions', label: copy.admin.sessions },
		{ href: '/admin/patch-notes', label: copy.admin.patchNotes },
		{ href: '/admin/suggestions', label: copy.admin.suggestions }
	];
</script>

<svelte:head>
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

{#if data.admin}
	<nav aria-label="Admin" class="mb-6 flex flex-wrap items-center gap-2 text-sm">
		{#each links as link (link.href)}
			<a
				href={link.href}
				aria-current={page.url.pathname === link.href ? 'page' : undefined}
				class={[
					'rounded-md border-2 border-outline px-2.5 py-1 font-semibold no-underline',
					page.url.pathname === link.href ? 'bg-ink text-paper' : 'bg-paper text-ink'
				]}
			>
				{link.label}
			</a>
		{/each}
		<form method="POST" action="/admin/logout" class="ml-auto">
			<button
				class="rounded-md border-2 border-outline bg-paper px-2.5 py-1 font-semibold text-ink"
			>
				{copy.admin.signOut}
			</button>
		</form>
	</nav>
{/if}

{@render children()}
