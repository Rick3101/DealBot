import { useEffect, useCallback } from 'react';
import {
  Expedition,
  CreateExpeditionRequest,
  TimelineData,
  AnalyticsData,
} from '@/types/expedition';
import { useExpeditionsList } from './useExpeditionsList';
import { useExpeditionCRUD } from './useExpeditionCRUD';
import { useDashboardData } from './useDashboardData';
import { useAutoRefresh } from './useAutoRefresh';
import { useExpeditionRealTime } from './useExpeditionRealTime';

interface UseExpeditionsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  realTimeUpdates?: boolean;
}

interface UseExpeditionsReturn {
  expeditions: Expedition[];
  timelineData: TimelineData | null;
  analytics: AnalyticsData | null;
  loading: boolean;
  error: string | null;
  refreshing: boolean;

  // Actions
  refreshExpeditions: () => Promise<void>;
  createExpedition: (data: CreateExpeditionRequest) => Promise<Expedition | null>;
  updateExpeditionStatus: (id: number, status: string) => Promise<boolean>;
  deleteExpedition: (id: number) => Promise<boolean>;

  // Timeline and analytics
  refreshTimeline: () => Promise<void>;
  refreshAnalytics: () => Promise<void>;
}

/**
 * Main expedition hook - composes focused hooks for complete functionality
 * This hook orchestrates:
 * - List management (useExpeditionsList)
 * - CRUD operations (useExpeditionCRUD)
 * - Dashboard data (useDashboardData)
 * - Auto-refresh (useAutoRefresh)
 * - Real-time updates (useExpeditionRealTime)
 */
export const useExpeditions = (options: UseExpeditionsOptions = {}): UseExpeditionsReturn => {
  const {
    autoRefresh = true,
    refreshInterval = 30000, // 30 seconds
    realTimeUpdates = true,
  } = options;

  // Hook 1: Expedition list management
  const {
    expeditions,
    loading,
    error: listError,
    refreshing,
    fetchExpeditions,
    setExpeditions,
  } = useExpeditionsList({ initialLoad: true });

  // Hook 2: CRUD operations
  const {
    error: crudError,
    createExpedition: createExpeditionAPI,
    updateExpeditionStatus: updateExpeditionStatusAPI,
    deleteExpedition: deleteExpeditionAPI,
  } = useExpeditionCRUD({
    onSuccess: () => {
      // Refresh dashboard data after mutations
      fetchTimeline();
      fetchAnalytics();
    },
  });

  // Hook 3: Dashboard data (timeline & analytics)
  const {
    timelineData,
    analytics,
    fetchTimeline,
    fetchAnalytics,
    refreshDashboard,
  } = useDashboardData();

  // Combine errors from list and CRUD
  const error = listError || crudError;

  // Refresh all data
  const refreshExpeditions = useCallback(async () => {
    await Promise.all([
      fetchExpeditions(false),
      refreshDashboard(),
    ]);
  }, [fetchExpeditions, refreshDashboard]);

  // Hook 4: Auto-refresh functionality
  useAutoRefresh({
    enabled: autoRefresh,
    interval: refreshInterval,
    onRefresh: refreshExpeditions,
  });

  // Hook 5: Real-time WebSocket updates
  useExpeditionRealTime({
    enabled: realTimeUpdates,
    onExpeditionUpdate: (data) => {
      // Refresh expeditions on any update
      fetchExpeditions(false);

      // Refresh dashboard for significant changes
      if (data.type === 'EXPEDITION_COMPLETED' || data.type === 'EXPEDITION_CREATED') {
        refreshDashboard();
      }
    },
    onItemConsumed: () => {
      // Refresh to get updated progress
      fetchExpeditions(false);
      fetchAnalytics();
    },
    onExpeditionCompleted: () => {
      fetchExpeditions(false);
      refreshDashboard();
    },
    onExpeditionCreated: () => {
      fetchExpeditions(false);
      refreshDashboard();
    },
  });

  // Initial data fetch
  useEffect(() => {
    // Fetch expeditions first (critical data)
    fetchExpeditions();

    // Fetch timeline and analytics in the background (non-blocking)
    setTimeout(() => {
      fetchTimeline();
      fetchAnalytics();
    }, 100);
  }, [fetchExpeditions, fetchTimeline, fetchAnalytics]);

  // Wrapped CRUD operations with local state updates
  const createExpedition = useCallback(
    async (data: CreateExpeditionRequest): Promise<Expedition | null> => {
      const newExpedition = await createExpeditionAPI(data);

      if (newExpedition) {
        setExpeditions((prev) => [newExpedition, ...prev]);
      }

      return newExpedition;
    },
    [createExpeditionAPI, setExpeditions]
  );

  const updateExpeditionStatus = useCallback(
    async (id: number, status: string): Promise<boolean> => {
      const updatedExpedition = await updateExpeditionStatusAPI(id, status);

      if (updatedExpedition) {
        setExpeditions((prev) =>
          prev.map((exp) => (exp.id === id ? updatedExpedition : exp))
        );
        return true;
      }

      return false;
    },
    [updateExpeditionStatusAPI, setExpeditions]
  );

  const deleteExpedition = useCallback(
    async (id: number): Promise<boolean> => {
      const success = await deleteExpeditionAPI(id);

      if (success) {
        setExpeditions((prev) => prev.filter((exp) => exp.id !== id));
      }

      return success;
    },
    [deleteExpeditionAPI, setExpeditions]
  );

  return {
    expeditions,
    timelineData,
    analytics,
    loading,
    error,
    refreshing,

    // Actions
    refreshExpeditions,
    createExpedition,
    updateExpeditionStatus,
    deleteExpedition,

    // Individual refresh methods
    refreshTimeline: fetchTimeline,
    refreshAnalytics: fetchAnalytics,
  };
};