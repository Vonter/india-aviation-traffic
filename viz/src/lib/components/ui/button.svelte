<script lang="ts">
	import { cn } from '$lib/utils';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLButtonElement> {
		variant?: 'default' | 'outline' | 'ghost';
		size?: 'default' | 'sm' | 'lg';
		class?: string;
		children?: any;
		disabled?: boolean;
	}

	let {
		variant = 'default',
		size = 'default',
		class: className = '',
		children,
		...restProps
	}: Props = $props();

	const variants = {
		default: 'bg-primary text-primary-foreground hover:bg-primary/90',
		outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
		ghost: 'hover:bg-accent hover:text-accent-foreground'
	};

	const sizes = {
		default: 'h-10 px-4 py-2',
		sm: 'h-9 rounded-md px-3',
		lg: 'h-11 rounded-md px-8'
	};
</script>

<button
	class={cn(
		'inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50',
		variants[variant],
		sizes[size],
		className
	)}
	{...restProps}
>
	{@render children()}
</button>
