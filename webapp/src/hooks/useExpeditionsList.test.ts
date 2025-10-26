import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useExpeditionsList } from './useExpeditionsList';
import { expeditionService } from '@/services/api/expeditionService';

vi.mock('@/services/api/expeditionService');

describe('useExpeditionsList', () => {
  const mockExpeditions = [
    {
      id: 1,
      name: 'Test Expedition 1',
      description: 'Description 1',
      status: 'active',
      created_at: '2025-01-01',
      deadline: '2025-12-31',
      items: [],
    },
    {
      id: 2,
      name: 'Test Expedition 2',
      description: 'Description 2',
      status: 'completed',
      created_at: '2025-01-01',
      deadline: '2025-12-31',
      items: [],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with loading state when initialLoad is true', () => {
    const { result } = renderHook(() => useExpeditionsList({ initialLoad: true }));

    expect(result.current.loading).toBe(true);
    expect(result.current.expeditions).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('should initialize without loading state when initialLoad is false', () => {
    const { result } = renderHook(() => useExpeditionsList({ initialLoad: false }));

    expect(result.current.loading).toBe(false);
    expect(result.current.expeditions).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('should fetch expeditions successfully', async () => {
    vi.mocked(expeditionService.getAll).mockResolvedValue(mockExpeditions);

    const { result } = renderHook(() => useExpeditionsList({ initialLoad: false }));

    await result.current.fetchExpeditions();

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.expeditions).toEqual(mockExpeditions);
      expect(result.current.error).toBeNull();
    });
  });

  it('should set loading state when showLoading is true', async () => {
    vi.mocked(expeditionService.getAll).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockExpeditions), 50))
    );

    const { result } = renderHook(() => useExpeditionsList({ initialLoad: false }));

    const fetchPromise = result.current.fetchExpeditions(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(true);
    });

    await fetchPromise;

    expect(result.current.loading).toBe(false);
  });

  it('should set refreshing state when showLoading is false', async () => {
    vi.mocked(expeditionService.getAll).mockResolvedValue(mockExpeditions);

    const { result } = renderHook(() => useExpeditionsList({ initialLoad: false }));

    result.current.fetchExpeditions(false);

    await waitFor(() => {
      expect(result.current.refreshing).toBe(false);
    });
  });

  it('should handle fetch errors', async () => {
    const errorMessage = 'Network error';
    vi.mocked(expeditionService.getAll).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useExpeditionsList({ initialLoad: false }));

    await result.current.fetchExpeditions();

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(errorMessage);
      expect(result.current.expeditions).toEqual([]);
    });
  });

  it('should allow manual state updates via setExpeditions', async () => {
    const { result } = renderHook(() => useExpeditionsList({ initialLoad: false }));

    result.current.setExpeditions(mockExpeditions);

    await waitFor(() => {
      expect(result.current.expeditions).toEqual(mockExpeditions);
    });
  });

  it('should clear error on successful fetch', async () => {
    vi.mocked(expeditionService.getAll)
      .mockRejectedValueOnce(new Error('First error'))
      .mockResolvedValueOnce(mockExpeditions);

    const { result } = renderHook(() => useExpeditionsList({ initialLoad: false }));

    // First fetch with error
    await result.current.fetchExpeditions();
    await waitFor(() => expect(result.current.error).toBe('First error'));

    // Second fetch successful
    await result.current.fetchExpeditions();
    await waitFor(() => {
      expect(result.current.error).toBeNull();
      expect(result.current.expeditions).toEqual(mockExpeditions);
    });
  });
});
