import { useMemo } from 'react';
import { Expedition, ExpeditionTimelineEntry } from '@/types/expedition';

interface TimelineData {
  stats?: any;
  timeline?: ExpeditionTimelineEntry[];
}

/**
 * Custom hook to transform expedition data for timeline display
 *
 * @param expeditions - Array of base expeditions
 * @param timelineData - Optional timeline data with pre-transformed entries
 * @returns Array of expedition timeline entries with progress and overdue status
 */
export function useTimelineExpeditions(
  expeditions: Expedition[],
  timelineData: TimelineData | null
): ExpeditionTimelineEntry[] {
  return useMemo(() => {
    // Use timeline data if available
    if (timelineData?.timeline) {
      return timelineData.timeline;
    }

    // Transform expeditions with overdue detection and default progress
    return expeditions.map(exp => ({
      ...exp,
      is_overdue: exp.deadline
        ? new Date(exp.deadline) < new Date() && exp.status === 'active'
        : false,
      progress: {
        completion_percentage: 0,
        total_items: 0,
        consumed_items: 0,
        remaining_items: 0,
        total_value: 0,
        consumed_value: 0,
        remaining_value: 0,
      },
    })) as ExpeditionTimelineEntry[];
  }, [expeditions, timelineData]);
}
