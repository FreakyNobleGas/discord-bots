<script lang="ts">
	import Field from '#lib/components/admin/Field.svelte';

	interface Props {
		games: { id: number; name: string }[];
		session?: {
			game_id: number;
			played_on: string;
			logged_by: string | null;
			notes: string | null;
		};
		tz: string;
	}

	let { games, session, tz }: Props = $props();
	const id = $props.id();
</script>

<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
	<div class="flex flex-col gap-1">
		<label for="{id}-game" class="text-sm font-semibold text-ink-2">
			Game<span aria-hidden="true"> *</span>
		</label>
		<select
			id="{id}-game"
			name="game_id"
			required
			class="rounded-md border-2 border-outline bg-paper px-2 py-1.5 text-ink"
		>
			{#if !session}<option value="" disabled selected>Pick a game</option>{/if}
			{#each games as game (game.id)}
				<option value={game.id} selected={game.id === session?.game_id}>{game.name}</option>
			{/each}
		</select>
	</div>
	<Field
		label="Played on"
		name="played_on"
		type="datetime-local"
		value={session?.played_on}
		required
		hint="Local time in {tz}"
	/>
	<Field label="Logged by" name="logged_by" value={session?.logged_by} maxlength={100} />
	<Field label="Notes" name="notes" value={session?.notes} maxlength={1000} />
</div>
