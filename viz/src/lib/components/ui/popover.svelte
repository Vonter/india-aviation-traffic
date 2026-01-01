<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		open?: boolean;
		contentClass?: string;
	}

	let { open = $bindable(false), contentClass = '' }: Props = $props();

	let contentElement: HTMLElement | null = $state(null);
	let triggerElement: HTMLElement | null = $state(null);
	let isPositioned = $state(false);

	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (
			contentElement &&
			!contentElement.contains(target) &&
			triggerElement &&
			!triggerElement.contains(target)
		) {
			open = false;
		}
	}

	function updatePosition() {
		if (!contentElement || !triggerElement) return;

		const triggerRect = triggerElement.getBoundingClientRect();
		const contentRect = contentElement.getBoundingClientRect();
		const viewportWidth = window.innerWidth;
		const viewportHeight = window.innerHeight;

		// Position below the trigger by default
		let top = triggerRect.bottom + 4;
		let left = triggerRect.left;

		// Adjust if it would overflow right
		if (left + contentRect.width > viewportWidth) {
			left = viewportWidth - contentRect.width - 8;
		}

		// Adjust if it would overflow left
		if (left < 8) {
			left = 8;
		}

		// If it would overflow bottom, position above instead
		if (top + contentRect.height > viewportHeight - 8) {
			top = triggerRect.top - contentRect.height - 4;
		}

		contentElement.style.position = 'fixed';
		contentElement.style.top = `${top}px`;
		contentElement.style.left = `${left}px`;
	}

	$effect(() => {
		if (open) {
			document.addEventListener('click', handleClickOutside);
			// Update position when opened and on resize/scroll
			setTimeout(updatePosition, 0);
			window.addEventListener('resize', updatePosition);
			window.addEventListener('scroll', updatePosition, true);
			return () => {
				document.removeEventListener('click', handleClickOutside);
				window.removeEventListener('resize', updatePosition);
				window.removeEventListener('scroll', updatePosition, true);
			};
		}
	});

	$effect(() => {
		if (open && contentElement) {
			updatePosition();
		}
	});
</script>

<div
	bind:this={triggerElement}
	class="relative inline-flex items-center"
	onclick={() => (open = !open)}
	role="button"
	tabindex="0"
	onkeydown={(e) => {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			open = !open;
		}
	}}
>
	<slot name="trigger" {open} />
</div>

{#if open}
	<div
		bind:this={contentElement}
		class={cn(
			'text-popover-foreground z-50 rounded-md bg-white p-0 shadow-md outline-none',
			contentClass
		)}
	>
		<slot name="content" />
	</div>
{/if}
