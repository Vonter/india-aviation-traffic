<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import Popover from '$lib/components/ui/popover.svelte';
	import Command from '$lib/components/ui/command.svelte';
	import { ChevronsUpDown, Check } from 'lucide-svelte';

	interface Item {
		name: string;
		value?: number;
	}

	interface Props {
		items: Item[];
		selected: Set<string>;
		searchValue: string;
		placeholder?: string;
		buttonText?: string;
		onToggle: (name: string) => void;
		onSearchChange: (value: string) => void;
		onClose?: () => void;
		open: boolean;
	}

	let {
		items,
		selected,
		searchValue = $bindable(''),
		placeholder = 'Search...',
		buttonText,
		onToggle,
		onSearchChange,
		onClose,
		open
	}: Props = $props();

	const getButtonText = () => {
		if (buttonText) return buttonText;
		if (selected.size === 0) return 'Choose';
		if (selected.size === 1) return '1 Selected';
		return `${selected.size} Selected`;
	};
</script>

<Popover
	bind:open
	onclose={() => {
		onClose?.();
		onSearchChange('');
	}}
>
	<span slot="trigger">
		<Button variant="outline" class="h-9 min-w-[120px]">
			{getButtonText()}
			<ChevronsUpDown class="ml-2 h-4 w-4 opacity-50" />
		</Button>
	</span>
	<span slot="content">
		<Command bind:searchValue>
			<div slot="input" class="border-b border-foreground/10 px-3 py-2">
				<input
					type="text"
					{placeholder}
					class="w-full bg-transparent outline-none placeholder:text-muted-foreground"
					bind:value={searchValue}
					onclick={(e) => e.stopPropagation()}
				/>
			</div>
			<div slot="list" class="max-h-[300px] overflow-y-auto">
				{#each items as item (item.name)}
					{@const isSelected = selected.has(item.name)}
					<button
						type="button"
						class="relative flex w-full cursor-default items-center rounded-md px-4 py-2 text-left text-sm outline-none hover:bg-accent"
						onclick={() => onToggle(item.name)}
					>
						<div class="flex items-center gap-2">
							{#if isSelected}
								<Check class="h-4 w-4" />
							{:else}
								<div class="h-4 w-4" />
							{/if}
							<span>{item.name}</span>
						</div>
					</button>
				{/each}
			</div>
		</Command>
	</span>
</Popover>
