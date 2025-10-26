import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocketUpdates } from './useWebSocketUpdates';
import { websocketService } from '@/services/websocketService';
import { WebSocketUpdate } from '@/types/expedition';

// Mock websocket service
vi.mock('@/services/websocketService', () => ({
  websocketService: {
    on: vi.fn(),
    off: vi.fn(),
    isConnected: vi.fn(() => false),
    reconnect: vi.fn(),
  },
}));

describe('useWebSocketUpdates', () => {
  let listeners: Record<string, Function>;

  beforeEach(() => {
    vi.clearAllMocks();
    listeners = {};

    // Capture event listeners
    vi.mocked(websocketService.on).mockImplementation((event, handler) => {
      listeners[event] = handler;
    });
  });

  it('should initialize with disconnected state', () => {
    const { result } = renderHook(() => useWebSocketUpdates());

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionStatus).toBe('disconnected');
    expect(result.current.updates).toEqual([]);
  });

  it('should update connection status when connected', async () => {
    const { result } = renderHook(() => useWebSocketUpdates());

    // Trigger connected event
    listeners.connected();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
      expect(result.current.connectionStatus).toBe('connected');
    });
  });

  it('should update connection status when disconnected', async () => {
    const { result } = renderHook(() => useWebSocketUpdates());

    // Connect first
    listeners.connected();
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Then disconnect
    listeners.disconnected({});

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
      expect(result.current.connectionStatus).toBe('disconnected');
    });
  });

  it('should set error status on connection error', async () => {
    const { result } = renderHook(() => useWebSocketUpdates());

    listeners.error();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
      expect(result.current.connectionStatus).toBe('error');
    });
  });

  it('should add updates to the list', async () => {
    const { result } = renderHook(() => useWebSocketUpdates());

    const update: WebSocketUpdate = {
      type: 'ITEM_CONSUMED',
      expedition_id: 1,
      expedition_name: 'Test Expedition',
      timestamp: Date.now(),
    };

    listeners.itemConsumed(update);

    await waitFor(() => {
      expect(result.current.updates).toHaveLength(1);
      expect(result.current.updates[0]).toEqual(update);
    });
  });

  it('should limit updates to maxUpdates', async () => {
    const { result } = renderHook(() => useWebSocketUpdates({ maxUpdates: 3 }));

    // Add 5 updates
    for (let i = 0; i < 5; i++) {
      listeners.itemConsumed({
        type: 'ITEM_CONSUMED',
        expedition_id: i,
        expedition_name: `Expedition ${i}`,
        timestamp: Date.now(),
      });
    }

    await waitFor(() => {
      expect(result.current.updates).toHaveLength(3);
      // Should keep the most recent 3
      expect(result.current.updates[0].expedition_id).toBe(4);
      expect(result.current.updates[1].expedition_id).toBe(3);
      expect(result.current.updates[2].expedition_id).toBe(2);
    });
  });

  it('should call onUpdate callback when update is received', async () => {
    const onUpdate = vi.fn();
    const { result } = renderHook(() => useWebSocketUpdates({ onUpdate }));

    const update: WebSocketUpdate = {
      type: 'EXPEDITION_COMPLETED',
      expedition_id: 1,
      expedition_name: 'Test',
      timestamp: Date.now(),
    };

    listeners.expeditionCompleted(update);

    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledWith(update);
    });
  });

  it('should clear updates', async () => {
    const { result } = renderHook(() => useWebSocketUpdates());

    // Add an update
    listeners.itemConsumed({
      type: 'ITEM_CONSUMED',
      expedition_id: 1,
      expedition_name: 'Test',
      timestamp: Date.now(),
    });

    await waitFor(() => {
      expect(result.current.updates).toHaveLength(1);
    });

    // Clear updates
    result.current.clearUpdates();

    await waitFor(() => {
      expect(result.current.updates).toHaveLength(0);
    });
  });

  it('should set connecting status on reconnect', async () => {
    const { result } = renderHook(() => useWebSocketUpdates());

    result.current.reconnect();

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connecting');
    });
    expect(websocketService.reconnect).toHaveBeenCalled();
  });

  it('should register all event listeners on mount', () => {
    renderHook(() => useWebSocketUpdates());

    expect(websocketService.on).toHaveBeenCalledWith('connected', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('disconnected', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('error', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('reconnected', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('expeditionUpdate', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('itemConsumed', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('expeditionCompleted', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('expeditionCreated', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('deadlineWarning', expect.any(Function));
  });

  it('should unregister all event listeners on unmount', () => {
    const { unmount } = renderHook(() => useWebSocketUpdates());

    unmount();

    expect(websocketService.off).toHaveBeenCalledWith('connected', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith('disconnected', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith('error', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith('reconnected', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith('expeditionUpdate', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith('itemConsumed', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith('expeditionCompleted', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith('expeditionCreated', expect.any(Function));
    expect(websocketService.off).toHaveBeenCalledWith('deadlineWarning', expect.any(Function));
  });

  it('should check initial connection status on mount', () => {
    vi.mocked(websocketService.isConnected).mockReturnValue(true);

    const { result } = renderHook(() => useWebSocketUpdates());

    // Should trigger handleConnected
    expect(result.current.isConnected).toBe(true);
    expect(result.current.connectionStatus).toBe('connected');
  });
});
