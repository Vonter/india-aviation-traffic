<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		domestic: boolean;
		international: boolean;
		onDomesticToggle: () => void;
		onInternationalToggle: () => void;
	}

	let { domestic, international, onDomesticToggle, onInternationalToggle }: Props = $props();
</script>

<div class="flex items-center gap-2 rounded-md bg-background">
	<button
		type="button"
		class={cn(
			'rounded px-3 py-1.5 text-sm transition-colors',
			domestic ? 'bg-gray-600 text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
		)}
		onclick={onDomesticToggle}
	>
		Domestic
	</button>
	<button
		type="button"
		class={cn(
			'rounded px-3 py-1.5 text-sm transition-colors',
			international
				? 'bg-gray-600 text-primary-foreground'
				: 'text-muted-foreground hover:bg-accent'
		)}
		onclick={onInternationalToggle}
	>
		International
	</button>
</div>
