<script lang="ts">
	import { enhance } from '$app/forms';
	import { copy } from '#lib/copy.ts';

	// Two-step delete without a JS confirm(): open the disclosure, then press the real button.
	let { id, label, note }: { id: string | number; label: string; note?: string } = $props();
</script>

<details class="group">
	<summary
		class="cursor-pointer list-none rounded-md border-2 border-outline px-2.5 py-1 text-sm font-semibold text-ink-2 hover:bg-paper-2 [&::-webkit-details-marker]:hidden"
	>
		{copy.admin.delete}
	</summary>
	<form method="POST" action="?/delete" use:enhance class="mt-2 flex flex-wrap items-center gap-2">
		<input type="hidden" name="id" value={id} />
		{#if note}<span class="text-xs text-ink-2">{note}</span>{/if}
		<button
			class="rounded-md border-2 border-outline bg-accent px-2.5 py-1 text-sm font-bold text-accent-ink"
			aria-label="{copy.admin.reallyDelete} {label}"
		>
			{copy.admin.reallyDelete}
		</button>
	</form>
</details>
