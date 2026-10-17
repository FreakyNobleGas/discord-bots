<script lang="ts">
	import './layout.css';
	import favicon from '#lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { copy } from '#lib/copy.ts';
	import ThemeToggle from '#lib/components/ThemeToggle.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	const links = [
		{ href: '/', label: copy.nav.overview, emoji: '🏠' },
		{ href: '/genres', label: copy.nav.genres, emoji: '🎭' },
		{ href: '/games', label: copy.nav.games, emoji: '🏆' },
		{ href: '/patch-notes', label: copy.nav.patchNotes, emoji: '📜' },
		{ href: '/suggestions', label: copy.nav.suggestions, emoji: '🔮' }
	];

	const isActive = (href: string) =>
		href === '/' ? page.url.pathname === '/' : page.url.pathname.startsWith(href);
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<header class="relative overflow-hidden border-b-4 border-outline">
	<!-- Original paper-cutout mountain town backdrop -->
	<svg
		class="pointer-events-none absolute inset-0 h-full w-full"
		viewBox="0 0 1200 220"
		preserveAspectRatio="xMidYMax slice"
		aria-hidden="true"
	>
		<rect width="1200" height="220" style="fill: var(--sky)" />
		<path
			d="M0 170 L120 70 L190 130 L300 40 L410 140 L520 60 L640 150 L760 50 L880 140 L990 70 L1100 130 L1200 80 L1200 220 L0 220 Z"
			fill="#6b7c8f"
			stroke="#1d1b1a"
			stroke-width="4"
			stroke-linejoin="round"
		/>
		<path
			d="M120 70 L95 91 L112 100 L128 88 L146 101 L158 99 Z M300 40 L270 72 L292 82 L308 66 L328 84 L340 78 Z M520 60 L492 88 L512 96 L528 82 L546 98 L556 92 Z M760 50 L730 82 L752 92 L770 76 L788 94 L800 88 Z M990 70 L962 96 L982 104 L998 90 L1014 104 L1024 98 Z"
			fill="#fff"
		/>
		<path
			d="M0 190 Q300 165 600 188 T1200 182 L1200 220 L0 220 Z"
			fill="#fff"
			stroke="#1d1b1a"
			stroke-width="4"
		/>
		{#each Array.from({ length: 28 }, (_, i) => i) as i (i)}
			<circle cx={(i * 137) % 1200} cy={(i * 53) % 150} r={2 + (i % 3)} fill="#fff" opacity="0.9" />
		{/each}
	</svg>

	<div class="relative mx-auto flex max-w-6xl flex-col gap-4 px-4 pt-6 pb-10 sm:pt-8 sm:pb-14">
		<div class="flex items-start justify-between gap-3">
			<a
				href="/"
				class="cutout inline-block -rotate-1 px-4 py-2 no-underline sm:px-6 sm:py-3"
				aria-label="{copy.site.name} home"
			>
				<span class="display block text-2xl leading-tight text-ink sm:text-4xl">
					{copy.site.name}
				</span>
				<span class="mt-0.5 block text-sm text-ink-2">{copy.site.tagline}</span>
			</a>
			<ThemeToggle />
		</div>

		<nav aria-label="Main">
			<ul class="flex flex-wrap gap-2">
				{#each links as link (link.href)}
					<li>
						<a
							href={link.href}
							aria-current={isActive(link.href) ? 'page' : undefined}
							class={[
								'cutout-sm inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold no-underline transition-transform hover:-translate-y-0.5',
								isActive(link.href) && 'bg-accent! text-accent-ink!'
							]}
						>
							<span aria-hidden="true">{link.emoji}</span>{link.label}
						</a>
					</li>
				{/each}
			</ul>
		</nav>
	</div>
</header>

<main class="mx-auto max-w-6xl px-4 py-8">
	{@render children()}
</main>

<footer class="mx-auto max-w-6xl px-4 pb-10 text-xs text-muted">
	{copy.site.footer} · <a class="underline" href="/api/v1">API</a> ·
	<a class="underline" href="/admin" rel="nofollow">{copy.admin.nav}</a>
</footer>
