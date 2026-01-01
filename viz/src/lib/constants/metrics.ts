/**
 * Metric definitions for airports and airlines
 */

export const AIRPORT_METRICS = [
	{ value: 'paxTotal', label: 'Passenger Ridership' },
	{ value: 'paxTo', label: 'Passengers To' },
	{ value: 'paxFrom', label: 'Passengers From' },
	{ value: 'freightTotal', label: 'Freight Total' },
	{ value: 'freightTo', label: 'Freight To' },
	{ value: 'freightFrom', label: 'Freight From' },
	{ value: 'mailTotal', label: 'Mail Total' }
] as const;

export const AIRLINE_METRICS = [
	{ value: 'passengerNumber', label: 'Passenger Number' },
	{ value: 'paxTotal', label: 'Passengers Total' },
	{ value: 'paxTo', label: 'Passengers To' },
	{ value: 'paxFrom', label: 'Passengers From' },
	{ value: 'aircraftNumber', label: 'Aircraft Number' },
	{ value: 'aircraftHours', label: 'Aircraft Hours' },
	{ value: 'passengerLoadFactor', label: 'Passenger Load Factor' },
	{ value: 'freightTotal', label: 'Freight Total' }
] as const;

export const AIRLINE_BRAND_COLORS: Record<string, string> = {
	// Domestic airlines
	INDIGO: '#483D8B',
	'AIR INDIA': '#E00122',
	VISTARA: '#601848',
	'JET LITE': '#FF0000',
	'GO FIRST': '#FF6600',
	'ALLIANCE AIR': '#00BFFF',
	SPICEJET: '#FF9900',
	'AKASA AIR': '#000080',
	'AIR ASIA INDIA': '#FFCC00',
	'JET AIRWAYS': '#0066CC',
	// International airlines
	'AIR INDIA EXPRESS': '#FF0000',
	'EMIRATES AIRLINE': '#008EEF',
	'ETIHAD AIRLINES': '#C8102E',
	'QATAR AIRWAYS': '#00B9FF',
	'AIR ARABIA': '#FF6600'
};
