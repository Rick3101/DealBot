import { useState, useCallback, useRef } from 'react';
import { TimelineData, AnalyticsData } from '@/types/expedition';
import { dashboardService } from '@/services/api/dashboardService';

interface UseDashboardDataReturn {
  timelineData: TimelineData | null;
  analytics: AnalyticsData | null;
  timelineLoading: boolean;
  analyticsLoading: boolean;
  fetchTimeline: () => Promise<void>;
  fetchAnalytics: () => Promise<void>;
  refreshDashboard: () => Promise<void>;
}

/**
 * Hook for managing dashboard data (timeline and analytics)
 * Single Responsibility: Dashboard-specific data management
 */
export const useDashboardData = (): UseDashboardDataReturn => {
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  const mountedRef = useRef(true);

  const fetchTimeline = useCallback(async () => {
    try {
      setTimelineLoading(true);
      const data = await dashboardService.getTimeline();

      if (mountedRef.current) {
        setTimelineData(data);
      }
    } catch (err) {
      console.warn('Timeline data unavailable (optional):', err);
      // Don't throw - this is optional data
    } finally {
      if (mountedRef.current) {
        setTimelineLoading(false);
      }
    }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      setAnalyticsLoading(true);
      const data = await dashboardService.getAnalytics();

      if (mountedRef.current) {
        setAnalytics(data);
      }
    } catch (err) {
      console.warn('Analytics data unavailable (optional):', err);
      // Don't throw - this is optional data
    } finally {
      if (mountedRef.current) {
        setAnalyticsLoading(false);
      }
    }
  }, []);

  const refreshDashboard = useCallback(async () => {
    await Promise.all([fetchTimeline(), fetchAnalytics()]);
  }, [fetchTimeline, fetchAnalytics]);

  return {
    timelineData,
    analytics,
    timelineLoading,
    analyticsLoading,
    fetchTimeline,
    fetchAnalytics,
    refreshDashboard,
  };
};
