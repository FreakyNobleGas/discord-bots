<script lang="ts">
	import { page } from '$app/state';

	const form = $derived(page.form as { ok?: string; error?: string } | null);
</script>

<div aria-live="polite" class="min-h-0">
	{#if form?.error}
		<p class="cutout-sm mb-4 border-l-8 px-3 py-2 font-semibold text-ink" role="alert">
			⚠️ {form.error}
		</p>
	{:else if form?.ok}
		<p class="cutout-sm mb-4 px-3 py-2 font-semibold text-ink">✅ {form.ok}</p>
	{/if}
</div>
