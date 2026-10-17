<script lang="ts">
	import { onMount } from 'svelte';

	type Theme = 'system' | 'light' | 'dark';
	const order: Theme[] = ['system', 'light', 'dark'];
	const labels: Record<Theme, string> = {
		system: '🖥️ Auto',
		light: '❄️ Upstairs',
		dark: '🛋️ Basement'
	};

	let theme = $state<Theme>('system');

	// The saved theme is applied in app.html before paint; sync the button label once mounted.
	onMount(() => {
		const t = document.documentElement.dataset.theme;
		theme = t === 'light' || t === 'dark' ? t : 'system';
	});

	function cycle() {
		theme = order[(order.indexOf(theme) + 1) % order.length];
		const root = document.documentElement;
		if (theme === 'system') delete root.dataset.theme;
		else root.dataset.theme = theme;
		try {
			if (theme === 'system') localStorage.removeItem('theme');
			else localStorage.setItem('theme', theme);
		} catch {
			// storage unavailable (private mode) — the theme still applies for this visit
		}
	}
</script>

<button
	type="button"
	class="cutout-sm shrink-0 px-3 py-1.5 text-sm font-semibold whitespace-nowrap"
	onclick={cycle}
	aria-label="Theme: {theme}. Click to change."
>
	{labels[theme]}
</button>
