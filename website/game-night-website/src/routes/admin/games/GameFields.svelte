<script lang="ts">
	import Field from '#lib/components/admin/Field.svelte';

	interface Game {
		name: string;
		rawg_id: number | null;
		rawg_slug: string | null;
		cover_url: string;
		genre_tags: string[];
		added_by: string;
	}

	let { game }: { game?: Game } = $props();
</script>

<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
	<Field label="Name" name="name" value={game?.name} required maxlength={200} />
	<Field label="Added by" name="added_by" value={game?.added_by} required maxlength={100} />
	<Field
		label="Genre tags"
		name="genre_tags"
		value={game?.genre_tags.join(', ')}
		hint="RAWG genre names, comma-separated (e.g. Action, Shooter)"
		class="sm:col-span-2"
	/>
	<Field label="RAWG slug" name="rawg_slug" value={game?.rawg_slug} placeholder="helldivers-2" />
	<Field label="RAWG id" name="rawg_id" type="number" value={game?.rawg_id} />
	<Field
		label="Cover URL"
		name="cover_url"
		type="url"
		value={game?.cover_url}
		class="sm:col-span-2"
	/>
</div>
