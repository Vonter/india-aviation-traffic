<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import Popover from '$lib/components/ui/popover.svelte';
	import Command from '$lib/components/ui/command.svelte';
	import { ChevronsUpDown, Check } from 'lucide-svelte';

	interface Props {
		items: string[];
		selected: string;
		searchValue: string;
		placeholder?: string;
		buttonText?: string;
		onSelect: (name: string) => void;
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
		onSelect,
		onSearchChange,
		onClose,
		open
	}: Props = $props();
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
			{buttonText || selected || 'Select'}
			<ChevronsUpDown class="ml-2 h-4 w-4 opacity-50" />
		</Button>
	</span>
	<span slot="content">
		<Command bind:searchValue>
			<div slot="input" class="border-b px-3 py-2">
				<input
					type="text"
					{placeholder}
					class="w-full bg-transparent outline-none placeholder:text-muted-foreground"
					bind:value={searchValue}
					onclick={(e) => e.stopPropagation()}
				/>
			</div>
			<div slot="list" class="max-h-[300px] overflow-y-auto">
				{#each items as item}
					{@const isSelected = selected === item}
					<button
						type="button"
						class="relative flex w-full cursor-default items-center rounded-md px-4 py-2 text-left text-sm outline-none hover:bg-accent"
						onclick={() => {
							onSelect(item);
							open = false;
						}}
					>
						<div class="flex items-center gap-2">
							{#if isSelected}
								<Check class="h-4 w-4" />
							{:else}
								<div class="h-4 w-4" />
							{/if}
							<span>{item}</span>
						</div>
					</button>
				{/each}
			</div>
		</Command>
	</span>
</Popover>
