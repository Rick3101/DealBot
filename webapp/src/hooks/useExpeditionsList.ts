import { useState, useCallback, useRef } from 'react';
import { Expedition } from '@/types/expedition';
import { expeditionService } from '@/services/api/expeditionService';

interface UseExpeditionsListOptions {
  initialLoad?: boolean;
}

interface UseExpeditionsListReturn {
  expeditions: Expedition[];
  loading: boolean;
  error: string | null;
  refreshing: boolean;
  fetchExpeditions: (showLoading?: boolean) => Promise<void>;
  setExpeditions: React.Dispatch<React.SetStateAction<Expedition[]>>;
}

/**
 * Hook for managing expedition list fetching and state
 * Single Responsibility: List data management
 */
export const useExpeditionsList = (
  options: UseExpeditionsListOptions = {}
): UseExpeditionsListReturn => {
  const { initialLoad = true } = options;

  const [expeditions, setExpeditions] = useState<Expedition[]>([]);
  const [loading, setLoading] = useState(initialLoad);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mountedRef = useRef(true);

  const fetchExpeditions = useCallback(async (showLoading = true) => {
    console.log('[useExpeditionsList] fetchExpeditions called, showLoading:', showLoading);
    try {
      if (showLoading) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError(null);

      console.log('[useExpeditionsList] Calling expeditionService.getAll()');
      const data = await expeditionService.getAll();
      console.log('[useExpeditionsList] Received data:', data?.length, 'expeditions');

      if (mountedRef.current) {
        setExpeditions(data);
      }
    } catch (err) {
      console.error('[useExpeditionsList] Failed to fetch expeditions:', err);
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to load expeditions');
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  return {
    expeditions,
    loading,
    error,
    refreshing,
    fetchExpeditions,
    setExpeditions,
  };
};
