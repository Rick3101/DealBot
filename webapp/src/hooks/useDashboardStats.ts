import { useMemo } from 'react';
import { Expedition } from '@/types/expedition';

export interface DashboardStats {
  total_expeditions: number;
  active_expeditions: number;
  completed_expeditions: number;
  overdue_expeditions: number;
}

interface TimelineData {
  stats?: DashboardStats;
  timeline?: any[];
}

/**
 * Custom hook to calculate dashboard statistics with fallback logic
 *
 * @param expeditions - Array of expeditions to calculate stats from
 * @param timelineData - Optional timeline data that may contain pre-calculated stats
 * @returns Dashboard statistics object
 */
export function useDashboardStats(
  expeditions: Expedition[],
  timelineData: TimelineData | null
): DashboardStats {
  return useMemo(() => {
    // Use timeline stats if available, otherwise calculate from expeditions
    if (timelineData?.stats) {
      return timelineData.stats;
    }

    // Fallback calculation from expeditions array
    return {
      total_expeditions: expeditions.length,
      active_expeditions: expeditions.filter(e => e.status === 'active').length,
      completed_expeditions: expeditions.filter(e => e.status === 'completed').length,
      overdue_expeditions: 0, // Will be calculated from timeline data when available
    };
  }, [expeditions, timelineData]);
}
