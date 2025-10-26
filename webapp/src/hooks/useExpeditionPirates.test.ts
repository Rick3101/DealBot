import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { useExpeditionPirates } from './useExpeditionPirates';
import { bramblerService } from '@/services/api/bramblerService';
import { userService } from '@/services/api/userService';
import { PirateName } from '@/types/expedition';
import * as telegramUtils from '@/utils/telegram';

// Mock dependencies
vi.mock('@/services/api/bramblerService', () => ({
  bramblerService: {
    getNames: vi.fn(),
    generateNames: vi.fn(),
  },
}));

vi.mock('@/services/api/userService', () => ({
  userService: {
    getBuyers: vi.fn(),
  },
}));

vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
}));

describe('useExpeditionPirates', () => {
  const mockExpeditionId = 42;
  const mockPirateNames: PirateName[] = [
    {
      id: 1,
      expedition_id: 42,
      pirate_name: 'BlackBeard',
      original_name: 'John',
      created_at: '2025-01-01',
    },
    {
      id: 2,
      expedition_id: 42,
      pirate_name: 'RedRum',
      original_name: 'Jane',
      created_at: '2025-01-01',
    },
  ];

  const mockBuyers = [
    { name: 'John' },
    { name: 'Jane' },
    { name: 'Bob' },
    { name: 'Alice' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (bramblerService.getNames as Mock).mockResolvedValue(mockPirateNames);
    (bramblerService.generateNames as Mock).mockResolvedValue({ success: true });
    (userService.getBuyers as Mock).mockResolvedValue(mockBuyers);
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() =>
      useExpeditionPirates(mockExpeditionId)
    );

    expect(result.current.pirateNames).toEqual([]);
    expect(result.current.availableBuyers).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should load pirate names on mount', async () => {
    const { result } = renderHook(() =>
      useExpeditionPirates(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.pirateNames).toEqual(mockPirateNames);
    });

    expect(bramblerService.getNames).toHaveBeenCalledWith(mockExpeditionId);
  });

  it('should not load pirate names if expeditionId is null', async () => {
    renderHook(() => useExpeditionPirates(null));

    await waitFor(() => {
      expect(bramblerService.getNames).not.toHaveBeenCalled();
    });
  });

  it('should handle errors when loading pirate names', async () => {
    const mockError = new Error('Failed to load');
    (bramblerService.getNames as Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() =>
      useExpeditionPirates(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.error).toBe('Failed to load pirate names');
    });
  });

  it('should provide refresh function', async () => {
    const { result } = renderHook(() =>
      useExpeditionPirates(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.pirateNames).toEqual(mockPirateNames);
    });

    expect(result.current.refresh).toBeInstanceOf(Function);
  });

  it('should reload pirate names when refresh is called', async () => {
    const { result } = renderHook(() =>
      useExpeditionPirates(mockExpeditionId)
    );

    await waitFor(() => {
      expect(result.current.pirateNames).toEqual(mockPirateNames);
    });

    vi.clearAllMocks();

    await act(async () => {
      await result.current.refresh();
    });

    expect(bramblerService.getNames).toHaveBeenCalledWith(mockExpeditionId);
  });

  describe('loadAvailableBuyers', () => {
    it('should load available buyers excluding existing pirates', async () => {
      const { result } = renderHook(() =>
        useExpeditionPirates(mockExpeditionId)
      );

      await act(async () => {
        await result.current.loadAvailableBuyers();
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(userService.getBuyers).toHaveBeenCalled();
      expect(bramblerService.getNames).toHaveBeenCalledWith(mockExpeditionId);

      // Should exclude John and Jane (existing pirates)
      expect(result.current.availableBuyers).toEqual([
        { name: 'Bob' },
        { name: 'Alice' },
      ]);
    });

    it('should set loading state while fetching buyers', async () => {
      const { result } = renderHook(() =>
        useExpeditionPirates(mockExpeditionId)
      );

      // Mock a slow async operation
      (userService.getBuyers as Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockBuyers), 100))
      );

      expect(result.current.loading).toBe(false);

      // Start loading without awaiting
      let loadPromise: Promise<void>;
      act(() => {
        loadPromise = result.current.loadAvailableBuyers();
      });

      // Check loading state is true during operation
      await waitFor(() => {
        expect(result.current.loading).toBe(true);
      }, { timeout: 50 });

      // Wait for completion
      await act(async () => {
        await loadPromise!;
      });

      expect(result.current.loading).toBe(false);
    });

    it('should handle errors when loading buyers', async () => {
      const mockError = new Error('Failed to load buyers');
      (userService.getBuyers as Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useExpeditionPirates(mockExpeditionId)
      );

      await act(async () => {
        await result.current.loadAvailableBuyers();
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to load available buyers');
      });

      expect(result.current.loading).toBe(false);
    });

    it('should not load buyers if expeditionId is null', async () => {
      const { result } = renderHook(() =>
        useExpeditionPirates(null)
      );

      await act(async () => {
        await result.current.loadAvailableBuyers();
      });

      expect(userService.getBuyers).not.toHaveBeenCalled();
    });
  });

  describe('addPirate', () => {
    it('should add a new pirate successfully', async () => {
      const { result } = renderHook(() =>
        useExpeditionPirates(mockExpeditionId)
      );

      await waitFor(() => {
        expect(result.current.pirateNames).toEqual(mockPirateNames);
      });

      vi.clearAllMocks();

      await act(async () => {
        await result.current.addPirate('Bob');
      });

      expect(bramblerService.generateNames).toHaveBeenCalledWith(
        mockExpeditionId,
        { original_names: ['Bob'] }
      );
      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('success');

      // Should reload pirate names and available buyers
      expect(bramblerService.getNames).toHaveBeenCalledWith(mockExpeditionId);
    });

    it('should trim whitespace from pirate name', async () => {
      const { result } = renderHook(() =>
        useExpeditionPirates(mockExpeditionId)
      );

      await waitFor(() => {
        expect(result.current.pirateNames).toEqual(mockPirateNames);
      });

      await act(async () => {
        await result.current.addPirate('  Bob  ');
      });

      expect(bramblerService.generateNames).toHaveBeenCalledWith(
        mockExpeditionId,
        { original_names: ['Bob'] }
      );
    });

    it('should throw error if expeditionId is null', async () => {
      const { result } = renderHook(() =>
        useExpeditionPirates(null)
      );

      await expect(async () => {
        await act(async () => {
          await result.current.addPirate('Bob');
        });
      }).rejects.toThrow('Invalid expedition ID or pirate name');
    });

    it('should throw error if pirate name is empty', async () => {
      const { result } = renderHook(() =>
        useExpeditionPirates(mockExpeditionId)
      );

      await expect(async () => {
        await act(async () => {
          await result.current.addPirate('   ');
        });
      }).rejects.toThrow('Invalid expedition ID or pirate name');
    });

    it('should trigger error haptic feedback on failure', async () => {
      const mockError = new Error('Failed to generate');
      (bramblerService.generateNames as Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useExpeditionPirates(mockExpeditionId)
      );

      await waitFor(() => {
        expect(result.current.pirateNames).toEqual(mockPirateNames);
      });

      await expect(async () => {
        await act(async () => {
          await result.current.addPirate('Bob');
        });
      }).rejects.toThrow('Failed to generate');

      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('error');
    });

    it('should reload pirate names and available buyers after adding', async () => {
      const { result } = renderHook(() =>
        useExpeditionPirates(mockExpeditionId)
      );

      await waitFor(() => {
        expect(result.current.pirateNames).toEqual(mockPirateNames);
      });

      vi.clearAllMocks();

      await act(async () => {
        await result.current.addPirate('Bob');
      });

      // Should have called getNames twice (once for pirate names, once in loadAvailableBuyers)
      expect(bramblerService.getNames).toHaveBeenCalledTimes(2);
      expect(userService.getBuyers).toHaveBeenCalledTimes(1);
    });
  });

  it('should reload pirate names when expeditionId changes', async () => {
    const { result, rerender } = renderHook(
      ({ id }) => useExpeditionPirates(id),
      { initialProps: { id: mockExpeditionId } }
    );

    await waitFor(() => {
      expect(result.current.pirateNames).toEqual(mockPirateNames);
    });

    vi.clearAllMocks();

    const newExpeditionId = 99;
    const newPirateNames = [{ ...mockPirateNames[0], expedition_id: newExpeditionId }];
    (bramblerService.getNames as Mock).mockResolvedValue(newPirateNames);

    rerender({ id: newExpeditionId });

    await waitFor(() => {
      expect(result.current.pirateNames).toEqual(newPirateNames);
    });

    expect(bramblerService.getNames).toHaveBeenCalledWith(newExpeditionId);
  });
});
