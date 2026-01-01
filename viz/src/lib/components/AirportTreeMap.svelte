<script lang="ts">
	import { onMount } from 'svelte';
	import { hierarchy, treemap } from 'd3-hierarchy';
	import { Plot, Rect, Text } from 'svelteplot';

	interface DestinationData {
		destination: string;
		value: number;
	}

	interface Props {
		data: DestinationData[];
		metricLabel?: string;
		onSelect?: (destination: string) => void;
	}

	let { data, metricLabel = 'Ridership', onSelect }: Props = $props();
	let containerEl: HTMLElement | null = $state(null);
	let containerWidth = $state(1200);
	let containerHeight = $state(600);
	let activeNode: any | null = $state(null);
	let isPinned = $state(false);
	let isMobile = $state(false);

	// Generate random light colors for each item
	const generateColor = (seed: string): string => {
		let hash = 0;
		for (let i = 0; i < seed.length; i++) {
			hash = seed.charCodeAt(i) + ((hash << 5) - hash);
		}
		const hue = Math.abs(hash) % 360;
		const saturation = 30 + (Math.abs(hash) % 30);
		const lightness = 75 + (Math.abs(hash) % 20);
		return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
	};

	// Helper: Get browser locale with fallback
	const getLocale = (): string => {
		if (typeof navigator !== 'undefined' && navigator.language) {
			return navigator.language;
		}
		return 'en-US';
	};

	// Format numbers using Intl API
	const formatCompactNumber = (value: number): string => {
		return new Intl.NumberFormat(getLocale(), {
			notation: 'compact',
			maximumFractionDigits: 1
		}).format(value);
	};

	onMount(() => {
		const checkMobile = () => {
			isMobile = window.innerWidth < 768;
		};
		checkMobile();
		window.addEventListener('resize', checkMobile);

		if (!containerEl) return;
		const observer = new ResizeObserver(([entry]) => {
			containerWidth = entry.contentRect.width;
			containerHeight = entry.contentRect.height || 600;
		});
		observer.observe(containerEl);
		return () => {
			observer.disconnect();
			window.removeEventListener('resize', checkMobile);
		};
	});

	// Prepare data for treemap
	const treemapData = $derived.by(() => {
		if (!data || data.length === 0) return [];
		const limited = data.slice(0, 100);
		return limited
			.filter((d) => d.destination && d.destination.trim() !== '' && d.value != null && d.value > 0)
			.map((d) => ({
				name: String(d.destination),
				value: Number(d.value),
				color: generateColor(String(d.destination))
			}));
	});

	// Calculate treemap layout
	const treemapLayout = $derived.by(() => {
		const currentData = treemapData;
		if (!currentData || currentData.length === 0) {
			return { data: [], x1: 'x1', y1: 'y1', x2: 'x2', y2: 'y2', maxCellSize: 0 };
		}

		const root = hierarchy({ children: currentData }).sum((d: any) => d.value || 0);
		const totalValue = root.value || 1;

		const layout = treemap().size([containerWidth, containerHeight]).padding(2);
		layout(root);

		const layoutData = root.leaves().map((d: any) => {
			const fillColor = d.data.color;
			const percentage = (d.data.value / totalValue) * 100;
			const width = d.x1 - d.x0;
			const height = d.y1 - d.y0;
			const cellSize = Math.min(width, height);

			return {
				x1: d.x0,
				y1: d.y0,
				x2: d.x1,
				y2: d.y1,
				name: d.data.name,
				value: d.data.value,
				percentage,
				fillColor,
				cellSize
			};
		});

		const maxCellSize =
			layoutData.length > 0 ? Math.max(...layoutData.map((d: any) => d.cellSize)) : 0;

		return {
			data: layoutData,
			x1: 'x1',
			y1: 'y1',
			x2: 'x2',
			y2: 'y2',
			maxCellSize
		};
	});

	// Hit testing
	function hitTest(x: number, y: number) {
		const layoutData = treemapLayout.data;
		if (layoutData.length === 0) return null;

		const plotY = containerHeight - y;
		return (
			layoutData.find((n: any) => x >= n.x1 && x <= n.x2 && plotY >= n.y1 && plotY <= n.y2) || null
		);
	}

	function handlePointerMove(event: PointerEvent) {
		if (isPinned || !containerEl) return;
		const rect = containerEl.getBoundingClientRect();
		activeNode = hitTest(event.clientX - rect.left, event.clientY - rect.top);
	}

	function handleClick(event: MouseEvent) {
		if (!containerEl) return;
		const rect = containerEl.getBoundingClientRect();
		const hit = hitTest(event.clientX - rect.left, event.clientY - rect.top);

		if (isPinned && activeNode && hit && activeNode.name === hit.name) {
			isPinned = false;
			activeNode = null;
		} else if (hit) {
			isPinned = true;
			activeNode = hit;
			if (onSelect) {
				onSelect(hit.name);
			}
		} else {
			isPinned = false;
			activeNode = null;
		}
	}
</script>

<div class="w-full overflow-auto" style="height: 70vh;" bind:this={containerEl}>
	{#if data && data.length > 0 && treemapData.length > 0}
		<div class="relative min-w-0">
			<Plot
				width={containerWidth}
				height={containerHeight}
				x={{ domain: [0, containerWidth] }}
				y={{ domain: [0, containerHeight] }}
				marginLeft={0}
				marginRight={0}
				marginBottom={0}
				marginTop={0}
			>
				<Rect
					data={treemapLayout.data}
					x1={treemapLayout.x1}
					y1={treemapLayout.y1}
					x2={treemapLayout.x2}
					y2={treemapLayout.y2}
					fill={(d: any) => d.fillColor}
					stroke="#ffffff"
					strokeWidth={0.5}
				/>

				<Text
					data={treemapLayout.data}
					x={(d: any) => (d.x1 + d.x2) / 2}
					y={(d: any) => (d.y1 + d.y2) / 2}
					text={(d: any) => {
						const width = d.x2 - d.x1;
						const height = d.y2 - d.y1;
						const name = d.name;
						const value = d.value;
						const padding = isMobile ? 6 : 12;
						const availableWidth = Math.max(0, width - padding * 2);
						const availableHeight = Math.max(0, height - padding * 2);

						if (availableWidth <= 0 || availableHeight <= 0) {
							return '';
						}

						const valueText = formatCompactNumber(value);
						const charWidthRatio = 0.6;
						const lineHeightRatio = 1.2;
						const minFontSize = isMobile ? 3 : 6;
						const maxFontSize = isMobile ? 16 : 20;

						const cellSize = Math.min(width, height);
						const maxCellSize = treemapLayout.maxCellSize;

						let fontSize: number;
						if (maxCellSize > 0) {
							const sizeRatio = cellSize / maxCellSize;
							fontSize = minFontSize + (maxFontSize - minFontSize) * sizeRatio;
						} else {
							fontSize = maxFontSize;
						}

						const valueWidthEstimate = valueText.length * charWidthRatio;
						const maxNameWidth = availableWidth;

						const fontSizeByHeight = availableHeight / (2 * lineHeightRatio);

						let fontSizeByWidth: number;
						if (name.length > valueText.length) {
							fontSizeByWidth = availableWidth / (name.length * charWidthRatio);
						} else {
							fontSizeByWidth = availableWidth / (valueText.length * charWidthRatio);
						}

						let maxFittingFontSize = Math.min(fontSizeByWidth, fontSizeByHeight);
						fontSize = Math.min(fontSize, maxFittingFontSize);
						fontSize = Math.max(minFontSize, Math.min(maxFontSize, fontSize));

						const charWidth = fontSize * charWidthRatio;
						const lineHeight = fontSize * lineHeightRatio;
						const nameWidth = name.length * charWidth;
						const valueWidth = valueText.length * charWidth;

						if (
							Math.max(nameWidth, valueWidth) <= availableWidth &&
							lineHeight * 2 <= availableHeight
						) {
							return `${name}\n${valueText}`;
						}

						const maxCharsForName = Math.floor(availableWidth / charWidth) - 1;

						if (
							maxCharsForName >= 2 &&
							valueWidth <= availableWidth &&
							lineHeight * 2 <= availableHeight
						) {
							let truncatedName: string;
							if (name.length > maxCharsForName) {
								const truncateTo = Math.max(1, maxCharsForName - 3);
								truncatedName = name.substring(0, truncateTo) + '...';
							} else {
								truncatedName = name;
							}

							const truncatedWidth = truncatedName.length * charWidth;
							if (Math.max(truncatedWidth, valueWidth) <= availableWidth) {
								return `${truncatedName}\n${valueText}`;
							}
						}

						return valueText;
					}}
					fontSize={(d: any) => {
						const width = d.x2 - d.x1;
						const height = d.y2 - d.y1;
						const padding = isMobile ? 6 : 12;
						const availableWidth = Math.max(0, width - padding * 2);
						const availableHeight = Math.max(0, height - padding * 2);

						if (availableWidth <= 0 || availableHeight <= 0) {
							return isMobile ? 3 : 6;
						}

						const name = d.name;
						const valueText = formatCompactNumber(d.value);
						const charWidthRatio = 0.6;
						const lineHeightRatio = 1.2;
						const minFontSize = isMobile ? 3 : 6;
						const maxFontSize = isMobile ? 16 : 20;

						const cellSize = Math.min(width, height);
						const maxCellSize = treemapLayout.maxCellSize;

						let fontSize: number;
						if (maxCellSize > 0) {
							const sizeRatio = cellSize / maxCellSize;
							fontSize = minFontSize + (maxFontSize - minFontSize) * sizeRatio;
						} else {
							fontSize = maxFontSize;
						}

						const fontSizeByHeight = availableHeight / (2 * lineHeightRatio);
						const maxTextLength = Math.max(name.length, valueText.length);
						const fontSizeByWidth = availableWidth / (maxTextLength * charWidthRatio);

						let maxFittingFontSize = Math.min(fontSizeByWidth, fontSizeByHeight);
						fontSize = Math.min(fontSize, maxFittingFontSize);
						fontSize = Math.max(minFontSize, Math.min(maxFontSize, fontSize));

						return fontSize;
					}}
					fontWeight="bold"
					strokeWidth={2}
					strokeLinejoin="round"
					stroke="rgba(255,255,255,0.8)"
					fill="#000000"
					filter={(d: any) => {
						const width = d.x2 - d.x1;
						const height = d.y2 - d.y1;
						const padding = isMobile ? 6 : 12;
						const availableWidth = width - padding * 2;
						const availableHeight = height - padding * 2;
						return availableWidth > 0 && availableHeight > 0;
					}}
				/>
			</Plot>

			<!-- Invisible overlay for interactions -->
			<div
				class="absolute inset-0 cursor-pointer touch-manipulation"
				onpointermove={handlePointerMove}
				onpointerleave={() => !isPinned && (activeNode = null)}
				onclick={handleClick}
				role="figure"
				tabindex="0"
			></div>
		</div>
	{:else}
		<div class="flex h-96 items-center justify-center text-muted-foreground">No data available</div>
	{/if}
</div>
