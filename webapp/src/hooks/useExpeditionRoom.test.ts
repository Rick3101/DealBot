import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useExpeditionRoom } from './useExpeditionRoom';
import { websocketService } from '@/services/websocketService';

// Mock websocket service
vi.mock('@/services/websocketService', () => ({
  websocketService: {
    isConnected: vi.fn(() => true),
    joinExpedition: vi.fn(),
    leaveExpedition: vi.fn(),
  },
}));

describe('useExpeditionRoom', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should join expedition when connected and autoJoin is true', () => {
    const { result } = renderHook(() =>
      useExpeditionRoom(true, { expeditionId: 1, autoJoin: true })
    );

    expect(websocketService.joinExpedition).toHaveBeenCalledWith(1);
  });

  it('should not join expedition when autoJoin is false', () => {
    const { result } = renderHook(() =>
      useExpeditionRoom(true, { expeditionId: 1, autoJoin: false })
    );

    expect(websocketService.joinExpedition).not.toHaveBeenCalled();
  });

  it('should not join expedition when not connected', () => {
    const { result } = renderHook(() =>
      useExpeditionRoom(false, { expeditionId: 1, autoJoin: true })
    );

    expect(websocketService.joinExpedition).not.toHaveBeenCalled();
  });

  it('should leave expedition on unmount', () => {
    const { unmount } = renderHook(() =>
      useExpeditionRoom(true, { expeditionId: 1, autoJoin: true })
    );

    // Should have joined on mount
    expect(websocketService.joinExpedition).toHaveBeenCalledWith(1);

    unmount();

    // Should leave on unmount
    expect(websocketService.leaveExpedition).toHaveBeenCalledWith(1);
  });

  it('should allow manual join', () => {
    const { result } = renderHook(() => useExpeditionRoom(true));

    result.current.joinExpedition(5);

    expect(websocketService.joinExpedition).toHaveBeenCalledWith(5);
  });

  it('should allow manual leave', () => {
    const { result } = renderHook(() => useExpeditionRoom(true));

    result.current.leaveExpedition(5);

    expect(websocketService.leaveExpedition).toHaveBeenCalledWith(5);
  });

  it('should not join if websocket is not connected', () => {
    vi.mocked(websocketService.isConnected).mockReturnValue(false);
    const { result } = renderHook(() => useExpeditionRoom(true));

    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    result.current.joinExpedition(5);

    expect(websocketService.joinExpedition).not.toHaveBeenCalled();
    expect(consoleSpy).toHaveBeenCalledWith(
      'Cannot join expedition 5: WebSocket not connected'
    );

    consoleSpy.mockRestore();
  });

  it('should rejoin all previously joined expeditions', () => {
    vi.mocked(websocketService.isConnected).mockReturnValue(true);
    const { result } = renderHook(() => useExpeditionRoom(true));

    // Join multiple expeditions
    result.current.joinExpedition(1);
    result.current.joinExpedition(2);
    result.current.joinExpedition(3);

    expect(websocketService.joinExpedition).toHaveBeenCalledTimes(3);

    // Clear the mock
    vi.clearAllMocks();

    // Rejoin all
    result.current.rejoinAll();

    expect(websocketService.joinExpedition).toHaveBeenCalledTimes(3);
    expect(websocketService.joinExpedition).toHaveBeenCalledWith(1);
    expect(websocketService.joinExpedition).toHaveBeenCalledWith(2);
    expect(websocketService.joinExpedition).toHaveBeenCalledWith(3);
  });

  it('should not rejoin if not connected', () => {
    vi.mocked(websocketService.isConnected).mockReturnValue(false);
    const { result } = renderHook(() => useExpeditionRoom(true));

    result.current.rejoinAll();

    expect(websocketService.joinExpedition).not.toHaveBeenCalled();
  });

  it('should update when expeditionId changes', async () => {
    vi.mocked(websocketService.isConnected).mockReturnValue(true);

    const { rerender } = renderHook(
      ({ expeditionId }) => useExpeditionRoom(true, { expeditionId, autoJoin: true }),
      { initialProps: { expeditionId: 1 } }
    );

    expect(websocketService.joinExpedition).toHaveBeenCalledWith(1);

    // Change expedition
    rerender({ expeditionId: 2 });

    expect(websocketService.leaveExpedition).toHaveBeenCalledWith(1);
    expect(websocketService.joinExpedition).toHaveBeenCalledWith(2);
  });

  it('should join when connection is re-established', () => {
    vi.mocked(websocketService.isConnected).mockReturnValue(true);

    const { rerender } = renderHook(
      ({ isConnected }) =>
        useExpeditionRoom(isConnected, { expeditionId: 1, autoJoin: true }),
      { initialProps: { isConnected: false } }
    );

    // Not connected initially
    expect(websocketService.joinExpedition).not.toHaveBeenCalled();

    // Connection established
    rerender({ isConnected: true });

    expect(websocketService.joinExpedition).toHaveBeenCalledWith(1);
  });
});
