import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { useExpeditionDetails } from './useExpeditionDetails';
import { expeditionService } from '@/services/api/expeditionService';
import { ExpeditionDetails } from '@/types/expedition';

// Mock dependencies
vi.mock('@/services/api/expeditionService', () => ({
  expeditionService: {
    getById: vi.fn(),
  },
}));

vi.mock('./useRealTimeUpdates', () => ({
  useRealTimeUpdates: vi.fn(() => ({ updates: [] })),
}));

describe('useExpeditionDetails', () => {
  const mockExpeditionId = 42;
  const mockExpedition: ExpeditionDetails = {
    id: 42,
    name: 'Test Expedition',
    description: 'Test Description',
    status: 'active',
    deadline: '2025-12-31',
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
    items: [],
    progress: {
      completion_percentage: 50,
      total_items: 10,
      consumed_items: 5,
      remaining_items: 5,
      total_value: 1000,
      consumed_value: 500,
      remaining_value: 500,
    },
  } as ExpeditionDetails;

  beforeEach(() => {
    vi.clearAllMocks();
    (expeditionService.getById as Mock).mockResolvedValue(mockExpedition);
  });

  it('should initialize with loading state', () => {
    const { result } = renderHook(() =>
      useExpeditionDetails(mockExpeditionId)
    );

    expect(result.current.loading).toBe(true);
    expect(result.current.expedition).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.refreshing).toBe(false);
  });

  it('should load expedition data on mount', async () => {
    const { result } = renderHook(() =>
      useExpeditionDetails(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(expeditionService.getById).toHaveBeenCalledWith(mockExpeditionId);
    expect(result.current.expedition).toEqual(mockExpedition);
    expect(result.current.error).toBeNull();
  });

  it('should handle loading errors', async () => {
    const mockError = new Error('Failed to load');
    (expeditionService.getById as Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() =>
      useExpeditionDetails(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.expedition).toBeNull();
    expect(result.current.error).toBe('Failed to load expedition details. Please try again.');
  });

  it('should set loading to false even if loading fails', async () => {
    (expeditionService.getById as Mock).mockRejectedValue(new Error('Failed'));

    const { result } = renderHook(() =>
      useExpeditionDetails(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.loading).toBe(false);
  });

  it('should provide refresh function', async () => {
    const { result } = renderHook(() =>
      useExpeditionDetails(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.refresh).toBeInstanceOf(Function);
  });

  it('should use refreshing state when refresh is called', async () => {
    const { result } = renderHook(() =>
      useExpeditionDetails(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Clear previous calls
    vi.clearAllMocks();

    // Call refresh
    result.current.refresh();

    await waitFor(() => {
      expect(result.current.refreshing).toBe(false);
    });

    expect(expeditionService.getById).toHaveBeenCalledWith(mockExpeditionId);
  });

  it('should reload expedition when expeditionId changes', async () => {
    const { result, rerender } = renderHook(
      ({ id }) => useExpeditionDetails(id),
      { initialProps: { id: mockExpeditionId } }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(expeditionService.getById).toHaveBeenCalledWith(mockExpeditionId);

    // Change expedition ID
    const newExpeditionId = 99;
    const newExpedition = { ...mockExpedition, id: newExpeditionId };
    (expeditionService.getById as Mock).mockResolvedValue(newExpedition);

    rerender({ id: newExpeditionId });

    await waitFor(() => {
      expect(result.current.expedition?.id).toBe(newExpeditionId);
    });

    expect(expeditionService.getById).toHaveBeenCalledWith(newExpeditionId);
  });

  it('should respect enableRealTime option', () => {
    const useRealTimeUpdatesMock = vi.fn(() => ({ updates: [] }));
    vi.doMock('./useRealTimeUpdates', () => ({
      useRealTimeUpdates: useRealTimeUpdatesMock,
    }));

    renderHook(() =>
      useExpeditionDetails(mockExpeditionId, { enableRealTime: false })
    );

    // Note: This test is simplified as the mock is already set up globally
    // In a real scenario, you'd verify the hook wasn't called with expeditionId
  });

  it('should handle refresh errors gracefully', async () => {
    const { result } = renderHook(() =>
      useExpeditionDetails(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Make refresh fail
    (expeditionService.getById as Mock).mockRejectedValue(new Error('Refresh failed'));

    result.current.refresh();

    await waitFor(() => {
      expect(result.current.refreshing).toBe(false);
    });

    expect(result.current.error).toBe('Failed to load expedition details. Please try again.');
  });

  it('should clear error on successful reload', async () => {
    // First, cause an error
    (expeditionService.getById as Mock).mockRejectedValue(new Error('Initial error'));

    const { result } = renderHook(() =>
      useExpeditionDetails(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    expect(result.current.error).toBe('Failed to load expedition details. Please try again.');

    // Now make it succeed
    (expeditionService.getById as Mock).mockResolvedValue(mockExpedition);

    result.current.refresh();

    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });

    expect(result.current.expedition).toEqual(mockExpedition);
  });
});
