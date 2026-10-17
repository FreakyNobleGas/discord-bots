<script lang="ts">
	interface Props {
		label: string;
		name: string;
		value?: string | number | null;
		type?: 'text' | 'number' | 'url' | 'date' | 'datetime-local' | 'password';
		required?: boolean;
		placeholder?: string;
		hint?: string;
		/** Render a textarea with this many rows */
		rows?: number;
		maxlength?: number;
		class?: string;
	}

	let {
		label,
		name,
		value = '',
		type = 'text',
		required = false,
		placeholder,
		hint,
		rows,
		maxlength,
		class: klass = ''
	}: Props = $props();

	const id = $props.id();
</script>

<div class={['flex flex-col gap-1', klass]}>
	<label for={id} class="text-sm font-semibold text-ink-2">
		{label}{#if required}<span aria-hidden="true"> *</span>{/if}
	</label>
	{#if rows}
		<textarea
			{id}
			{name}
			{rows}
			{required}
			{placeholder}
			{maxlength}
			aria-describedby={hint ? `${id}-hint` : undefined}
			class="rounded-md border-2 border-outline bg-paper px-2 py-1.5 text-ink"
			>{value ?? ''}</textarea
		>
	{:else}
		<input
			{id}
			{name}
			{type}
			{required}
			{placeholder}
			{maxlength}
			value={value ?? ''}
			aria-describedby={hint ? `${id}-hint` : undefined}
			class="rounded-md border-2 border-outline bg-paper px-2 py-1.5 text-ink"
		/>
	{/if}
	{#if hint}<p id="{id}-hint" class="text-xs text-muted">{hint}</p>{/if}
</div>
