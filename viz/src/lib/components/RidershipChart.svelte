<script lang="ts">
	import { Plot, Line } from 'svelteplot';
	import type { AggregatedData } from '../data';
	import { onMount } from 'svelte';

	// Constants
	const BREAKPOINTS = { mobile: 640, tablet: 1024 } as const;
	const HOVER_OPACITY = { active: 1, dimmed: 0.2, legend: 0.3 };
	const LINE_WIDTH = { default: 2, hovered: 4 };

	type SeriesData = { name: string; data: AggregatedData[]; color: string };
	type DataSegment = { data: AggregatedData[] };
	type Tooltip = { x: number; y: number; name: string; date: Date; value: number };

	let {
		data,
		placeholderText,
		metricLabel = 'Ridership',
		yAxisLabel,
		colorMap,
		onToggle
	}: {
		data: AggregatedData[];
		placeholderText?: string;
		metricLabel?: string;
		yAxisLabel?: string;
		colorMap?: Map<string, string> | Record<string, string>;
		onToggle?: (name: string) => void;
	} = $props();

	let windowWidth = $state(0);
	let hoveredSeries = $state<string | null>(null);
	let tooltip = $state<Tooltip | null>(null);
	let chartContainer: HTMLDivElement | undefined = $state();
	let containerWidth = $state(1200);
	let showTotal = $state(false);

	onMount(() => {
		const updateWidth = () => (windowWidth = window.innerWidth);
		updateWidth();
		window.addEventListener('resize', updateWidth);
		return () => window.removeEventListener('resize', updateWidth);
	});

	// Observe container width changes when container becomes available
	$effect(() => {
		if (!chartContainer) return;

		// Initialize width from container
		containerWidth = chartContainer.getBoundingClientRect().width;

		const observer = new ResizeObserver((entries) => {
			for (const entry of entries) {
				containerWidth = entry.contentRect.width;
			}
		});
		observer.observe(chartContainer);

		return () => {
			observer.disconnect();
		};
	});

	// Helper: Get browser locale with fallback
	const getLocale = (): string => {
		if (typeof navigator !== 'undefined' && navigator.language) {
			return navigator.language;
		}
		return 'en-US';
	};

	// Helper: Format compact numbers using Intl API
	const formatCompactNumber = (value: number): string => {
		return new Intl.NumberFormat(getLocale(), {
			notation: 'compact',
			maximumFractionDigits: 1
		}).format(value);
	};

	// Helper: Detect gaps and split data into segments
	const splitDataIntoSegments = (data: AggregatedData[]): DataSegment[] => {
		if (data.length === 0) return [];

		const sorted = [...data].sort((a, b) => a.period.getTime() - b.period.getTime());
		const segments: DataSegment[] = [];
		let currentSegment: AggregatedData[] = [sorted[0]];

		// Detect data frequency (daily, monthly, quarterly, or yearly)
		let dataFrequency: 'daily' | 'monthly' | 'quarterly' | 'yearly' | 'unknown' = 'unknown';
		if (sorted.length >= 2) {
			const firstGap = sorted[1].period.getTime() - sorted[0].period.getTime();
			const days = firstGap / (24 * 60 * 60 * 1000);

			// Check if data appears to be daily (0.5-2.5 days between points)
			if (days >= 0.5 && days <= 2.5) {
				dataFrequency = 'daily';
			} else if (days >= 85 && days <= 100) {
				dataFrequency = 'quarterly';
			} else if (days >= 25 && days <= 35) {
				dataFrequency = 'monthly';
			} else if (days >= 360 && days <= 370) {
				dataFrequency = 'yearly';
			}
		}

		for (let i = 1; i < sorted.length; i++) {
			const timeDiff = sorted[i].period.getTime() - sorted[i - 1].period.getTime();
			const days = timeDiff / (24 * 60 * 60 * 1000);

			// Adjust gap threshold based on data frequency
			let gapThreshold: number;
			if (dataFrequency === 'daily') {
				// For daily data, allow up to ~3 days between points
				gapThreshold = 3 * 24 * 60 * 60 * 1000; // ~3 days
			} else if (dataFrequency === 'quarterly') {
				// For quarterly data, allow up to ~100 days (one quarter + buffer)
				gapThreshold = 180 * 24 * 60 * 60 * 1000; // ~6 months
			} else if (dataFrequency === 'monthly') {
				// For monthly data, allow up to ~35 days
				gapThreshold = 60 * 24 * 60 * 60 * 1000; // ~2 months
			} else if (dataFrequency === 'yearly') {
				// For yearly data, allow up to ~370 days
				gapThreshold = 400 * 24 * 60 * 60 * 1000; // ~13 months
			} else {
				// Default: use a conservative threshold
				gapThreshold = 120 * 24 * 60 * 60 * 1000; // ~4 months
			}

			// Check if this is an expected gap for the data frequency
			const isExpectedGap =
				(dataFrequency === 'daily' && days >= 0.5 && days <= 2.5) ||
				(dataFrequency === 'quarterly' && days >= 85 && days <= 100) ||
				(dataFrequency === 'monthly' && days >= 25 && days <= 35) ||
				(dataFrequency === 'yearly' && days >= 360 && days <= 370);

			if (timeDiff > gapThreshold && !isExpectedGap) {
				segments.push({ data: currentSegment });
				currentSegment = [sorted[i]];
			} else {
				currentSegment.push(sorted[i]);
			}
		}

		if (currentSegment.length > 0) {
			segments.push({ data: currentSegment });
		}

		return segments;
	};

	// Format date for display
	const formatDate = (date: Date): string => {
		const year = date.getFullYear();
		return year.toString();
	};

	// Format date as quarter (e.g., "Q1 2024")
	const formatQuarter = (date: Date): string => {
		const year = date.getUTCFullYear();
		const month = date.getUTCMonth(); // 0-11
		const quarter = Math.floor(month / 3) + 1; // 1-4
		return `Q${quarter} ${year}`;
	};

	// Generate colors for series
	const generateColor = (seed: string, index: number): string => {
		// Check if there's a brand color for this name
		if (colorMap) {
			const brandColor =
				colorMap instanceof Map ? colorMap.get(seed) : (colorMap as Record<string, string>)[seed];
			if (brandColor) {
				return brandColor;
			}
		}

		// Fallback to default colors
		const colors = [
			'#3b82f6', // blue
			'#ef4444', // red
			'#10b981', // green
			'#f59e0b', // amber
			'#8b5cf6', // purple
			'#ec4899', // pink
			'#06b6d4', // cyan
			'#84cc16', // lime
			'#f97316', // orange
			'#6366f1' // indigo
		];
		return colors[index % colors.length];
	};

	// Calculate cutoff date (first day of the quarter before the most recent quarter)
	const getCutoffDate = (): Date => {
		const now = new Date();
		const quarter = Math.floor(now.getMonth() / 3) - 1;
		const firstDayOfQuarter = new Date(now.getFullYear(), quarter * 3, 1);
		const cutoff = new Date(firstDayOfQuarter.setDate(firstDayOfQuarter.getDate()));
		return cutoff;
	};

	const cutoffDate = getCutoffDate();

	// Detect if data is daily (for daily data, we don't apply the cutoff filter)
	const isDailyData = $derived.by(() => {
		if (!data.length || data.length < 2) return false;
		const sorted = [...data].sort((a, b) => a.period.getTime() - b.period.getTime());
		// Check first few gaps to determine if it's daily data
		for (let i = 1; i < Math.min(10, sorted.length); i++) {
			const gap = sorted[i].period.getTime() - sorted[i - 1].period.getTime();
			const days = gap / (24 * 60 * 60 * 1000);
			// If gaps are consistently 1-2 days, it's daily data
			if (days >= 0.5 && days <= 2.5) {
				return true;
			}
		}
		return false;
	});

	// Filter data to only include points up to 9 months before current month
	// Skip cutoff for daily data
	const filteredData = $derived.by(() => {
		if (!data.length) return [];
		if (isDailyData) {
			// For daily data, show all data (no cutoff)
			return data;
		}
		return data.filter((d) => d.period.getTime() <= cutoffDate.getTime());
	});

	// Global time range for accurate mouse-to-time mapping
	const timeRange = $derived.by(() => {
		if (!filteredData.length) return { min: 0, max: 0 };
		const times = filteredData.map((d) => d.period.getTime());
		return { min: Math.min(...times), max: Math.max(...times) };
	});

	// Find closest data point to mouse position
	const findClosestPoint = (event: MouseEvent, seriesData: AggregatedData[]) => {
		if (!chartContainer || !seriesData.length) return null;

		// Use requestAnimationFrame to ensure we get stable measurements
		const rect = chartContainer.getBoundingClientRect();
		const chartWidth = rect.width;
		// Calculate relative position using viewport coordinates (clientX/clientY are viewport-relative)
		const relativeX = event.clientX - rect.left;

		// Ensure we have valid dimensions
		if (chartWidth <= 0) return null;

		// Map mouse X to time value using GLOBAL time range
		const mouseTime = timeRange.min + (relativeX / chartWidth) * (timeRange.max - timeRange.min);

		// Find nearest point in this series - ensure data is sorted by time
		const sortedData = [...seriesData].sort((a, b) => a.period.getTime() - b.period.getTime());

		// Use explicit initial value to ensure correct comparison
		let closest = sortedData[0];
		let closestDistance = Math.abs(closest.period.getTime() - mouseTime);

		for (const point of sortedData) {
			const distance = Math.abs(point.period.getTime() - mouseTime);
			if (distance < closestDistance) {
				closest = point;
				closestDistance = distance;
			}
		}

		return closest;
	};

	// Interaction handlers
	const handleHover = (seriesName: string) => (hoveredSeries = seriesName);
	const handleLeave = () => ((hoveredSeries = null), (tooltip = null));
	const handleMove = (e: MouseEvent, name: string) => {
		const series = seriesMap.get(name);
		if (!series) return;
		// Use requestAnimationFrame to ensure stable positioning during scroll
		requestAnimationFrame(() => {
			const point = findClosestPoint(e, series.data);
			if (point) {
				tooltip = { x: e.clientX, y: e.clientY, name, date: point.period, value: point.value };
			}
		});
	};

	// Apply 7-day rolling average for smoothing on mobile
	const applyRollingAverage = (
		data: AggregatedData[],
		windowSize: number = 7
	): AggregatedData[] => {
		if (data.length === 0) return [];

		const sorted = [...data].sort((a, b) => a.period.getTime() - b.period.getTime());
		const smoothed: AggregatedData[] = [];

		for (let i = 0; i < sorted.length; i++) {
			// Calculate window bounds (centered on current point)
			const halfWindow = Math.floor(windowSize / 2);
			const start = Math.max(0, i - halfWindow);
			const end = Math.min(sorted.length - 1, i + halfWindow);

			// Calculate average value in window
			let sum = 0;
			let count = 0;
			for (let j = start; j <= end; j++) {
				sum += sorted[j].value;
				count++;
			}

			// Create smoothed data point with same period
			smoothed.push({
				...sorted[i],
				value: sum / count
			});
		}

		return smoothed;
	};

	// Process and group data by series (using filtered data)
	const series = $derived.by((): SeriesData[] => {
		if (!filteredData.length) return [];

		const grouped = new Map<string, AggregatedData[]>();

		for (const item of filteredData) {
			const name = item.name || 'Unknown';
			const items = grouped.get(name) ?? [];
			if (!grouped.has(name)) grouped.set(name, items);
			items.push(item);
		}

		// Convert to array and assign colors
		return Array.from(grouped.entries()).map(([name, items], index) => {
			// Sort data by time
			const sortedData = items.sort((a, b) => a.period.getTime() - b.period.getTime());

			// Apply 7-day rolling average on mobile for daily data
			let processedData = sortedData;
			if (isMobile && isDailyData && sortedData.length > 7) {
				processedData = applyRollingAverage(sortedData, 7);
			}

			return {
				name,
				data: processedData,
				color: generateColor(name, index)
			};
		});
	});

	// Create map for quick lookup
	const seriesMap = $derived.by(() => {
		const map = new Map<string, SeriesData>();
		for (const s of series) {
			map.set(s.name, s);
		}
		return map;
	});

	// Filter visible series and sort by total value (descending)
	const visibleSeries = $derived.by(() => {
		const filtered = series.filter((s) => s.name !== 'Total' || showTotal);
		// Sort by total value in descending order
		return filtered.sort((a, b) => {
			const totalA = a.data.reduce((sum, d) => sum + d.value, 0);
			const totalB = b.data.reduce((sum, d) => sum + d.value, 0);
			return totalB - totalA;
		});
	});

	// Chart dimensions
	const isMobile = $derived(windowWidth < BREAKPOINTS.mobile);

	const chartDimensions = $derived.by(() => {
		const height = 500;
		// Use container width, with a minimum of 300px for very small screens
		const width = Math.max(300, containerWidth);

		return {
			width,
			height
		};
	});

	// Prepare segments for each series
	const seriesWithSegments = $derived.by(() => {
		return visibleSeries.map((s) => ({
			...s,
			segments: splitDataIntoSegments(s.data)
		}));
	});

	// Calculate unique years for x-axis ticks
	const uniqueYears = $derived.by(() => {
		if (!filteredData.length) return [];
		const years = new Set<number>();
		filteredData.forEach((d) => {
			years.add(d.period.getFullYear());
		});
		return Array.from(years)
			.sort()
			.map((year) => new Date(year, 0, 1));
	});

	// Build x-axis configuration with unique year ticks
	const xAxisConfig = $derived.by(() => {
		const baseConfig: any = {
			type: 'time',
			label: 'Year',
			tickRotate: 0,
			tickFormat: (d: any) => formatDate(d instanceof Date ? d : new Date(d))
		};
		if (uniqueYears.length > 0) {
			baseConfig.ticks = uniqueYears;
		}
		return baseConfig;
	});
</script>

{#if placeholderText}
	<div
		class="flex items-center justify-center rounded-lg border border-gray-200 bg-card p-2 shadow-sm sm:p-4 md:p-6"
		style:height="{chartDimensions.height}px"
	>
		<div class="px-2 text-center text-sm text-muted-foreground sm:px-4 sm:text-base md:text-lg">
			{placeholderText}
		</div>
	</div>
{:else}
	<div class="space-y-4 rounded-lg border border-gray-200 bg-card p-2 shadow-sm sm:p-4 md:p-6">
		<div class="flex items-start justify-between gap-2 px-2 py-2">
			<!-- Total Toggle Button -->
			{#if series.some((s) => s.name === 'Total')}
				<button
					onclick={() => (showTotal = !showTotal)}
					title={showTotal ? 'Hide Total' : 'Show Total'}
					class="rounded p-1.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
					aria-label={showTotal ? 'Hide Total' : 'Show Total'}
				>
					<svg
						class="h-4 w-4 transition-opacity"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						style:opacity={showTotal ? '1' : '0.3'}
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M7 4h10M7 4L12 12M7 4v0M12 12L7 20M12 12l0 0M7 20h10"
						/>
					</svg>
				</button>
			{/if}
		</div>

		<!-- Chart -->
		<div
			bind:this={chartContainer}
			class="relative w-full"
			style:height="{chartDimensions.height}px"
			role="presentation"
		>
			{#key showTotal}
				<Plot
					{...chartDimensions}
					x={xAxisConfig}
					y={{
						label: yAxisLabel || (metricLabel ? metricLabel.toUpperCase() : 'VALUE'),
						grid: true,
						zero: true,
						tickFormat: (d: any) => formatCompactNumber(d)
					}}
				>
					{#each seriesWithSegments as { name, color, segments } (name)}
						{@const isActive = hoveredSeries === name}
						{@const lineOpacity =
							hoveredSeries === null || isActive ? HOVER_OPACITY.active : HOVER_OPACITY.dimmed}
						{@const lineWidth = isActive ? LINE_WIDTH.hovered : LINE_WIDTH.default}
						{#each segments as segment, segIdx (`${name}-seg-${segIdx}`)}
							<Line
								data={segment.data as any}
								x="period"
								y="value"
								stroke={color}
								strokeWidth={lineWidth}
								opacity={lineOpacity}
								onmouseenter={() => handleHover(name)}
								onmousemove={(e: MouseEvent) => handleMove(e, name)}
								onmouseleave={handleLeave}
								style="cursor: default; transition: stroke-width 0.2s, opacity 0.2s;"
							/>
						{/each}
					{/each}
				</Plot>
			{/key}

			<!-- Tooltip -->
			{#if tooltip}
				{@const color = seriesMap.get(tooltip.name)?.color || 'white'}
				<div
					class="pointer-events-none fixed z-50 rounded-lg bg-gray-900 px-3 py-2 text-sm text-white shadow-lg"
					style:left="{tooltip.x + 15}px"
					style:top="{tooltip.y - 15}px"
					role="tooltip"
				>
					<div class="font-semibold">{tooltip.name}</div>
					<div class="mt-0.5 text-xs text-gray-300">{formatQuarter(tooltip.date)}</div>
					<div class="mt-1">{formatCompactNumber(Math.round(tooltip.value))}</div>
				</div>
			{/if}
		</div>

		<!-- Legend -->
		{#if visibleSeries.length > 1}
			{@const hasHover = hoveredSeries !== null}
			<div class="flex flex-wrap justify-center gap-3 border-t border-gray-200 px-2 pt-2">
				{#each visibleSeries as { name, color } (name)}
					{@const isHovered = hoveredSeries === name}
					{@const legendOpacity =
						hasHover && !isHovered ? HOVER_OPACITY.legend : HOVER_OPACITY.active}
					{@const lineLength = isHovered ? '40px' : '32px'}
					{@const textColor = isHovered ? color : '#374151'}
					{@const fontWeight = isHovered ? 600 : 400}
					<button
						class="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm transition-all hover:bg-gray-50"
						onmouseenter={() => handleHover(name)}
						onmouseleave={handleLeave}
						onclick={() => onToggle?.(name)}
						style:opacity={legendOpacity}
					>
						<div
							class="h-0.5 rounded transition-all"
							style:background-color={color}
							style:width={lineLength}
						></div>
						<span class="transition-all" style:color={textColor} style:font-weight={fontWeight}>
							{name}
						</span>
					</button>
				{/each}
			</div>
		{/if}
	</div>
{/if}
