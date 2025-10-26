import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTimelineExpeditions } from './useTimelineExpeditions';
import { Expedition, ExpeditionTimelineEntry } from '@/types/expedition';

describe('useTimelineExpeditions', () => {
  const mockExpeditions: Expedition[] = [
    {
      id: 1,
      name: 'Active Expedition',
      description: 'Test',
      status: 'active',
      deadline: '2025-12-31',
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition,
    {
      id: 2,
      name: 'Completed Expedition',
      description: 'Test',
      status: 'completed',
      deadline: '2025-01-01',
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition,
  ];

  beforeEach(() => {
    // Mock current date to 2025-06-01
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-06-01'));
  });

  it('should use timeline data when available', () => {
    const mockTimelineEntries: ExpeditionTimelineEntry[] = [
      {
        ...mockExpeditions[0],
        is_overdue: false,
        progress: {
          completion_percentage: 50,
          total_items: 10,
          consumed_items: 5,
          remaining_items: 5,
          total_value: 1000,
          consumed_value: 500,
          remaining_value: 500,
        },
      } as ExpeditionTimelineEntry,
    ];

    const timelineData = {
      timeline: mockTimelineEntries,
    };

    const { result } = renderHook(() =>
      useTimelineExpeditions(mockExpeditions, timelineData)
    );

    expect(result.current).toEqual(mockTimelineEntries);
  });

  it('should transform expeditions when timeline data is null', () => {
    const { result } = renderHook(() =>
      useTimelineExpeditions(mockExpeditions, null)
    );

    expect(result.current).toHaveLength(2);
    expect(result.current[0]).toMatchObject({
      ...mockExpeditions[0],
      is_overdue: false,
      progress: {
        completion_percentage: 0,
        total_items: 0,
        consumed_items: 0,
        remaining_items: 0,
        total_value: 0,
        consumed_value: 0,
        remaining_value: 0,
      },
    });
  });

  it('should mark expedition as overdue when deadline has passed and status is active', () => {
    const overdueExpedition: Expedition = {
      id: 3,
      name: 'Overdue Expedition',
      description: 'Test',
      status: 'active',
      deadline: '2025-01-01', // Past date
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition;

    const { result } = renderHook(() =>
      useTimelineExpeditions([overdueExpedition], null)
    );

    expect(result.current[0].is_overdue).toBe(true);
  });

  it('should not mark expedition as overdue when deadline has passed but status is not active', () => {
    const completedExpedition: Expedition = {
      id: 4,
      name: 'Completed Expedition',
      description: 'Test',
      status: 'completed',
      deadline: '2025-01-01', // Past date
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition;

    const { result } = renderHook(() =>
      useTimelineExpeditions([completedExpedition], null)
    );

    expect(result.current[0].is_overdue).toBe(false);
  });

  it('should not mark expedition as overdue when deadline is in future', () => {
    const futureExpedition: Expedition = {
      id: 5,
      name: 'Future Expedition',
      description: 'Test',
      status: 'active',
      deadline: '2025-12-31', // Future date
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition;

    const { result } = renderHook(() =>
      useTimelineExpeditions([futureExpedition], null)
    );

    expect(result.current[0].is_overdue).toBe(false);
  });

  it('should handle expeditions without deadlines', () => {
    const noDeadlineExpedition: Expedition = {
      id: 6,
      name: 'No Deadline Expedition',
      description: 'Test',
      status: 'active',
      deadline: null,
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    } as Expedition;

    const { result } = renderHook(() =>
      useTimelineExpeditions([noDeadlineExpedition], null)
    );

    expect(result.current[0].is_overdue).toBe(false);
  });

  it('should add default progress object to all expeditions', () => {
    const { result } = renderHook(() =>
      useTimelineExpeditions(mockExpeditions, null)
    );

    result.current.forEach(entry => {
      expect(entry.progress).toEqual({
        completion_percentage: 0,
        total_items: 0,
        consumed_items: 0,
        remaining_items: 0,
        total_value: 0,
        consumed_value: 0,
        remaining_value: 0,
      });
    });
  });

  it('should return empty array for empty expeditions', () => {
    const { result } = renderHook(() =>
      useTimelineExpeditions([], null)
    );

    expect(result.current).toEqual([]);
  });

  it('should memoize result when inputs do not change', () => {
    const { result, rerender } = renderHook(() =>
      useTimelineExpeditions(mockExpeditions, null)
    );

    const firstResult = result.current;
    rerender();

    expect(result.current).toBe(firstResult); // Same reference
  });

  it('should update result when expeditions change', () => {
    const { result, rerender } = renderHook(
      ({ expeditions }) => useTimelineExpeditions(expeditions, null),
      { initialProps: { expeditions: mockExpeditions } }
    );

    expect(result.current).toHaveLength(2);

    const newExpeditions = [
      ...mockExpeditions,
      {
        id: 7,
        name: 'New Expedition',
        status: 'active',
      } as Expedition,
    ];

    rerender({ expeditions: newExpeditions });

    expect(result.current).toHaveLength(3);
  });

  it('should update result when timeline data changes', () => {
    const { result, rerender } = renderHook(
      ({ timelineData }) => useTimelineExpeditions(mockExpeditions, timelineData),
      { initialProps: { timelineData: null as any } }
    );

    expect(result.current[0].progress.completion_percentage).toBe(0);

    const newTimelineData = {
      timeline: [
        {
          ...mockExpeditions[0],
          is_overdue: true,
          progress: {
            completion_percentage: 75,
            total_items: 20,
            consumed_items: 15,
            remaining_items: 5,
            total_value: 2000,
            consumed_value: 1500,
            remaining_value: 500,
          },
        },
      ] as ExpeditionTimelineEntry[],
    };

    rerender({ timelineData: newTimelineData });

    expect(result.current).toEqual(newTimelineData.timeline);
  });
});
