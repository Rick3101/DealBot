import { renderHook } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useDashboardStats } from './useDashboardStats';
import { Expedition } from '@/types/expedition';

describe('useDashboardStats', () => {
  const mockExpeditions: Expedition[] = [
    {
      id: 1,
      name: 'Expedition 1',
      description: 'Test expedition',
      status: 'active',
      deadline: '2025-12-31',
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition,
    {
      id: 2,
      name: 'Expedition 2',
      description: 'Test expedition 2',
      status: 'active',
      deadline: '2025-12-31',
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition,
    {
      id: 3,
      name: 'Expedition 3',
      description: 'Test expedition 3',
      status: 'completed',
      deadline: '2025-12-31',
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition,
  ];

  it('should use timeline stats when available', () => {
    const timelineData = {
      stats: {
        total_expeditions: 10,
        active_expeditions: 5,
        completed_expeditions: 3,
        overdue_expeditions: 2,
      },
    };

    const { result } = renderHook(() =>
      useDashboardStats(mockExpeditions, timelineData)
    );

    expect(result.current).toEqual(timelineData.stats);
  });

  it('should calculate stats from expeditions when timeline data is null', () => {
    const { result } = renderHook(() =>
      useDashboardStats(mockExpeditions, null)
    );

    expect(result.current).toEqual({
      total_expeditions: 3,
      active_expeditions: 2,
      completed_expeditions: 1,
      overdue_expeditions: 0,
    });
  });

  it('should calculate stats from expeditions when timeline data has no stats', () => {
    const timelineData = {
      timeline: [],
    };

    const { result } = renderHook(() =>
      useDashboardStats(mockExpeditions, timelineData)
    );

    expect(result.current).toEqual({
      total_expeditions: 3,
      active_expeditions: 2,
      completed_expeditions: 1,
      overdue_expeditions: 0,
    });
  });

  it('should return zero stats for empty expeditions array', () => {
    const { result } = renderHook(() =>
      useDashboardStats([], null)
    );

    expect(result.current).toEqual({
      total_expeditions: 0,
      active_expeditions: 0,
      completed_expeditions: 0,
      overdue_expeditions: 0,
    });
  });

  it('should handle expeditions with different statuses', () => {
    const mixedExpeditions: Expedition[] = [
      { id: 1, status: 'active' } as Expedition,
      { id: 2, status: 'active' } as Expedition,
      { id: 3, status: 'completed' } as Expedition,
      { id: 4, status: 'completed' } as Expedition,
      { id: 5, status: 'completed' } as Expedition,
      { id: 6, status: 'cancelled' } as Expedition,
    ];

    const { result } = renderHook(() =>
      useDashboardStats(mixedExpeditions, null)
    );

    expect(result.current).toEqual({
      total_expeditions: 6,
      active_expeditions: 2,
      completed_expeditions: 3,
      overdue_expeditions: 0,
    });
  });

  it('should memoize result when inputs do not change', () => {
    const { result, rerender } = renderHook(() =>
      useDashboardStats(mockExpeditions, null)
    );

    const firstResult = result.current;

    // Rerender without changing inputs
    rerender();

    expect(result.current).toBe(firstResult); // Should be same reference
  });

  it('should update result when expeditions change', () => {
    const { result, rerender } = renderHook(
      ({ expeditions }) => useDashboardStats(expeditions, null),
      { initialProps: { expeditions: mockExpeditions } }
    );

    expect(result.current.total_expeditions).toBe(3);

    // Change expeditions
    const newExpeditions = [
      ...mockExpeditions,
      { id: 4, status: 'active' } as Expedition,
    ];

    rerender({ expeditions: newExpeditions });

    expect(result.current.total_expeditions).toBe(4);
    expect(result.current.active_expeditions).toBe(3);
  });

  it('should update result when timeline data changes', () => {
    const { result, rerender } = renderHook(
      ({ timelineData }) => useDashboardStats(mockExpeditions, timelineData),
      { initialProps: { timelineData: null as any } }
    );

    expect(result.current.total_expeditions).toBe(3);

    // Add timeline data
    const newTimelineData = {
      stats: {
        total_expeditions: 100,
        active_expeditions: 50,
        completed_expeditions: 30,
        overdue_expeditions: 20,
      },
    };

    rerender({ timelineData: newTimelineData });

    expect(result.current).toEqual(newTimelineData.stats);
  });
});
