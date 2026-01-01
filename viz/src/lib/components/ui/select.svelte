<script lang="ts">
	import { cn } from '$lib/utils';
	import type { HTMLAttributes, HTMLSelectAttributes } from 'svelte/elements';

	interface Props extends HTMLSelectAttributes {
		class?: string;
		items: Array<{ value: string; label: string }>;
	}

	let { class: className = '', items, ...restProps }: Props = $props();
</script>

<select
	class={cn(
		'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50',
		className
	)}
	{...restProps}
>
	{#each items as item}
		<option value={item.value}>{item.label}</option>
	{/each}
</select>
