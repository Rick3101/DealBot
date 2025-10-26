import { useState, useCallback } from 'react';
import { NavigateFunction } from 'react-router-dom';
import { ExpeditionTimelineEntry } from '@/types/expedition';
import { hapticFeedback } from '@/utils/telegram';

export interface DashboardActions {
  handleRefresh: () => Promise<void>;
  handleCreateExpedition: () => void;
  handleViewExpedition: (expedition: ExpeditionTimelineEntry) => void;
  handleManageExpedition: (expedition: ExpeditionTimelineEntry) => void;
  refreshing: boolean;
}

/**
 * Custom hook to centralize all dashboard action handlers
 *
 * @param navigate - React Router navigate function
 * @param refreshExpeditions - Function to refresh expedition data
 * @returns Object containing all action handlers and loading state
 */
export function useDashboardActions(
  navigate: NavigateFunction,
  refreshExpeditions: () => Promise<void>
): DashboardActions {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    console.log('[Dashboard] Refresh button clicked');
    setRefreshing(true);
    hapticFeedback('light');
    try {
      console.log('[Dashboard] Calling refreshExpeditions...');
      await refreshExpeditions();
      console.log('[Dashboard] Refresh complete');
    } catch (error) {
      console.error('[Dashboard] Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  }, [refreshExpeditions]);

  const handleCreateExpedition = useCallback(() => {
    hapticFeedback('medium');
    navigate('/expedition/create');
  }, [navigate]);

  const handleViewExpedition = useCallback((expedition: ExpeditionTimelineEntry) => {
    hapticFeedback('light');
    navigate(`/expedition/${expedition.id}`);
  }, [navigate]);

  const handleManageExpedition = useCallback((expedition: ExpeditionTimelineEntry) => {
    hapticFeedback('medium');
    navigate(`/expedition/${expedition.id}`);
  }, [navigate]);

  return {
    handleRefresh,
    handleCreateExpedition,
    handleViewExpedition,
    handleManageExpedition,
    refreshing,
  };
}
