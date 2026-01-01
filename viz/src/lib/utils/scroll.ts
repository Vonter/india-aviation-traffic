import { tick } from 'svelte';

/**
 * Captures the current scroll position
 * @returns The current scroll position {x, y}
 */
export function captureScrollPosition(): { x: number; y: number } {
	return {
		x: window.scrollX,
		y: window.scrollY
	};
}

/**
 * Restores scroll position after DOM updates.
 * Uses Svelte's tick() to wait for all pending DOM updates, which is more
 * efficient and idiomatic than double requestAnimationFrame.
 *
 * @param position - The scroll position to restore
 * @param afterPromise - Optional promise to wait for before restoring (e.g., data loading)
 */
export async function restoreScrollPosition(
	position: { x: number; y: number },
	afterPromise?: Promise<void>
): Promise<void> {
	if (afterPromise) {
		await afterPromise;
	}
	// Wait for all pending DOM updates
	await tick();
	// Restore scroll position
	window.scrollTo(position.x, position.y);
}

/**
 * Creates a scroll preservation handler that can be used with async operations.
 * Returns a function that should be called after the async operation completes.
 *
 * @example
 * const preserveScroll = createScrollPreserver();
 * await loadData();
 * await preserveScroll();
 */
export function createScrollPreserver(): () => Promise<void> {
	const position = captureScrollPosition();
	return () => restoreScrollPosition(position);
}
