/**
 * Utility functions for working with metrics
 */

export interface Metric {
	value: string;
	label: string;
}

/**
 * Get metric label from value
 */
export function getMetricLabel(metric: string, metrics: readonly Metric[]): string {
	return metrics.find((m) => m.value === metric)?.label || metric;
}
