import { useEffect, useRef, useCallback } from 'react';

interface UseAutoRefreshOptions {
  enabled?: boolean;
  interval?: number; // milliseconds
  onRefresh: () => void | Promise<void>;
}

/**
 * Hook for automatic interval-based refresh functionality
 * Single Responsibility: Auto-refresh timer management
 * Reusable across any component that needs periodic updates
 */
export const useAutoRefresh = (options: UseAutoRefreshOptions): void => {
  const { enabled = true, interval = 30000, onRefresh } = options;

  const intervalRef = useRef<number | null>(null);
  const mountedRef = useRef(true);
  const onRefreshRef = useRef(onRefresh);

  // Keep onRefresh reference up to date
  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);

  const refresh = useCallback(() => {
    if (mountedRef.current) {
      onRefreshRef.current();
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    intervalRef.current = window.setInterval(refresh, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, interval, refresh]);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);
};
