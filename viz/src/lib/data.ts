/**
 * Data loading utilities for aviation traffic data
 * Uses pre-calculated aggregations for optimal performance
 */

export interface DailyDataPoint {
	date: string;
	[key: string]: string | number;
}

export interface AggregatedData {
	period: Date;
	name: string;
	value: number;
	avgRidership?: number;
}

// Cache for loaded data
const dataCache = new Map<string, any>();

async function loadJsonFile<T>(path: string): Promise<T> {
	if (dataCache.has(path)) {
		return dataCache.get(path);
	}

	const response = await fetch(path);
	if (!response.ok) {
		throw new Error(`Failed to load ${path}: ${response.statusText}`);
	}

	const data = await response.json();
	dataCache.set(path, data);
	return data;
}

/**
 * Load daily data
 */
export async function loadDailyData(): Promise<DailyDataPoint[]> {
	return loadJsonFile<DailyDataPoint[]>('/data/daily.json');
}

/**
 * Load pre-calculated airport aggregations
 */
export async function loadAirportAggregations(): Promise<{
	domestic: Record<string, AggregatedData[]>;
	international: Record<string, AggregatedData[]>;
	all: Record<string, AggregatedData[]>;
}> {
	const data = await loadJsonFile<any>('/data/airport-aggregations.json');
	// Convert period strings to Date objects
	const convert = (arr: any[]) => {
		return arr.map((item) => ({
			...item,
			period: new Date(item.period)
		}));
	};
	return {
		domestic: Object.fromEntries(
			Object.entries(data.domestic).map(([k, v]) => [k, convert(v as any[])])
		),
		international: Object.fromEntries(
			Object.entries(data.international).map(([k, v]) => [k, convert(v as any[])])
		),
		all: Object.fromEntries(Object.entries(data.all).map(([k, v]) => [k, convert(v as any[])]))
	};
}

/**
 * Load pre-calculated airline aggregations
 */
export async function loadAirlineAggregations(): Promise<{
	domestic: Record<string, AggregatedData[]>;
	international: Record<string, AggregatedData[]>;
	all: Record<string, AggregatedData[]>;
}> {
	const data = await loadJsonFile<any>('/data/airline-aggregations.json');
	// Convert period strings to Date objects
	const convert = (arr: any[]) => {
		return arr.map((item) => ({
			...item,
			period: new Date(item.period)
		}));
	};
	return {
		domestic: Object.fromEntries(
			Object.entries(data.domestic).map(([k, v]) => [k, convert(v as any[])])
		),
		international: Object.fromEntries(
			Object.entries(data.international).map(([k, v]) => [k, convert(v as any[])])
		),
		all: Object.fromEntries(Object.entries(data.all).map(([k, v]) => [k, convert(v as any[])]))
	};
}

/**
 * Load pre-calculated airport sorted lists
 */
export async function loadAirportSorted(): Promise<
	Record<string, Array<{ name: string; value: number }>>
> {
	return loadJsonFile<Record<string, Array<{ name: string; value: number }>>>(
		'/data/airport-sorted.json'
	);
}

/**
 * Load pre-calculated airline sorted lists
 */
export async function loadAirlineSorted(): Promise<
	Record<string, Array<{ name: string; value: number }>>
> {
	return loadJsonFile<Record<string, Array<{ name: string; value: number }>>>(
		'/data/airline-sorted.json'
	);
}

/**
 * Load airport metadata (airports with data, years, metrics, destinations)
 */
export async function loadAirportMetadata(): Promise<{
	airports: string[];
	destinations?: string[];
	years: number[];
	metrics: string[];
}> {
	return loadJsonFile<{
		airports: string[];
		destinations?: string[];
		years: number[];
		metrics: string[];
	}>('/data/airport-metadata.json');
}

/**
 * Load pre-calculated airport destinations
 */
export async function loadAirportDestinationsPrecalc(): Promise<
	Record<
		string,
		Record<number, Record<string, Record<string, Array<{ destination: string; value: number }>>>>
	>
> {
	return loadJsonFile<any>('/data/airport-destinations.json');
}

// Removed unused utility functions - using pre-calculated sorted lists and metadata instead

/**
 * Aggregate airport data by time period (using pre-calculated data)
 */
export function aggregateAirportDataFromPrecalc(
	aggregations: {
		domestic: Record<string, AggregatedData[]>;
		international: Record<string, AggregatedData[]>;
		all: Record<string, AggregatedData[]>;
	},
	selectedAirports: Set<string>,
	type: 'domestic' | 'international' | 'all',
	metric: string = 'paxTotal'
): AggregatedData[] {
	const typeData = aggregations[type];
	const metricData = typeData[metric] || [];

	// Filter by selected airports
	return metricData.filter((point) => selectedAirports.has(point.name));
}

/**
 * Aggregate airline data by time period (using pre-calculated data)
 */
export function aggregateAirlineDataFromPrecalc(
	aggregations: {
		domestic: Record<string, AggregatedData[]>;
		international: Record<string, AggregatedData[]>;
		all: Record<string, AggregatedData[]>;
	},
	selectedAirlines: Set<string>,
	type: 'domestic' | 'international' | 'all',
	metric: string = 'passengerNumber'
): AggregatedData[] {
	const typeData = aggregations[type];
	const metricData = typeData[metric] || [];

	// Filter by selected airlines
	return metricData.filter((point) => selectedAirlines.has(point.name));
}

/**
 * Get destination breakdown for an airport (using pre-calculated data)
 * If the selected item is a destination (not an airport), performs reverse lookup
 */
export async function getAirportDestinations(
	airport: string,
	type: 'domestic' | 'international' | 'all',
	metric: string = 'paxTotal',
	year?: number
): Promise<Array<{ destination: string; value: number }>> {
	const destinations = await loadAirportDestinationsPrecalc();
	const defaultYear = year || 2025;
	// Convert year to string since JSON keys are strings
	const yearKey = String(defaultYear);

	// Check if this is an airport (exists as a key in destinations)
	const airportData = destinations[airport as keyof typeof destinations] as
		| Record<string, Record<string, Record<string, Array<{ destination: string; value: number }>>>>
		| undefined;
	if (airportData?.[yearKey]?.[type]?.[metric]) {
		// It's an airport, return its destinations
		return airportData[yearKey][type][metric];
	}

	// It's a destination, perform reverse lookup - find all airports that have this destination
	const reverseResults = new Map<string, number>();

	for (const [originAirport, airportYears] of Object.entries(destinations)) {
		const originData = airportYears as Record<
			string,
			Record<string, Record<string, Array<{ destination: string; value: number }>>>
		>;
		if (originData[yearKey]?.[type]?.[metric]) {
			for (const destEntry of originData[yearKey][type][metric]) {
				if (destEntry.destination === airport) {
					// Found a route to this destination, aggregate by origin airport
					const current = reverseResults.get(originAirport) || 0;
					reverseResults.set(originAirport, current + destEntry.value);
				}
			}
		}
	}

	// Convert to array format (treating origin airports as "destinations" for display)
	return Array.from(reverseResults.entries())
		.map(([destination, value]) => ({ destination, value }))
		.sort((a, b) => b.value - a.value);
}

/**
 * Aggregate daily data by date
 */
export function aggregateDailyData(data: DailyDataPoint[], metric: string): AggregatedData[] {
	return data
		.map((point) => {
			const value = point[metric];
			const numValue = typeof value === 'number' ? value : parseFloat(String(value)) || 0;
			return {
				period: new Date(point.date),
				name: 'Daily Data',
				value: numValue,
				avgRidership: numValue
			};
		})
		.filter((point) => !isNaN(point.period.getTime()) && !isNaN(point.value))
		.sort((a, b) => a.period.getTime() - b.period.getTime());
}

/**
 * Get available metrics from daily data
 */
export function getDailyMetrics(data: DailyDataPoint[]): string[] {
	if (data.length === 0) return [];
	return Object.keys(data[0]).filter((key) => key !== 'date');
}
