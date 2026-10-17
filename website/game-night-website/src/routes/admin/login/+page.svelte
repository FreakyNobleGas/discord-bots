<script lang="ts">
	import { enhance } from '$app/forms';
	import { copy } from '#lib/copy.ts';
	import Field from '#lib/components/admin/Field.svelte';
	import FormStatus from '#lib/components/admin/FormStatus.svelte';
	import SubmitButton from '#lib/components/admin/SubmitButton.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<svelte:head>
	<title>{copy.admin.login} · {copy.site.name}</title>
</svelte:head>

<div class="mx-auto max-w-sm">
	<h1 class="display text-3xl text-ink">{copy.admin.login}</h1>
	<p class="mt-1 mb-6 text-ink-2">{copy.admin.loginIntro}</p>
	<FormStatus />
	{#if data.configured}
		<form method="POST" use:enhance class="cutout flex flex-col gap-4 p-5">
			<Field label={copy.admin.password} name="password" type="password" required />
			<SubmitButton>{copy.admin.signIn}</SubmitButton>
		</form>
	{:else}
		<p class="cutout p-5 text-ink">{copy.admin.disabled}</p>
	{/if}
</div>
