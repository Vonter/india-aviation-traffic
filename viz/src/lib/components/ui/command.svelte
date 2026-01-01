<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		searchValue?: string;
	}

	let { class: className = '', searchValue = $bindable('') }: Props = $props();
</script>

<div
	class={cn(
		'bg-popover text-popover-foreground flex h-full w-full flex-col overflow-hidden rounded-md',
		className
	)}
>
	<slot name="input" {searchValue} />
	<slot name="list" {searchValue} />
</div>
