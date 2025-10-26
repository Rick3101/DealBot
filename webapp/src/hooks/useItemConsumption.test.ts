import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { useItemConsumption } from './useItemConsumption';
import { expeditionItemsService } from '@/services/api/expeditionItemsService';
import * as telegramUtils from '@/utils/telegram';

// Mock dependencies
vi.mock('@/services/api/expeditionItemsService', () => ({
  expeditionItemsService: {
    consumeItem: vi.fn(),
  },
}));

vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
}));

describe('useItemConsumption', () => {
  const mockExpeditionId = 42;
  const mockConsumeParams = {
    product_id: 1,
    pirate_name: 'BlackBeard',
    quantity: 5,
    price: 100,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (expeditionItemsService.consumeItem as Mock).mockResolvedValue({ success: true });
  });

  it('should initialize with non-consuming state', () => {
    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    expect(result.current.consuming).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.consumeItem).toBeInstanceOf(Function);
  });

  it('should consume item successfully', async () => {
    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    await act(async () => {
      await result.current.consumeItem(mockConsumeParams);
    });

    expect(expeditionItemsService.consumeItem).toHaveBeenCalledWith(
      mockExpeditionId,
      mockConsumeParams
    );
    expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('success');
    expect(result.current.error).toBeNull();
    expect(result.current.consuming).toBe(false);
  });

  it('should set consuming state while consuming', async () => {
    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    // Mock a slow async operation
    (expeditionItemsService.consumeItem as Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    expect(result.current.consuming).toBe(false);

    // Start consumption without awaiting
    let consumePromise: Promise<void>;
    act(() => {
      consumePromise = result.current.consumeItem(mockConsumeParams);
    });

    // Check consuming state is true during operation
    await waitFor(() => {
      expect(result.current.consuming).toBe(true);
    }, { timeout: 50 });

    // Wait for completion
    await act(async () => {
      await consumePromise!;
    });

    expect(result.current.consuming).toBe(false);
  });

  it('should call onSuccess callback after successful consumption', async () => {
    const onSuccess = vi.fn();
    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    await act(async () => {
      await result.current.consumeItem(mockConsumeParams, onSuccess);
    });

    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('success');
  });

  it('should not call onSuccess callback if consumption fails', async () => {
    const onSuccess = vi.fn();
    const mockError = new Error('Consumption failed');
    (expeditionItemsService.consumeItem as Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    await expect(async () => {
      await act(async () => {
        await result.current.consumeItem(mockConsumeParams, onSuccess);
      });
    }).rejects.toThrow('Consumption failed');

    expect(onSuccess).not.toHaveBeenCalled();
  });

  it('should handle consumption errors', async () => {
    const mockError = new Error('Consumption failed');
    (expeditionItemsService.consumeItem as Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    try {
      await act(async () => {
        await result.current.consumeItem(mockConsumeParams);
      });
      fail('Should have thrown an error');
    } catch (err) {
      // Expected to throw
    }

    // Give React time to flush state updates from the catch block
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.error).toBe('Consumption failed');
    expect(result.current.consuming).toBe(false);
    expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('error');
  });

  it('should handle non-Error exceptions', async () => {
    const mockError = 'String error';
    (expeditionItemsService.consumeItem as Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    try {
      await act(async () => {
        await result.current.consumeItem(mockConsumeParams);
      });
      fail('Should have thrown an error');
    } catch (err) {
      // Expected to throw
    }

    // Give React time to flush state updates from the catch block
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.error).toBe('Failed to consume item');
    expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('error');
  });

  it('should clear error on successful consumption after previous error', async () => {
    const mockError = new Error('First error');
    (expeditionItemsService.consumeItem as Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    // First call - should fail
    try {
      await act(async () => {
        await result.current.consumeItem(mockConsumeParams);
      });
      fail('Should have thrown an error');
    } catch (err) {
      // Expected to throw
    }

    // Give React time to flush state updates from the catch block
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.error).toBe('First error');

    // Second call - should succeed
    (expeditionItemsService.consumeItem as Mock).mockResolvedValue({ success: true });

    await act(async () => {
      await result.current.consumeItem(mockConsumeParams);
    });

    expect(result.current.error).toBeNull();
    expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('success');
  });

  it('should set consuming to false even if consumption fails', async () => {
    const mockError = new Error('Failed');
    (expeditionItemsService.consumeItem as Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    await expect(async () => {
      await act(async () => {
        await result.current.consumeItem(mockConsumeParams);
      });
    }).rejects.toThrow();

    expect(result.current.consuming).toBe(false);
  });

  it('should handle multiple consume operations', async () => {
    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    // First consumption
    await act(async () => {
      await result.current.consumeItem(mockConsumeParams);
    });

    expect(expeditionItemsService.consumeItem).toHaveBeenCalledTimes(1);

    // Second consumption with different params
    const secondParams = {
      ...mockConsumeParams,
      product_id: 2,
      quantity: 10,
    };

    await act(async () => {
      await result.current.consumeItem(secondParams);
    });

    expect(expeditionItemsService.consumeItem).toHaveBeenCalledTimes(2);
    expect(expeditionItemsService.consumeItem).toHaveBeenLastCalledWith(
      mockExpeditionId,
      secondParams
    );
    expect(result.current.consuming).toBe(false);
  });

  it('should pass correct expedition ID to service', async () => {
    const customExpeditionId = 99;
    const { result } = renderHook(() =>
      useItemConsumption(customExpeditionId)
    );

    await act(async () => {
      await result.current.consumeItem(mockConsumeParams);
    });

    expect(expeditionItemsService.consumeItem).toHaveBeenCalledWith(
      customExpeditionId,
      mockConsumeParams
    );
  });

  it('should preserve all consume parameters', async () => {
    const { result } = renderHook(() =>
      useItemConsumption(mockExpeditionId)
    );

    const detailedParams = {
      product_id: 123,
      pirate_name: 'CaptainJack',
      quantity: 42,
      price: 999.99,
    };

    await act(async () => {
      await result.current.consumeItem(detailedParams);
    });

    expect(expeditionItemsService.consumeItem).toHaveBeenCalledWith(
      mockExpeditionId,
      detailedParams
    );
  });
});
