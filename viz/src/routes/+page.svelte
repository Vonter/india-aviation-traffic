<script lang="ts">
	import { onMount } from 'svelte';
	import RidershipChart from '$lib/components/RidershipChart.svelte';
	import AirportTreeMap from '$lib/components/AirportTreeMap.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Popover from '$lib/components/ui/popover.svelte';
	import Command from '$lib/components/ui/command.svelte';
	import { ChevronsUpDown } from 'lucide-svelte';
	import SelectionPopover from '$lib/components/SelectionPopover.svelte';
	import SingleSelectionPopover from '$lib/components/SingleSelectionPopover.svelte';
	import MetricSelector from '$lib/components/MetricSelector.svelte';
	import TypeToggle from '$lib/components/TypeToggle.svelte';
	import {
		loadAirportAggregations,
		loadAirlineAggregations,
		loadAirportSorted,
		loadAirlineSorted,
		loadAirportMetadata,
		loadDailyData,
		aggregateAirportDataFromPrecalc,
		aggregateAirlineDataFromPrecalc,
		getAirportDestinations,
		aggregateDailyData,
		getDailyMetrics,
		type AggregatedData
	} from '$lib/data';
	import { filterBySearch, getAvailableAirports } from '$lib/utils/filters';
	import { getType, filterSelected, getDefaultSelection } from '$lib/utils/dataLoaders';
	import { getMetricLabel } from '$lib/utils/metrics';
	import { captureScrollPosition, restoreScrollPosition } from '$lib/utils/scroll';
	import { AIRPORT_METRICS, AIRLINE_METRICS, AIRLINE_BRAND_COLORS } from '$lib/constants/metrics';

	// Airport visualization state
	let airportData = $state<AggregatedData[]>([]);
	let allAirports = $state<string[]>([]);
	let sortedAirports = $state<Array<{ name: string; value: number }>>([]);
	let selectedAirports = $state<Set<string>>(new Set());
	let airportDomestic = $state(true);
	let airportInternational = $state(true);
	let airportMetric = $state<string>('paxTotal');
	let airportLoading = $state(false);
	let airportPopoverOpen = $state(false);
	let airportMetricPopoverOpen = $state(false);
	let airportSearchValue = $state('');

	// Pre-calculated data cache
	let airportAggregations = $state<Awaited<ReturnType<typeof loadAirportAggregations>> | null>(
		null
	);
	let airportMetadata = $state<Awaited<ReturnType<typeof loadAirportMetadata>> | null>(null);
	let airportSortedCache = $state<Awaited<ReturnType<typeof loadAirportSorted>> | null>(null);

	// Airline visualization state
	let airlineData = $state<AggregatedData[]>([]);
	let allAirlines = $state<string[]>([]);
	let sortedAirlines = $state<Array<{ name: string; value: number }>>([]);
	let selectedAirlines = $state<Set<string>>(new Set());
	let airlineDomestic = $state(true);
	let airlineInternational = $state(true);
	let airlineMetric = $state<string>('passengerNumber');
	let airlineLoading = $state(false);
	let airlinePopoverOpen = $state(false);
	let airlineMetricPopoverOpen = $state(false);
	let airlineSearchValue = $state('');

	// Pre-calculated data cache
	let airlineAggregations = $state<Awaited<ReturnType<typeof loadAirlineAggregations>> | null>(
		null
	);
	let airlineSortedCache = $state<Awaited<ReturnType<typeof loadAirlineSorted>> | null>(null);

	// TreeMap state
	let treemapData = $state<Array<{ destination: string; value: number }>>([]);
	let selectedAirport = $state<string>('');
	let allDestinations = $state<string[]>([]); // All destinations including international cities
	let treemapDomestic = $state(true);
	let treemapInternational = $state(true);
	let treemapMetric = $state<string>('paxTotal');
	let treemapYear = $state<number>(2024);
	let treemapLoading = $state(false);
	let treemapAirportPopoverOpen = $state(false);
	let treemapMetricPopoverOpen = $state(false);
	let treemapYearPopoverOpen = $state(false);
	let treemapAirportSearchValue = $state('');

	// Daily chart state
	let dailyData = $state<AggregatedData[]>([]);
	let dailyMetrics = $state<string[]>([]);
	let selectedDailyMetric = $state<string>('');
	let dailyLoading = $state(false);
	let dailyMetricPopoverOpen = $state(false);
	let pendingScrollRestore: (() => Promise<void>) | null = $state(null);

	// Track if initial load is complete to prevent effects from running on mount
	let initialLoadComplete = $state(false);

	// Responsive window width detection
	let windowWidth = $state(0);
	const isMobile = $derived(windowWidth < 640);
	const defaultSelectionCount = $derived(isMobile ? 5 : 10);

	// Load initial data
	onMount(async () => {
		// Initialize window width
		const updateWidth = () => (windowWidth = window.innerWidth);
		updateWidth();
		window.addEventListener('resize', updateWidth);
		// Load pre-calculated data first
		const [agg, metadata, sorted, airlineAgg, airlineSorted] = await Promise.all([
			loadAirportAggregations(),
			loadAirportMetadata(),
			loadAirportSorted(),
			loadAirlineAggregations(),
			loadAirlineSorted()
		]);

		airportAggregations = agg;
		airportMetadata = metadata;
		airportSortedCache = sorted;
		airlineAggregations = airlineAgg;
		airlineSortedCache = airlineSorted;

		// Load destinations for treemap dropdown
		if (metadata.destinations) {
			allDestinations = metadata.destinations;
		}

		// Initialize sortedAirports from cache immediately (if available)
		// If cache is empty, loadAirportData will generate it from aggregations
		if (sorted && airportMetric && sorted[airportMetric] && sorted[airportMetric].length > 0) {
			sortedAirports = sorted[airportMetric];
		}

		// Initialize sortedAirlines from cache immediately
		if (airlineSorted && airlineMetric) {
			sortedAirlines = airlineSorted[airlineMetric] || [];
		}

		// Load initial data
		await Promise.all([loadAirportData(), loadAirlineData(), loadDailyChartData()]);

		// Set default airport for treemap to Bengaluru
		if (!selectedAirport && allAirports.length > 0) {
			const bengaluruIndex = allAirports.findIndex(
				(a: string) =>
					a.toLowerCase().includes('bengaluru') || a.toLowerCase().includes('bangalore')
			);
			if (bengaluruIndex !== -1) {
				selectedAirport = allAirports[bengaluruIndex];
			} else if (allAirports.length > 0) {
				// Fallback to first airport if Bengaluru not found
				selectedAirport = allAirports[0];
			}
		}
		initialLoadComplete = true;

		// Cleanup resize listener
		return () => window.removeEventListener('resize', updateWidth);
	});

	// Get airport type based on toggles
	const getAirportType = () => getType(airportDomestic, airportInternational);

	// Load airport data (using pre-calculated aggregations)
	async function loadAirportData() {
		if (!airportAggregations || !airportMetadata || airportLoading) return Promise.resolve();

		airportLoading = true;
		try {
			// Get available airports - data processing already filtered to only airports with both types
			const airportType = getAirportType();
			const domesticData = airportAggregations.domestic[airportMetric] || [];
			const internationalData = airportAggregations.international[airportMetric] || [];
			const availableAirports = getAvailableAirports(domesticData, internationalData, airportType);

			// Get airports with data from metadata, or fall back to extracting from aggregations
			if (airportMetadata.airports && airportMetadata.airports.length > 0) {
				allAirports = airportMetadata.airports;
			} else {
				// Fallback: extract unique airports from aggregations
				const allAirportsSet = new Set<string>();
				domesticData.forEach((d: AggregatedData) => allAirportsSet.add(d.name));
				internationalData.forEach((d: AggregatedData) => allAirportsSet.add(d.name));
				allAirports = Array.from(allAirportsSet).sort();
			}

			// Get sorted list for current metric (from cache)
			if (
				airportSortedCache &&
				airportSortedCache[airportMetric] &&
				airportSortedCache[airportMetric].length > 0
			) {
				sortedAirports = airportSortedCache[airportMetric];
			} else {
				// Fallback: generate sorted list from aggregations data
				const totals = new Map<string, number>();

				// Sum up values for each airport from all data points
				domesticData.forEach((point: AggregatedData) => {
					const current = totals.get(point.name) || 0;
					totals.set(point.name, current + point.value);
				});
				internationalData.forEach((point: AggregatedData) => {
					const current = totals.get(point.name) || 0;
					totals.set(point.name, current + point.value);
				});

				// Convert to sorted array
				sortedAirports = Array.from(totals.entries())
					.map(([name, value]) => ({ name, value }))
					.sort((a, b) => b.value - a.value);
			}

			// Filter selected airports to only include those available
			selectedAirports = filterSelected(selectedAirports, availableAirports);

			// Get default selection (responsive count) if none selected - always set default if empty
			if (
				selectedAirports.size === 0 &&
				sortedAirports.length > 0 &&
				availableAirports.length > 0
			) {
				const defaultSelection = getDefaultSelection(
					sortedAirports,
					availableAirports,
					defaultSelectionCount
				);
				if (defaultSelection.size > 0) {
					selectedAirports = defaultSelection;
				}
			}

			// Aggregate data from pre-calculated aggregations
			airportData = aggregateAirportDataFromPrecalc(
				airportAggregations,
				selectedAirports,
				airportType,
				airportMetric
			);
		} catch (error) {
			console.error('Error loading airport data:', error);
		} finally {
			airportLoading = false;
		}
	}

	// Get airline type based on toggles
	const getAirlineType = () => getType(airlineDomestic, airlineInternational);

	// Get treemap type based on toggles
	const getTreemapType = () => getType(treemapDomestic, treemapInternational);

	// Load airline data (using pre-calculated aggregations)
	async function loadAirlineData() {
		if (!airlineAggregations || airlineLoading) return Promise.resolve();

		airlineLoading = true;
		try {
			// Filter airlines based on selected modes
			const airlineType = getAirlineType();
			let availableAirlines: string[];
			let typeData: AggregatedData[];

			if (airlineType === 'domestic') {
				// Get airlines that have domestic data
				typeData = airlineAggregations.domestic[airlineMetric] || [];
				availableAirlines = Array.from(new Set(typeData.map((d) => d.name)));
			} else if (airlineType === 'international') {
				// Get airlines that have international data
				typeData = airlineAggregations.international[airlineMetric] || [];
				availableAirlines = Array.from(new Set(typeData.map((d) => d.name)));
			} else {
				// All airlines - combine both types
				const domesticData = airlineAggregations.domestic[airlineMetric] || [];
				const internationalData = airlineAggregations.international[airlineMetric] || [];
				typeData = [...domesticData, ...internationalData];
				availableAirlines = Array.from(new Set(typeData.map((d) => d.name)));
			}

			// Generate type-specific sorted list from aggregations
			const totals = new Map<string, number>();
			typeData.forEach((point: AggregatedData) => {
				const current = totals.get(point.name) || 0;
				totals.set(point.name, current + point.value);
			});

			sortedAirlines = Array.from(totals.entries())
				.map(([name, value]) => ({ name, value }))
				.sort((a, b) => b.value - a.value);

			// Get unique airlines from sorted list
			allAirlines = sortedAirlines.map((a) => a.name);

			// Filter selected airlines to only include those available in current mode
			const filteredSelected = new Set<string>();
			for (const airline of selectedAirlines) {
				if (availableAirlines.includes(airline)) {
					filteredSelected.add(airline);
				}
			}
			selectedAirlines = filteredSelected;

			// Get default selection (responsive count) if none selected
			if (
				selectedAirlines.size === 0 &&
				sortedAirlines.length > 0 &&
				availableAirlines.length > 0
			) {
				const defaultSelection = getDefaultSelection(
					sortedAirlines,
					availableAirlines,
					defaultSelectionCount
				);
				if (defaultSelection.size > 0) {
					selectedAirlines = defaultSelection;
				}
			}

			// Aggregate data from pre-calculated aggregations
			airlineData = aggregateAirlineDataFromPrecalc(
				airlineAggregations,
				selectedAirlines,
				airlineType,
				airlineMetric
			);
		} catch (error) {
			console.error('Error loading airline data:', error);
		} finally {
			airlineLoading = false;
		}
	}

	// Load treemap data
	async function loadTreemapData() {
		// Set default to Bengaluru if not selected and airports are loaded
		if (!selectedAirport && allAirports.length > 0) {
			const bengaluruIndex = allAirports.findIndex(
				(a) => a.toLowerCase().includes('bengaluru') || a.toLowerCase().includes('bangalore')
			);
			if (bengaluruIndex !== -1) {
				selectedAirport = allAirports[bengaluruIndex];
			}
		}

		if (!selectedAirport || treemapLoading) return;
		treemapLoading = true;
		try {
			const treemapType = getTreemapType();
			treemapData = await getAirportDestinations(
				selectedAirport,
				treemapType,
				treemapMetric,
				treemapYear
			);
		} catch (error) {
			console.error('Error loading treemap data:', error);
		} finally {
			treemapLoading = false;
		}
	}

	// Load daily chart data
	async function loadDailyChartData() {
		if (dailyLoading) return Promise.resolve();
		dailyLoading = true;
		try {
			const data = await loadDailyData();
			if (!data || data.length === 0) {
				console.warn('No daily data available');
				dailyData = [];
				dailyMetrics = [];
				return;
			}

			dailyMetrics = getDailyMetrics(data);

			if (dailyMetrics.length === 0) {
				console.warn('No metrics found in daily data');
				dailyData = [];
				return;
			}

			// Default to "International (Airport Footfalls)" if not set
			if (!selectedDailyMetric) {
				const internationalFootfalls = dailyMetrics.find(
					(m) => m === 'International (Airport Footfalls)'
				);
				selectedDailyMetric = internationalFootfalls || dailyMetrics[0];
			}

			// Verify metric exists in data
			if (selectedDailyMetric && !dailyMetrics.includes(selectedDailyMetric)) {
				console.warn(`Metric ${selectedDailyMetric} not found, using first available`);
				selectedDailyMetric = dailyMetrics[0];
			}

			// Always aggregate data if metric is selected
			if (selectedDailyMetric) {
				dailyData = aggregateDailyData(data, selectedDailyMetric);
				if (dailyData.length === 0) {
					console.warn(`No data aggregated for metric ${selectedDailyMetric}`);
				}
			} else {
				dailyData = [];
			}
		} catch (error) {
			console.error('Error loading daily data:', error);
			dailyData = [];
			dailyMetrics = [];
		} finally {
			dailyLoading = false;
		}
	}

	// Debounce timers to prevent excessive calls
	let airportLoadTimer: ReturnType<typeof setTimeout> | null = null;
	let airlineLoadTimer: ReturnType<typeof setTimeout> | null = null;
	let treemapLoadTimer: ReturnType<typeof setTimeout> | null = null;
	let dailyLoadTimer: ReturnType<typeof setTimeout> | null = null;

	// Watch for changes - use reactive statements
	// Only watch toggle states and metrics, not selected sets (to avoid infinite loops)
	// Only run after initial load is complete
	$effect(() => {
		if (!initialLoadComplete || !airportAggregations) return;
		// Track dependencies to trigger reload
		airportDomestic;
		airportInternational;
		airportMetric;
		// Debounce to prevent excessive calls
		if (airportLoadTimer) clearTimeout(airportLoadTimer);
		airportLoadTimer = setTimeout(() => {
			loadAirportData();
		}, 0);
	});

	$effect(() => {
		if (!initialLoadComplete || !airlineAggregations) return;
		airlineDomestic;
		airlineInternational;
		airlineMetric;
		// Debounce to prevent excessive calls
		if (airlineLoadTimer) clearTimeout(airlineLoadTimer);
		airlineLoadTimer = setTimeout(() => {
			loadAirlineData();
		}, 0);
	});

	$effect(() => {
		if (!initialLoadComplete) return;
		selectedAirport;
		treemapDomestic;
		treemapInternational;
		treemapMetric;
		treemapYear;
		// Debounce to prevent excessive calls
		if (treemapLoadTimer) clearTimeout(treemapLoadTimer);
		treemapLoadTimer = setTimeout(() => {
			loadTreemapData();
		}, 0);
	});

	$effect(() => {
		if (!initialLoadComplete) return;
		selectedDailyMetric;
		// Always reload when metric changes, even if it's empty
		if (dailyLoadTimer) clearTimeout(dailyLoadTimer);
		dailyLoadTimer = setTimeout(() => {
			loadDailyChartData().then(async () => {
				// Restore scroll position after data loads and chart re-renders
				if (pendingScrollRestore) {
					await pendingScrollRestore();
					pendingScrollRestore = null;
				}
			});
		}, 0);
	});

	// Toggle airport selection
	function toggleAirport(airport: string) {
		// Preserve scroll position
		const scrollPosition = captureScrollPosition();

		const newSet = new Set(selectedAirports);
		if (newSet.has(airport)) {
			newSet.delete(airport);
		} else {
			newSet.add(airport);
		}
		selectedAirports = newSet;
		// Reload data when selection changes (effect will handle it, but trigger immediately for better UX)
		if (initialLoadComplete && !airportLoading) {
			// Clear any pending timer and load immediately
			if (airportLoadTimer) clearTimeout(airportLoadTimer);
			loadAirportData().then(() => restoreScrollPosition(scrollPosition));
		} else {
			// Restore scroll position after DOM updates
			restoreScrollPosition(scrollPosition);
		}
	}

	// Toggle airline selection
	function toggleAirline(airline: string) {
		// Preserve scroll position
		const scrollPosition = captureScrollPosition();

		const newSet = new Set(selectedAirlines);
		if (newSet.has(airline)) {
			newSet.delete(airline);
		} else {
			newSet.add(airline);
		}
		selectedAirlines = newSet;
		// Reload data when selection changes (effect will handle it, but trigger immediately for better UX)
		if (initialLoadComplete && !airlineLoading) {
			// Clear any pending timer and load immediately
			if (airlineLoadTimer) clearTimeout(airlineLoadTimer);
			loadAirlineData().then(() => restoreScrollPosition(scrollPosition));
		} else {
			// Restore scroll position after DOM updates
			restoreScrollPosition(scrollPosition);
		}
	}

	// Filter airports based on search
	const filteredAirports = $derived.by(() => {
		if (!sortedAirports || sortedAirports.length === 0) return [];
		return filterBySearch(sortedAirports, airportSearchValue);
	});

	// Filter airlines based on search
	const filteredAirlines = $derived.by(() => filterBySearch(sortedAirlines, airlineSearchValue));

	// Filter treemap airports based on search (include both airports and destinations)
	const filteredTreemapAirports = $derived.by(() => {
		// Combine airports and destinations for the dropdown
		const airportList = sortedAirports.length > 0 ? sortedAirports.map((a) => a.name) : allAirports;
		const combinedList = [...new Set([...airportList, ...allDestinations])];
		return filterBySearch(
			combinedList.map((name) => ({ name })),
			treemapAirportSearchValue
		).map((item) => item.name);
	});
</script>

<svelte:head>
	<title>Indian Aviation</title>
</svelte:head>

<div class="min-h-screen bg-background p-2 sm:p-4 md:p-6 lg:p-8">
	<div class="mx-auto space-y-4 sm:space-y-6 md:space-y-8">
		<!-- Header -->
		<div class="flex flex-col gap-2">
			<h1 class="text-3xl font-bold sm:text-4xl">Indian Aviation Traffic</h1>
		</div>

		<!-- Airport Visualization -->
		<Card class="border-none shadow-none">
			<div class="space-y-4 p-2 sm:p-4 md:p-6">
				<div class="flex flex-wrap items-center justify-between gap-4">
					<h2 class="text-xl font-semibold sm:text-2xl">Airports</h2>
					<div class="flex flex-wrap items-center gap-2">
						<SelectionPopover
							items={filteredAirports}
							selected={selectedAirports}
							bind:searchValue={airportSearchValue}
							placeholder="Search airports..."
							buttonText={`${selectedAirports.size} Airports`}
							onToggle={toggleAirport}
							onSearchChange={(v) => (airportSearchValue = v)}
							open={airportPopoverOpen}
						/>

						<MetricSelector
							metrics={AIRPORT_METRICS}
							selected={airportMetric}
							getLabel={(m) => getMetricLabel(m, AIRPORT_METRICS)}
							onSelect={(m) => (airportMetric = m)}
							open={airportMetricPopoverOpen}
						/>

						<TypeToggle
							domestic={airportDomestic}
							international={airportInternational}
							onDomesticToggle={() => (airportDomestic = !airportDomestic)}
							onInternationalToggle={() => (airportInternational = !airportInternational)}
						/>
					</div>
				</div>

				{#if airportLoading}
					<div
						class="flex h-[350px] items-center justify-center text-muted-foreground sm:h-[400px] md:h-[500px]"
					>
						Loading...
					</div>
				{:else if airportData.length === 0}
					<RidershipChart
						data={[]}
						placeholderText="No data available for selected airports"
						metricLabel={getMetricLabel(airportMetric, AIRPORT_METRICS)}
					/>
				{:else}
					<RidershipChart
						data={airportData}
						metricLabel={getMetricLabel(airportMetric, AIRPORT_METRICS)}
						yAxisLabel={`${getMetricLabel(airportMetric, AIRPORT_METRICS).toUpperCase()} (Quarterly)`}
						onToggle={toggleAirport}
					/>
				{/if}
			</div>
		</Card>

		<!-- Airline Visualization -->
		<Card class="border-none shadow-none">
			<div class="space-y-4 p-2 sm:p-4 md:p-6">
				<div class="flex flex-wrap items-center justify-between gap-4">
					<h2 class="text-xl font-semibold sm:text-2xl">Airlines</h2>
					<div class="flex flex-wrap items-center gap-2">
						<SelectionPopover
							items={filteredAirlines}
							selected={selectedAirlines}
							bind:searchValue={airlineSearchValue}
							placeholder="Search airlines..."
							buttonText={`${selectedAirlines.size} Airlines`}
							onToggle={toggleAirline}
							onSearchChange={(v) => (airlineSearchValue = v)}
							open={airlinePopoverOpen}
						/>

						<MetricSelector
							metrics={AIRLINE_METRICS}
							selected={airlineMetric}
							getLabel={(m) => getMetricLabel(m, AIRLINE_METRICS)}
							onSelect={(m) => (airlineMetric = m)}
							open={airlineMetricPopoverOpen}
						/>

						<TypeToggle
							domestic={airlineDomestic}
							international={airlineInternational}
							onDomesticToggle={() => (airlineDomestic = !airlineDomestic)}
							onInternationalToggle={() => (airlineInternational = !airlineInternational)}
						/>
					</div>
				</div>

				{#if airlineLoading}
					<div
						class="flex h-[350px] items-center justify-center text-muted-foreground sm:h-[400px] md:h-[500px]"
					>
						Loading...
					</div>
				{:else if airlineData.length === 0}
					<RidershipChart
						data={[]}
						placeholderText="No data available for selected airlines"
						metricLabel={getMetricLabel(airlineMetric, AIRLINE_METRICS)}
					/>
				{:else}
					<RidershipChart
						data={airlineData}
						metricLabel={getMetricLabel(airlineMetric, AIRLINE_METRICS)}
						yAxisLabel={`${getMetricLabel(airlineMetric, AIRLINE_METRICS).toUpperCase()} (Quarterly)`}
						colorMap={AIRLINE_BRAND_COLORS}
					/>
				{/if}
			</div>
		</Card>

		<!-- Airport Destination TreeMap -->
		<Card class="border-none shadow-none">
			<div class="space-y-4 p-2 sm:p-4 md:p-6">
				<div class="flex flex-wrap items-center justify-between gap-4">
					<div class="flex flex-wrap items-center gap-2">
						<h2 class="text-xl font-semibold sm:text-2xl">Airport Pairs for</h2>
						<SingleSelectionPopover
							items={filteredTreemapAirports}
							selected={selectedAirport}
							bind:searchValue={treemapAirportSearchValue}
							placeholder="Search airports..."
							buttonText={selectedAirport || 'Select Airport'}
							onSelect={(airport) => (selectedAirport = airport)}
							onSearchChange={(v) => (treemapAirportSearchValue = v)}
							open={treemapAirportPopoverOpen}
						/>
					</div>
					<div class="flex flex-wrap items-center gap-2">
						<!-- Year selector -->
						<Popover bind:open={treemapYearPopoverOpen}>
							<span slot="trigger">
								<Button variant="outline" class="h-9 min-w-[80px]">
									{treemapYear}
									<ChevronsUpDown class="ml-2 h-4 w-4 opacity-50" />
								</Button>
							</span>
							<span slot="content">
								<Command>
									<div slot="list" class="max-h-[300px] overflow-y-auto">
										{#each Array.from({ length: 2025 - 2015 + 1 }, (_, i) => 2015 + i).reverse() as year}
											<button
												type="button"
												class="relative flex w-full cursor-default items-center rounded-md px-4 py-2 text-left text-sm outline-none hover:bg-accent"
												onclick={() => {
													treemapYear = year;
													treemapYearPopoverOpen = false;
												}}
											>
												{year}
											</button>
										{/each}
									</div>
								</Command>
							</span>
						</Popover>

						<MetricSelector
							metrics={AIRPORT_METRICS}
							selected={treemapMetric}
							getLabel={(m) => getMetricLabel(m, AIRPORT_METRICS)}
							onSelect={(m) => (treemapMetric = m)}
							open={treemapMetricPopoverOpen}
						/>

						<TypeToggle
							domestic={treemapDomestic}
							international={treemapInternational}
							onDomesticToggle={() => (treemapDomestic = !treemapDomestic)}
							onInternationalToggle={() => (treemapInternational = !treemapInternational)}
						/>
					</div>
				</div>

				{#if treemapLoading}
					<div
						class="flex h-[50vh] min-h-[350px] items-center justify-center text-muted-foreground"
					>
						Loading...
					</div>
				{:else if !selectedAirport}
					<div
						class="flex h-[50vh] min-h-[350px] items-center justify-center text-muted-foreground"
					>
						Please select an airport to view destination breakdown
					</div>
				{:else if treemapData.length === 0}
					<div
						class="flex h-[50vh] min-h-[350px] items-center justify-center text-muted-foreground"
					>
						No destination data available for {selectedAirport}
					</div>
				{:else}
					<AirportTreeMap
						data={treemapData}
						metricLabel={getMetricLabel(treemapMetric, AIRPORT_METRICS)}
						onSelect={(destination) => {
							// Check if the destination is in the airports list
							if (allAirports.includes(destination)) {
								selectedAirport = destination;
							} else if (allDestinations.includes(destination)) {
								// If it's a destination (international city), set it as selected airport
								selectedAirport = destination;
							}
						}}
					/>
				{/if}
			</div>
		</Card>

		<!-- Daily Historical Chart -->
		<Card class="border-none shadow-none">
			<div class="space-y-4 p-2 sm:p-4 md:p-6">
				<div class="flex flex-wrap items-center justify-between gap-4">
					<h2 class="text-xl font-semibold sm:text-2xl">Daily Historical Data</h2>
					<div class="flex flex-wrap items-center gap-2">
						<!-- Metric selector -->
						<Popover bind:open={dailyMetricPopoverOpen}>
							<span slot="trigger">
								<Button variant="outline" class="h-9 min-w-[140px]">
									{selectedDailyMetric || 'Select Metric'}
									<ChevronsUpDown class="ml-2 h-4 w-4 opacity-50" />
								</Button>
							</span>
							<span slot="content">
								<Command>
									<div slot="list" class="max-h-[300px] overflow-y-auto">
										{#each dailyMetrics as metric}
											<button
												type="button"
												class="relative flex w-full cursor-default items-center rounded-md px-4 py-2 text-left text-sm outline-none hover:bg-accent"
												onclick={() => {
													// Preserve scroll position on mobile before changing metric
													// This will be restored after the chart data loads
													const scrollPosition = captureScrollPosition();
													pendingScrollRestore = () => restoreScrollPosition(scrollPosition);

													selectedDailyMetric = metric;
													dailyMetricPopoverOpen = false;
												}}
											>
												{metric}
											</button>
										{/each}
									</div>
								</Command>
							</span>
						</Popover>
					</div>
				</div>

				{#if dailyLoading}
					<div
						class="flex h-[350px] items-center justify-center text-muted-foreground sm:h-[400px] md:h-[500px]"
					>
						Loading...
					</div>
				{:else if !selectedDailyMetric}
					<div
						class="flex h-[350px] items-center justify-center text-muted-foreground sm:h-[400px] md:h-[500px]"
					>
						Please select a metric to view
					</div>
				{:else if dailyData.length === 0}
					<RidershipChart
						data={[]}
						placeholderText="No data available for selected metric"
						metricLabel={selectedDailyMetric}
					/>
				{:else}
					<RidershipChart data={dailyData} metricLabel={selectedDailyMetric} />
				{/if}
			</div>
		</Card>

		<!-- Footer -->
		<Card class="border-none shadow-none">
			<div class="text-center text-sm text-muted-foreground">
				<p>
					Made using <a href="https://kit.svelte.dev" target="_blank" class="underline">SvelteKit</a
					>, with assistance from
					<a href="https://anthropic.com/claude" target="_blank" class="underline">Claude</a>. Data
					and code available on
					<a
						href="https://github.com/Vonter/india-aviation-traffic"
						target="_blank"
						class="underline">GitHub</a
					>.
				</p>
			</div>
		</Card>
	</div>
</div>
