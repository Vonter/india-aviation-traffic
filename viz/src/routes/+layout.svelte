<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import SEO from '$lib/components/SEO.svelte';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<SEO />

{@render children()}
