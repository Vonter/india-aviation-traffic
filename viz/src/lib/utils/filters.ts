/**
 * Utility functions for filtering and searching data
 */

export interface SearchableItem {
	name: string;
	value?: number;
}

/**
 * Filter items by search query (case-insensitive)
 */
export function filterBySearch<T extends SearchableItem>(items: T[], searchValue: string): T[] {
	if (!searchValue.trim()) return items;
	const searchLower = searchValue.toLowerCase();
	return items.filter((item) => item.name.toLowerCase().includes(searchLower));
}

/**
 * Get airports that have both domestic and international data
 */
export function getAirportsWithBothTypes(
	domesticData: Array<{ name: string }>,
	internationalData: Array<{ name: string }>
): string[] {
	const domesticAirports = new Set(domesticData.map((d) => d.name));
	const internationalAirports = new Set(internationalData.map((d) => d.name));
	return Array.from(domesticAirports).filter((name) => internationalAirports.has(name));
}

/**
 * Get available airports based on type selection
 */
export function getAvailableAirports(
	domesticData: Array<{ name: string }>,
	internationalData: Array<{ name: string }>,
	type: 'domestic' | 'international' | 'all'
): string[] {
	if (type === 'domestic') {
		return Array.from(new Set(domesticData.map((d) => d.name)));
	} else if (type === 'international') {
		return Array.from(new Set(internationalData.map((d) => d.name)));
	} else {
		// All - airports with either type (union, not intersection)
		const domesticAirports = new Set(domesticData.map((d) => d.name));
		const internationalAirports = new Set(internationalData.map((d) => d.name));
		return Array.from(new Set([...domesticAirports, ...internationalAirports]));
	}
}
