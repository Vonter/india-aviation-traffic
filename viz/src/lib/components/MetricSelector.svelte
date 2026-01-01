<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import Popover from '$lib/components/ui/popover.svelte';
	import Command from '$lib/components/ui/command.svelte';
	import { ChevronsUpDown } from 'lucide-svelte';

	interface Metric {
		value: string;
		label: string;
	}

	interface Props {
		metrics: Metric[];
		selected: string;
		getLabel: (metric: string) => string;
		onSelect: (metric: string) => void;
		open: boolean;
	}

	let { metrics, selected, getLabel, onSelect, open }: Props = $props();
</script>

<Popover bind:open>
	<span slot="trigger">
		<Button variant="outline" class="h-9 min-w-[140px]">
			{getLabel(selected)}
			<ChevronsUpDown class="ml-2 h-4 w-4 opacity-50" />
		</Button>
	</span>
	<span slot="content">
		<Command>
			<div slot="list">
				{#each metrics as metric (metric.value)}
					<button
						type="button"
						class="relative flex w-full cursor-default items-center rounded-md px-4 py-3 text-left text-sm outline-none hover:bg-accent"
						onclick={() => {
							onSelect(metric.value);
							open = false;
						}}
					>
						{metric.label}
					</button>
				{/each}
			</div>
		</Command>
	</span>
</Popover>
