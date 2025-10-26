/**
 * Tests for useExpeditions facade hook
 *
 * Tests the main expedition hook that composes 5 focused hooks:
 * - Hook composition and orchestration
 * - CRUD operations with local state updates
 * - Auto-refresh functionality
 * - Real-time updates integration
 * - Backward compatibility
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useExpeditions } from './useExpeditions';
import type { Expedition, CreateExpeditionRequest } from '@/types/expedition';

// Mock all composed hooks
vi.mock('./useExpeditionsList', () => ({
  useExpeditionsList: vi.fn(() => ({
    expeditions: [],
    loading: false,
    error: null,
    refreshing: false,
    fetchExpeditions: vi.fn(),
    setExpeditions: vi.fn(),
  })),
}));

vi.mock('./useExpeditionCRUD', () => ({
  useExpeditionCRUD: vi.fn(() => ({
    error: null,
    createExpedition: vi.fn(),
    updateExpeditionStatus: vi.fn(),
    deleteExpedition: vi.fn(),
  })),
}));

vi.mock('./useDashboardData', () => ({
  useDashboardData: vi.fn(() => ({
    timelineData: null,
    analytics: null,
    fetchTimeline: vi.fn(),
    fetchAnalytics: vi.fn(),
    refreshDashboard: vi.fn(),
  })),
}));

vi.mock('./useAutoRefresh', () => ({
  useAutoRefresh: vi.fn(),
}));

vi.mock('./useExpeditionRealTime', () => ({
  useExpeditionRealTime: vi.fn(),
}));

import { useExpeditionsList } from './useExpeditionsList';
import { useExpeditionCRUD } from './useExpeditionCRUD';
import { useDashboardData } from './useDashboardData';
import { useAutoRefresh } from './useAutoRefresh';
import { useExpeditionRealTime } from './useExpeditionRealTime';

describe('useExpeditions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Hook Composition', () => {
    it('should compose all five sub-hooks', () => {
      renderHook(() => useExpeditions());

      expect(useExpeditionsList).toHaveBeenCalled();
      expect(useExpeditionCRUD).toHaveBeenCalled();
      expect(useDashboardData).toHaveBeenCalled();
      expect(useAutoRefresh).toHaveBeenCalled();
      expect(useExpeditionRealTime).toHaveBeenCalled();
    });

    it('should initialize expedition list with initialLoad true', () => {
      renderHook(() => useExpeditions());

      expect(useExpeditionsList).toHaveBeenCalledWith({ initialLoad: true });
    });

    it('should pass onSuccess callback to CRUD hook', () => {
      renderHook(() => useExpeditions());

      expect(useExpeditionCRUD).toHaveBeenCalledWith(
        expect.objectContaining({
          onSuccess: expect.any(Function),
        })
      );
    });
  });

  describe('Options Handling', () => {
    it('should use default options when none provided', () => {
      renderHook(() => useExpeditions());

      expect(useAutoRefresh).toHaveBeenCalledWith(
        expect.objectContaining({
          enabled: true,
          interval: 30000,
        })
      );

      expect(useExpeditionRealTime).toHaveBeenCalledWith(
        expect.objectContaining({
          enabled: true,
        })
      );
    });

    it('should pass custom autoRefresh option', () => {
      renderHook(() => useExpeditions({ autoRefresh: false }));

      expect(useAutoRefresh).toHaveBeenCalledWith(
        expect.objectContaining({
          enabled: false,
        })
      );
    });

    it('should pass custom refreshInterval option', () => {
      renderHook(() => useExpeditions({ refreshInterval: 60000 }));

      expect(useAutoRefresh).toHaveBeenCalledWith(
        expect.objectContaining({
          interval: 60000,
        })
      );
    });

    it('should pass custom realTimeUpdates option', () => {
      renderHook(() => useExpeditions({ realTimeUpdates: false }));

      expect(useExpeditionRealTime).toHaveBeenCalledWith(
        expect.objectContaining({
          enabled: false,
        })
      );
    });
  });

  describe('Return Value', () => {
    it('should return all required properties', () => {
      const { result } = renderHook(() => useExpeditions());

      expect(result.current).toHaveProperty('expeditions');
      expect(result.current).toHaveProperty('timelineData');
      expect(result.current).toHaveProperty('analytics');
      expect(result.current).toHaveProperty('loading');
      expect(result.current).toHaveProperty('error');
      expect(result.current).toHaveProperty('refreshing');
      expect(result.current).toHaveProperty('refreshExpeditions');
      expect(result.current).toHaveProperty('createExpedition');
      expect(result.current).toHaveProperty('updateExpeditionStatus');
      expect(result.current).toHaveProperty('deleteExpedition');
      expect(result.current).toHaveProperty('refreshTimeline');
      expect(result.current).toHaveProperty('refreshAnalytics');
    });

    it('should delegate expeditions from list hook', () => {
      const mockExpeditions: Expedition[] = [
        { id: 1, name: 'Test Expedition', status: 'active' } as Expedition,
      ];

      (useExpeditionsList as any).mockReturnValue({
        expeditions: mockExpeditions,
        loading: false,
        error: null,
        refreshing: false,
        fetchExpeditions: vi.fn(),
        setExpeditions: vi.fn(),
      });

      const { result } = renderHook(() => useExpeditions());

      expect(result.current.expeditions).toEqual(mockExpeditions);
    });

    it('should delegate loading from list hook', () => {
      (useExpeditionsList as any).mockReturnValue({
        expeditions: [],
        loading: true,
        error: null,
        refreshing: false,
        fetchExpeditions: vi.fn(),
        setExpeditions: vi.fn(),
      });

      const { result } = renderHook(() => useExpeditions());

      expect(result.current.loading).toBe(true);
    });

    it('should delegate refreshing from list hook', () => {
      (useExpeditionsList as any).mockReturnValue({
        expeditions: [],
        loading: false,
        error: null,
        refreshing: true,
        fetchExpeditions: vi.fn(),
        setExpeditions: vi.fn(),
      });

      const { result } = renderHook(() => useExpeditions());

      expect(result.current.refreshing).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should return list error', () => {
      (useExpeditionsList as any).mockReturnValue({
        expeditions: [],
        loading: false,
        error: 'List error',
        refreshing: false,
        fetchExpeditions: vi.fn(),
        setExpeditions: vi.fn(),
      });

      const { result } = renderHook(() => useExpeditions());

      expect(result.current.error).toBe('List error');
    });

    it('should return CRUD error', () => {
      // Ensure list error is null
      (useExpeditionsList as any).mockReturnValue({
        expeditions: [],
        loading: false,
        error: null,
        refreshing: false,
        fetchExpeditions: vi.fn(),
        setExpeditions: vi.fn(),
      });

      (useExpeditionCRUD as any).mockReturnValue({
        error: 'CRUD error',
        createExpedition: vi.fn(),
        updateExpeditionStatus: vi.fn(),
        deleteExpedition: vi.fn(),
      });

      const { result } = renderHook(() => useExpeditions());

      expect(result.current.error).toBe('CRUD error');
    });

    it('should prioritize list error over CRUD error', () => {
      (useExpeditionsList as any).mockReturnValue({
        expeditions: [],
        loading: false,
        error: 'List error',
        refreshing: false,
        fetchExpeditions: vi.fn(),
        setExpeditions: vi.fn(),
      });

      (useExpeditionCRUD as any).mockReturnValue({
        error: 'CRUD error',
        createExpedition: vi.fn(),
        updateExpeditionStatus: vi.fn(),
        deleteExpedition: vi.fn(),
      });

      const { result } = renderHook(() => useExpeditions());

      expect(result.current.error).toBe('List error');
    });
  });

  describe('CRUD Operations', () => {
    it('should create expedition and update local state', async () => {
      const mockCreate = vi.fn().mockResolvedValue({ id: 1, name: 'New' } as Expedition);
      const mockSetExpeditions = vi.fn();

      (useExpeditionCRUD as any).mockReturnValue({
        error: null,
        createExpedition: mockCreate,
        updateExpeditionStatus: vi.fn(),
        deleteExpedition: vi.fn(),
      });

      (useExpeditionsList as any).mockReturnValue({
        expeditions: [],
        loading: false,
        error: null,
        refreshing: false,
        fetchExpeditions: vi.fn(),
        setExpeditions: mockSetExpeditions,
      });

      const { result } = renderHook(() => useExpeditions());

      const newExpedition: CreateExpeditionRequest = {
        name: 'New',
        description: 'Test',
        deadline_days: 7,
      };

      await act(async () => {
        await result.current.createExpedition(newExpedition);
      });

      expect(mockCreate).toHaveBeenCalledWith(newExpedition);
      expect(mockSetExpeditions).toHaveBeenCalled();
    });

    it('should update expedition status and update local state', async () => {
      const mockUpdate = vi.fn().mockResolvedValue({ id: 1, status: 'completed' } as Expedition);
      const mockSetExpeditions = vi.fn();

      (useExpeditionCRUD as any).mockReturnValue({
        error: null,
        createExpedition: vi.fn(),
        updateExpeditionStatus: mockUpdate,
        deleteExpedition: vi.fn(),
      });

      (useExpeditionsList as any).mockReturnValue({
        expeditions: [{ id: 1, status: 'active' } as Expedition],
        loading: false,
        error: null,
        refreshing: false,
        fetchExpeditions: vi.fn(),
        setExpeditions: mockSetExpeditions,
      });

      const { result } = renderHook(() => useExpeditions());

      await act(async () => {
        const success = await result.current.updateExpeditionStatus(1, 'completed');
        expect(success).toBe(true);
      });

      expect(mockUpdate).toHaveBeenCalledWith(1, 'completed');
      expect(mockSetExpeditions).toHaveBeenCalled();
    });

    it('should delete expedition and update local state', async () => {
      const mockDelete = vi.fn().mockResolvedValue(true);
      const mockSetExpeditions = vi.fn();

      (useExpeditionCRUD as any).mockReturnValue({
        error: null,
        createExpedition: vi.fn(),
        updateExpeditionStatus: vi.fn(),
        deleteExpedition: mockDelete,
      });

      (useExpeditionsList as any).mockReturnValue({
        expeditions: [{ id: 1, name: 'Test' } as Expedition],
        loading: false,
        error: null,
        refreshing: false,
        fetchExpeditions: vi.fn(),
        setExpeditions: mockSetExpeditions,
      });

      const { result } = renderHook(() => useExpeditions());

      await act(async () => {
        const success = await result.current.deleteExpedition(1);
        expect(success).toBe(true);
      });

      expect(mockDelete).toHaveBeenCalledWith(1);
      expect(mockSetExpeditions).toHaveBeenCalled();
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh all data when refreshExpeditions is called', async () => {
      const mockFetchExpeditions = vi.fn().mockResolvedValue(undefined);
      const mockRefreshDashboard = vi.fn().mockResolvedValue(undefined);

      (useExpeditionsList as any).mockReturnValue({
        expeditions: [],
        loading: false,
        error: null,
        refreshing: false,
        fetchExpeditions: mockFetchExpeditions,
        setExpeditions: vi.fn(),
      });

      (useDashboardData as any).mockReturnValue({
        timelineData: null,
        analytics: null,
        fetchTimeline: vi.fn(),
        fetchAnalytics: vi.fn(),
        refreshDashboard: mockRefreshDashboard,
      });

      const { result } = renderHook(() => useExpeditions());

      await act(async () => {
        await result.current.refreshExpeditions();
      });

      expect(mockFetchExpeditions).toHaveBeenCalledWith(false);
      expect(mockRefreshDashboard).toHaveBeenCalled();
    });

    it('should delegate refreshTimeline to fetchTimeline', () => {
      const mockFetchTimeline = vi.fn();

      (useDashboardData as any).mockReturnValue({
        timelineData: null,
        analytics: null,
        fetchTimeline: mockFetchTimeline,
        fetchAnalytics: vi.fn(),
        refreshDashboard: vi.fn(),
      });

      const { result } = renderHook(() => useExpeditions());

      act(() => {
        result.current.refreshTimeline();
      });

      expect(mockFetchTimeline).toHaveBeenCalled();
    });

    it('should delegate refreshAnalytics to fetchAnalytics', () => {
      const mockFetchAnalytics = vi.fn();

      (useDashboardData as any).mockReturnValue({
        timelineData: null,
        analytics: null,
        fetchTimeline: vi.fn(),
        fetchAnalytics: mockFetchAnalytics,
        refreshDashboard: vi.fn(),
      });

      const { result } = renderHook(() => useExpeditions());

      act(() => {
        result.current.refreshAnalytics();
      });

      expect(mockFetchAnalytics).toHaveBeenCalled();
    });
  });

  describe('Auto-Refresh Integration', () => {
    it('should pass refresh callback to useAutoRefresh', () => {
      renderHook(() => useExpeditions());

      expect(useAutoRefresh).toHaveBeenCalledWith(
        expect.objectContaining({
          onRefresh: expect.any(Function),
        })
      );
    });
  });

  describe('Real-Time Updates Integration', () => {
    it('should register expedition update handler', () => {
      renderHook(() => useExpeditions());

      expect(useExpeditionRealTime).toHaveBeenCalledWith(
        expect.objectContaining({
          onExpeditionUpdate: expect.any(Function),
        })
      );
    });

    it('should register item consumed handler', () => {
      renderHook(() => useExpeditions());

      expect(useExpeditionRealTime).toHaveBeenCalledWith(
        expect.objectContaining({
          onItemConsumed: expect.any(Function),
        })
      );
    });

    it('should register expedition completed handler', () => {
      renderHook(() => useExpeditions());

      expect(useExpeditionRealTime).toHaveBeenCalledWith(
        expect.objectContaining({
          onExpeditionCompleted: expect.any(Function),
        })
      );
    });

    it('should register expedition created handler', () => {
      renderHook(() => useExpeditions());

      expect(useExpeditionRealTime).toHaveBeenCalledWith(
        expect.objectContaining({
          onExpeditionCreated: expect.any(Function),
        })
      );
    });
  });

  describe('Backward Compatibility', () => {
    it('should maintain consistent API across versions', () => {
      const { result } = renderHook(() => useExpeditions());

      const apiSurface = Object.keys(result.current).sort();

      expect(apiSurface).toEqual([
        'analytics',
        'createExpedition',
        'deleteExpedition',
        'error',
        'expeditions',
        'loading',
        'refreshAnalytics',
        'refreshExpeditions',
        'refreshTimeline',
        'refreshing',
        'timelineData',
        'updateExpeditionStatus',
      ]);
    });

    it('should work without any options', () => {
      const { result } = renderHook(() => useExpeditions());

      expect(result.current).toBeDefined();
      expect(result.current.expeditions).toBeDefined();
      expect(result.current.loading).toBeDefined();
    });
  });
});
