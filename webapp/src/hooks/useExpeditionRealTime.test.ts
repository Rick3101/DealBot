import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useExpeditionRealTime } from './useExpeditionRealTime';
import { websocketService } from '@/services/websocketService';

vi.mock('@/services/websocketService', () => ({
  websocketService: {
    on: vi.fn(),
    off: vi.fn(),
  },
}));

describe('useExpeditionRealTime', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should subscribe to WebSocket events when enabled', () => {
    const onExpeditionUpdate = vi.fn();
    const onItemConsumed = vi.fn();
    const onExpeditionCompleted = vi.fn();
    const onExpeditionCreated = vi.fn();

    renderHook(() =>
      useExpeditionRealTime({
        enabled: true,
        onExpeditionUpdate,
        onItemConsumed,
        onExpeditionCompleted,
        onExpeditionCreated,
      })
    );

    expect(websocketService.on).toHaveBeenCalledWith(
      'expeditionUpdate',
      expect.any(Function)
    );
    expect(websocketService.on).toHaveBeenCalledWith('itemConsumed', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith(
      'expeditionCompleted',
      expect.any(Function)
    );
    expect(websocketService.on).toHaveBeenCalledWith(
      'expeditionCreated',
      expect.any(Function)
    );
  });

  it('should not subscribe to WebSocket events when disabled', () => {
    renderHook(() =>
      useExpeditionRealTime({
        enabled: false,
      })
    );

    expect(websocketService.on).not.toHaveBeenCalled();
  });

  it('should unsubscribe from WebSocket events on unmount', () => {
    const { unmount } = renderHook(() =>
      useExpeditionRealTime({
        enabled: true,
      })
    );

    unmount();

    expect(websocketService.off).toHaveBeenCalledWith(
      'expeditionUpdate',
      expect.any(Function)
    );
    expect(websocketService.off).toHaveBeenCalledWith('itemConsumed', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith(
      'expeditionCompleted',
      expect.any(Function)
    );
    expect(websocketService.off).toHaveBeenCalledWith(
      'expeditionCreated',
      expect.any(Function)
    );
  });

  it('should call onExpeditionUpdate when expedition is updated', () => {
    const onExpeditionUpdate = vi.fn();
    let capturedHandler: any;

    vi.mocked(websocketService.on).mockImplementation((event, handler) => {
      if (event === 'expeditionUpdate') {
        capturedHandler = handler;
      }
    });

    renderHook(() =>
      useExpeditionRealTime({
        enabled: true,
        onExpeditionUpdate,
      })
    );

    const updateData = { type: 'EXPEDITION_UPDATED', expeditionId: 1 };
    capturedHandler(updateData);

    expect(onExpeditionUpdate).toHaveBeenCalledWith(updateData);
  });

  it('should call onItemConsumed when item is consumed', () => {
    const onItemConsumed = vi.fn();
    let capturedHandler: any;

    vi.mocked(websocketService.on).mockImplementation((event, handler) => {
      if (event === 'itemConsumed') {
        capturedHandler = handler;
      }
    });

    renderHook(() =>
      useExpeditionRealTime({
        enabled: true,
        onItemConsumed,
      })
    );

    const consumedData = { expeditionId: 1, itemId: 2 };
    capturedHandler(consumedData);

    expect(onItemConsumed).toHaveBeenCalledWith(consumedData);
  });

  it('should call onExpeditionCompleted when expedition is completed', () => {
    const onExpeditionCompleted = vi.fn();
    let capturedHandler: any;

    vi.mocked(websocketService.on).mockImplementation((event, handler) => {
      if (event === 'expeditionCompleted') {
        capturedHandler = handler;
      }
    });

    renderHook(() =>
      useExpeditionRealTime({
        enabled: true,
        onExpeditionCompleted,
      })
    );

    const completedData = { type: 'EXPEDITION_COMPLETED', expeditionId: 1 };
    capturedHandler(completedData);

    expect(onExpeditionCompleted).toHaveBeenCalledWith(completedData);
  });

  it('should call onExpeditionCreated when expedition is created', () => {
    const onExpeditionCreated = vi.fn();
    let capturedHandler: any;

    vi.mocked(websocketService.on).mockImplementation((event, handler) => {
      if (event === 'expeditionCreated') {
        capturedHandler = handler;
      }
    });

    renderHook(() =>
      useExpeditionRealTime({
        enabled: true,
        onExpeditionCreated,
      })
    );

    const createdData = { type: 'EXPEDITION_CREATED', expeditionId: 3 };
    capturedHandler(createdData);

    expect(onExpeditionCreated).toHaveBeenCalledWith(createdData);
  });

  it('should log events to console', () => {
    const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    let capturedHandler: any;

    vi.mocked(websocketService.on).mockImplementation((event, handler) => {
      if (event === 'expeditionUpdate') {
        capturedHandler = handler;
      }
    });

    renderHook(() =>
      useExpeditionRealTime({
        enabled: true,
      })
    );

    const updateData = { type: 'EXPEDITION_UPDATED', expeditionId: 1 };
    capturedHandler(updateData);

    expect(consoleLogSpy).toHaveBeenCalledWith('Real-time expedition update:', updateData);

    consoleLogSpy.mockRestore();
  });

  it('should handle missing callbacks gracefully', () => {
    let capturedHandler: any;

    vi.mocked(websocketService.on).mockImplementation((event, handler) => {
      if (event === 'expeditionUpdate') {
        capturedHandler = handler;
      }
    });

    renderHook(() =>
      useExpeditionRealTime({
        enabled: true,
        // No callbacks provided
      })
    );

    // Should not throw when handler is called without callback
    expect(() => {
      capturedHandler({ type: 'EXPEDITION_UPDATED', expeditionId: 1 });
    }).not.toThrow();
  });

  it('should resubscribe when enabled changes from false to true', () => {
    const { rerender } = renderHook(
      ({ enabled }) => useExpeditionRealTime({ enabled }),
      { initialProps: { enabled: false } }
    );

    expect(websocketService.on).not.toHaveBeenCalled();

    rerender({ enabled: true });

    expect(websocketService.on).toHaveBeenCalledTimes(4);
  });
});
