/**
 * Utility functions for loading and processing data
 */

import type { AggregatedData } from '$lib/data';
import { getAvailableAirports } from './filters';

export interface DataLoaderConfig {
	domestic: boolean;
	international: boolean;
	metric: string;
	selected: Set<string>;
	aggregations: {
		domestic: Record<string, AggregatedData[]>;
		international: Record<string, AggregatedData[]>;
		all: Record<string, AggregatedData[]>;
	};
	sortedCache: Array<{ name: string; value: number }> | null;
}

/**
 * Get type based on domestic/international toggles
 */
export function getType(
	domestic: boolean,
	international: boolean
): 'domestic' | 'international' | 'all' {
	if (domestic && international) return 'all';
	if (domestic) return 'domestic';
	if (international) return 'international';
	return 'all';
}

/**
 * Filter selected items to only include available ones
 */
export function filterSelected(selected: Set<string>, available: string[]): Set<string> {
	const filtered = new Set<string>();
	for (const item of selected) {
		if (available.includes(item)) {
			filtered.add(item);
		}
	}
	return filtered;
}

/**
 * Get default selection (top N items)
 */
export function getDefaultSelection(
	sorted: Array<{ name: string; value: number }>,
	available: string[],
	count: number = 10
): Set<string> {
	if (sorted.length === 0) return new Set();
	const top = sorted
		.slice(0, count)
		.filter((a) => available.includes(a.name))
		.map((a) => a.name);
	return new Set(top);
}
