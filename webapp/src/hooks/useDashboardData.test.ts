import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDashboardData } from './useDashboardData';
import { dashboardService } from '@/services/api/dashboardService';

vi.mock('@/services/api/dashboardService');

describe('useDashboardData', () => {
  const mockTimelineData = {
    upcoming: [
      {
        id: 1,
        name: 'Test Expedition',
        deadline: '2025-12-31',
        status: 'active',
        daysRemaining: 90,
      },
    ],
    overdue: [],
  };

  const mockAnalytics = {
    totalExpeditions: 10,
    activeExpeditions: 5,
    completedExpeditions: 3,
    totalProfit: 1000,
    averageCompletionTime: 15,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with null data', () => {
    const { result } = renderHook(() => useDashboardData());

    expect(result.current.timelineData).toBeNull();
    expect(result.current.analytics).toBeNull();
    expect(result.current.timelineLoading).toBe(false);
    expect(result.current.analyticsLoading).toBe(false);
  });

  it('should fetch timeline data successfully', async () => {
    vi.mocked(dashboardService.getTimeline).mockResolvedValue(mockTimelineData);

    const { result } = renderHook(() => useDashboardData());

    await result.current.fetchTimeline();

    await waitFor(() => {
      expect(result.current.timelineData).toEqual(mockTimelineData);
      expect(result.current.timelineLoading).toBe(false);
    });
  });

  it('should fetch analytics data successfully', async () => {
    vi.mocked(dashboardService.getAnalytics).mockResolvedValue(mockAnalytics);

    const { result } = renderHook(() => useDashboardData());

    await result.current.fetchAnalytics();

    await waitFor(() => {
      expect(result.current.analytics).toEqual(mockAnalytics);
      expect(result.current.analyticsLoading).toBe(false);
    });
  });

  it('should set loading states during fetch', async () => {
    vi.mocked(dashboardService.getTimeline).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockTimelineData), 100))
    );
    vi.mocked(dashboardService.getAnalytics).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockAnalytics), 100))
    );

    const { result } = renderHook(() => useDashboardData());

    const timelinePromise = result.current.fetchTimeline();
    const analyticsPromise = result.current.fetchAnalytics();

    // Wait a tick for state to update
    await waitFor(() => {
      expect(result.current.timelineLoading || result.current.analyticsLoading).toBe(true);
    });

    await Promise.all([timelinePromise, analyticsPromise]);

    await waitFor(() => {
      expect(result.current.timelineLoading).toBe(false);
      expect(result.current.analyticsLoading).toBe(false);
    });
  });

  it('should handle timeline fetch errors gracefully', async () => {
    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.mocked(dashboardService.getTimeline).mockRejectedValue(
      new Error('Network error')
    );

    const { result } = renderHook(() => useDashboardData());

    await result.current.fetchTimeline();

    await waitFor(() => {
      expect(result.current.timelineLoading).toBe(false);
      expect(result.current.timelineData).toBeNull();
      expect(consoleWarnSpy).toHaveBeenCalled();
    });

    consoleWarnSpy.mockRestore();
  });

  it('should handle analytics fetch errors gracefully', async () => {
    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.mocked(dashboardService.getAnalytics).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useDashboardData());

    await result.current.fetchAnalytics();

    await waitFor(() => {
      expect(result.current.analyticsLoading).toBe(false);
      expect(result.current.analytics).toBeNull();
      expect(consoleWarnSpy).toHaveBeenCalled();
    });

    consoleWarnSpy.mockRestore();
  });

  it('should refresh both timeline and analytics with refreshDashboard', async () => {
    vi.mocked(dashboardService.getTimeline).mockResolvedValue(mockTimelineData);
    vi.mocked(dashboardService.getAnalytics).mockResolvedValue(mockAnalytics);

    const { result } = renderHook(() => useDashboardData());

    await result.current.refreshDashboard();

    await waitFor(() => {
      expect(result.current.timelineData).toEqual(mockTimelineData);
      expect(result.current.analytics).toEqual(mockAnalytics);
      expect(result.current.timelineLoading).toBe(false);
      expect(result.current.analyticsLoading).toBe(false);
    });
  });

  it('should fetch timeline and analytics in parallel with refreshDashboard', async () => {
    const timelineSpy = vi
      .mocked(dashboardService.getTimeline)
      .mockResolvedValue(mockTimelineData);
    const analyticsSpy = vi
      .mocked(dashboardService.getAnalytics)
      .mockResolvedValue(mockAnalytics);

    const { result } = renderHook(() => useDashboardData());

    await result.current.refreshDashboard();

    expect(timelineSpy).toHaveBeenCalledTimes(1);
    expect(analyticsSpy).toHaveBeenCalledTimes(1);
  });
});
