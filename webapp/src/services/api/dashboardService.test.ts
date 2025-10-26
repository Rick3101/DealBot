/**
 * Tests for Dashboard Service
 *
 * Tests dashboard timeline, analytics, and overdue expeditions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { dashboardService, DashboardService } from './dashboardService';
import { httpClient } from './httpClient';

// Mock httpClient
vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
  },
}));

describe('DashboardService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockTimelineData = {
    upcoming: [
      {
        id: 1,
        name: 'Test Expedition',
        deadline: '2025-12-31',
        status: 'active',
        daysRemaining: 90,
        progress: 50,
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

  const mockOverdueExpeditions = {
    expeditions: [
      {
        id: 2,
        name: 'Overdue Expedition',
        deadline: '2024-12-31',
        status: 'active',
        daysOverdue: 5,
      },
    ],
  };

  describe('getTimeline', () => {
    it('should fetch dashboard timeline', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockTimelineData,
      } as any);

      const result = await dashboardService.getTimeline();

      expect(httpClient.get).toHaveBeenCalledWith('/api/dashboard/timeline');
      expect(result).toEqual(mockTimelineData);
    });

    it('should handle empty timeline', async () => {
      const emptyTimeline = { upcoming: [], overdue: [] };

      vi.mocked(httpClient.get).mockResolvedValue({
        data: emptyTimeline,
      } as any);

      const result = await dashboardService.getTimeline();

      expect(result.upcoming).toEqual([]);
      expect(result.overdue).toEqual([]);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch timeline');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(dashboardService.getTimeline()).rejects.toThrow('Failed to fetch timeline');
    });
  });

  describe('getAnalytics', () => {
    it('should fetch analytics data', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockAnalytics,
      } as any);

      const result = await dashboardService.getAnalytics();

      expect(httpClient.get).toHaveBeenCalledWith('/api/dashboard/analytics');
      expect(result).toEqual(mockAnalytics);
    });

    it('should handle zero values', async () => {
      const zeroAnalytics = {
        totalExpeditions: 0,
        activeExpeditions: 0,
        completedExpeditions: 0,
        totalProfit: 0,
        averageCompletionTime: 0,
      };

      vi.mocked(httpClient.get).mockResolvedValue({
        data: zeroAnalytics,
      } as any);

      const result = await dashboardService.getAnalytics();

      expect(result.totalExpeditions).toBe(0);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch analytics');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(dashboardService.getAnalytics()).rejects.toThrow('Failed to fetch analytics');
    });
  });

  describe('getOverdueExpeditions', () => {
    it('should fetch overdue expeditions', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockOverdueExpeditions,
      } as any);

      const result = await dashboardService.getOverdueExpeditions();

      expect(httpClient.get).toHaveBeenCalledWith('/api/dashboard/overdue');
      expect(result).toEqual(mockOverdueExpeditions);
    });

    it('should handle no overdue expeditions', async () => {
      const noOverdue = { expeditions: [] };

      vi.mocked(httpClient.get).mockResolvedValue({
        data: noOverdue,
      } as any);

      const result = await dashboardService.getOverdueExpeditions();

      expect(result.expeditions).toEqual([]);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch overdue');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(dashboardService.getOverdueExpeditions()).rejects.toThrow(
        'Failed to fetch overdue'
      );
    });
  });

  describe('Service Instance', () => {
    it('should export a singleton instance', () => {
      expect(dashboardService).toBeInstanceOf(DashboardService);
    });

    it('should export the class for testing', () => {
      expect(DashboardService).toBeDefined();
      const newInstance = new DashboardService();
      expect(newInstance).toBeInstanceOf(DashboardService);
    });
  });
});
