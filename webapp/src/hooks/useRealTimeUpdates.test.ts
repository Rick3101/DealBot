/**
 * Tests for useRealTimeUpdates facade hook
 *
 * Tests the composition of WebSocket hooks into a unified API:
 * - Hook composition
 * - Backward compatibility
 * - Prop delegation
 * - API surface
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useRealTimeUpdates } from './useRealTimeUpdates';
import type { WebSocketUpdate } from '@/types/expedition';

// Mock the composed hooks
vi.mock('./useWebSocketUpdates', () => ({
  useWebSocketUpdates: vi.fn((options) => ({
    isConnected: true,
    updates: [] as WebSocketUpdate[],
    connectionStatus: 'connected' as const,
    clearUpdates: vi.fn(),
    reconnect: vi.fn(),
  })),
}));

vi.mock('./useUpdateNotifications', () => ({
  useUpdateNotifications: vi.fn(() => ({
    notify: vi.fn(),
  })),
}));

vi.mock('./useExpeditionRoom', () => ({
  useExpeditionRoom: vi.fn(() => ({
    joinExpedition: vi.fn(),
    leaveExpedition: vi.fn(),
    rejoinAll: vi.fn(),
  })),
}));

import { useWebSocketUpdates } from './useWebSocketUpdates';
import { useUpdateNotifications } from './useUpdateNotifications';
import { useExpeditionRoom } from './useExpeditionRoom';

describe('useRealTimeUpdates', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Hook Composition', () => {
    it('should compose all three sub-hooks', () => {
      renderHook(() => useRealTimeUpdates());

      expect(useWebSocketUpdates).toHaveBeenCalled();
      expect(useUpdateNotifications).toHaveBeenCalled();
      expect(useExpeditionRoom).toHaveBeenCalled();
    });

    it('should pass notification handler to WebSocket hook', () => {
      const mockNotify = vi.fn();
      (useUpdateNotifications as any).mockReturnValue({ notify: mockNotify });

      renderHook(() => useRealTimeUpdates());

      expect(useWebSocketUpdates).toHaveBeenCalledWith(
        expect.objectContaining({
          onUpdate: mockNotify,
        })
      );
    });

    it('should pass isConnected to expedition room hook', () => {
      (useWebSocketUpdates as any).mockReturnValue({
        isConnected: true,
        updates: [],
        connectionStatus: 'connected',
        clearUpdates: vi.fn(),
        reconnect: vi.fn(),
      });

      renderHook(() => useRealTimeUpdates());

      expect(useExpeditionRoom).toHaveBeenCalledWith(
        true,
        expect.objectContaining({
          autoJoin: true,
        })
      );
    });
  });

  describe('Options Handling', () => {
    it('should use default options when none provided', () => {
      renderHook(() => useRealTimeUpdates());

      expect(useUpdateNotifications).toHaveBeenCalledWith({
        enableHaptic: true,
        enablePopups: true,
      });

      expect(useExpeditionRoom).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          autoJoin: true,
        })
      );
    });

    it('should pass custom haptic option', () => {
      renderHook(() =>
        useRealTimeUpdates(undefined, { enableHaptic: false })
      );

      expect(useUpdateNotifications).toHaveBeenCalledWith(
        expect.objectContaining({
          enableHaptic: false,
        })
      );
    });

    it('should pass custom popup option', () => {
      renderHook(() =>
        useRealTimeUpdates(undefined, { enablePopups: false })
      );

      expect(useUpdateNotifications).toHaveBeenCalledWith(
        expect.objectContaining({
          enablePopups: false,
        })
      );
    });

    it('should pass custom auto-join option', () => {
      renderHook(() =>
        useRealTimeUpdates(undefined, { autoJoinExpeditions: false })
      );

      expect(useExpeditionRoom).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          autoJoin: false,
        })
      );
    });
  });

  describe('Expedition ID Handling', () => {
    it('should pass expeditionId to room hook', () => {
      const expeditionId = 123;

      renderHook(() => useRealTimeUpdates(expeditionId));

      expect(useExpeditionRoom).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          expeditionId,
        })
      );
    });

    it('should handle undefined expeditionId', () => {
      renderHook(() => useRealTimeUpdates());

      expect(useExpeditionRoom).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          expeditionId: undefined,
        })
      );
    });
  });

  describe('Return Value', () => {
    it('should return all required properties', () => {
      const { result } = renderHook(() => useRealTimeUpdates());

      expect(result.current).toHaveProperty('isConnected');
      expect(result.current).toHaveProperty('updates');
      expect(result.current).toHaveProperty('connectionStatus');
      expect(result.current).toHaveProperty('joinExpedition');
      expect(result.current).toHaveProperty('leaveExpedition');
      expect(result.current).toHaveProperty('clearUpdates');
      expect(result.current).toHaveProperty('reconnect');
    });

    it('should delegate isConnected from WebSocket hook', () => {
      (useWebSocketUpdates as any).mockReturnValue({
        isConnected: false,
        updates: [],
        connectionStatus: 'disconnected',
        clearUpdates: vi.fn(),
        reconnect: vi.fn(),
      });

      const { result } = renderHook(() => useRealTimeUpdates());

      expect(result.current.isConnected).toBe(false);
    });

    it('should delegate updates from WebSocket hook', () => {
      const mockUpdates: WebSocketUpdate[] = [
        {
          type: 'expedition_updated',
          expedition_id: 1,
          timestamp: new Date().toISOString(),
        },
      ];

      (useWebSocketUpdates as any).mockReturnValue({
        isConnected: true,
        updates: mockUpdates,
        connectionStatus: 'connected',
        clearUpdates: vi.fn(),
        reconnect: vi.fn(),
      });

      const { result } = renderHook(() => useRealTimeUpdates());

      expect(result.current.updates).toEqual(mockUpdates);
    });

    it('should delegate connectionStatus from WebSocket hook', () => {
      (useWebSocketUpdates as any).mockReturnValue({
        isConnected: false,
        updates: [],
        connectionStatus: 'connecting',
        clearUpdates: vi.fn(),
        reconnect: vi.fn(),
      });

      const { result } = renderHook(() => useRealTimeUpdates());

      expect(result.current.connectionStatus).toBe('connecting');
    });

    it('should delegate clearUpdates from WebSocket hook', () => {
      const mockClearUpdates = vi.fn();

      (useWebSocketUpdates as any).mockReturnValue({
        isConnected: true,
        updates: [],
        connectionStatus: 'connected',
        clearUpdates: mockClearUpdates,
        reconnect: vi.fn(),
      });

      const { result } = renderHook(() => useRealTimeUpdates());

      act(() => {
        result.current.clearUpdates();
      });

      expect(mockClearUpdates).toHaveBeenCalled();
    });

    it('should delegate reconnect from WebSocket hook', () => {
      const mockReconnect = vi.fn();

      (useWebSocketUpdates as any).mockReturnValue({
        isConnected: true,
        updates: [],
        connectionStatus: 'connected',
        clearUpdates: vi.fn(),
        reconnect: mockReconnect,
      });

      const { result } = renderHook(() => useRealTimeUpdates());

      act(() => {
        result.current.reconnect();
      });

      expect(mockReconnect).toHaveBeenCalled();
    });

    it('should delegate joinExpedition from room hook', () => {
      const mockJoinExpedition = vi.fn();

      (useExpeditionRoom as any).mockReturnValue({
        joinExpedition: mockJoinExpedition,
        leaveExpedition: vi.fn(),
        rejoinAll: vi.fn(),
      });

      const { result } = renderHook(() => useRealTimeUpdates());

      act(() => {
        result.current.joinExpedition(123);
      });

      expect(mockJoinExpedition).toHaveBeenCalledWith(123);
    });

    it('should delegate leaveExpedition from room hook', () => {
      const mockLeaveExpedition = vi.fn();

      (useExpeditionRoom as any).mockReturnValue({
        joinExpedition: vi.fn(),
        leaveExpedition: mockLeaveExpedition,
        rejoinAll: vi.fn(),
      });

      const { result } = renderHook(() => useRealTimeUpdates());

      act(() => {
        result.current.leaveExpedition(123);
      });

      expect(mockLeaveExpedition).toHaveBeenCalledWith(123);
    });
  });

  describe('Backward Compatibility', () => {
    it('should maintain consistent API across versions', () => {
      const { result } = renderHook(() => useRealTimeUpdates());

      // API surface check
      const apiSurface = Object.keys(result.current).sort();

      expect(apiSurface).toEqual([
        'clearUpdates',
        'connectionStatus',
        'isConnected',
        'joinExpedition',
        'leaveExpedition',
        'reconnect',
        'updates',
      ]);
    });

    it('should work without any parameters', () => {
      const { result } = renderHook(() => useRealTimeUpdates());

      expect(result.current).toBeDefined();
      expect(result.current.isConnected).toBeDefined();
      expect(result.current.updates).toBeDefined();
    });

    it('should work with only expeditionId parameter', () => {
      const { result } = renderHook(() => useRealTimeUpdates(123));

      expect(result.current).toBeDefined();
      expect(useExpeditionRoom).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          expeditionId: 123,
        })
      );
    });
  });
});
