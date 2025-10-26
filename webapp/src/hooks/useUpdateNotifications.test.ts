import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useUpdateNotifications } from './useUpdateNotifications';
import { hapticFeedback, showAlert } from '@/utils/telegram';
import { WebSocketUpdate } from '@/types/expedition';

// Mock telegram utilities
vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
  showAlert: vi.fn(),
}));

describe('useUpdateNotifications', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should trigger haptic feedback for updates', () => {
    const { result } = renderHook(() => useUpdateNotifications());

    const update: WebSocketUpdate = {
      type: 'ITEM_CONSUMED',
      expedition_id: 1,
      expedition_name: 'Test',
      timestamp: Date.now(),
    };

    result.current.notify(update);

    expect(hapticFeedback).toHaveBeenCalledWith('light');
  });

  it('should show popup for important updates', () => {
    const { result } = renderHook(() => useUpdateNotifications());

    const update: WebSocketUpdate = {
      type: 'EXPEDITION_COMPLETED',
      expedition_id: 1,
      expedition_name: 'Test Expedition',
      timestamp: Date.now(),
    };

    result.current.notify(update);

    expect(hapticFeedback).toHaveBeenCalledWith('success');
    expect(showAlert).toHaveBeenCalledWith('Expedition "Test Expedition" has been completed!');
  });

  it('should not trigger haptic when disabled', () => {
    const { result } = renderHook(() =>
      useUpdateNotifications({ enableHaptic: false })
    );

    const update: WebSocketUpdate = {
      type: 'ITEM_CONSUMED',
      expedition_id: 1,
      expedition_name: 'Test',
      timestamp: Date.now(),
    };

    result.current.notify(update);

    expect(hapticFeedback).not.toHaveBeenCalled();
  });

  it('should not show popups when disabled', () => {
    const { result } = renderHook(() =>
      useUpdateNotifications({ enablePopups: false })
    );

    const update: WebSocketUpdate = {
      type: 'EXPEDITION_COMPLETED',
      expedition_id: 1,
      expedition_name: 'Test',
      timestamp: Date.now(),
    };

    result.current.notify(update);

    expect(showAlert).not.toHaveBeenCalled();
    expect(hapticFeedback).toHaveBeenCalled(); // Haptic still enabled
  });

  it('should handle deadline warnings with warning haptic', () => {
    const { result } = renderHook(() => useUpdateNotifications());

    const update: WebSocketUpdate = {
      type: 'DEADLINE_WARNING',
      expedition_id: 1,
      expedition_name: 'Urgent Expedition',
      timestamp: Date.now(),
    };

    result.current.notify(update);

    expect(hapticFeedback).toHaveBeenCalledWith('warning');
    expect(showAlert).toHaveBeenCalledWith('Expedition "Urgent Expedition" deadline is approaching!');
  });

  it('should handle item consumed updates', () => {
    const { result } = renderHook(() => useUpdateNotifications());

    const update: WebSocketUpdate = {
      type: 'ITEM_CONSUMED',
      expedition_id: 1,
      expedition_name: 'Test',
      pirate_name: 'Blackbeard',
      item_name: 'Rum',
      timestamp: Date.now(),
    };

    result.current.notify(update);

    expect(hapticFeedback).toHaveBeenCalledWith('light');
    expect(showAlert).toHaveBeenCalledWith('Blackbeard consumed Rum!');
  });

  it('should not show popup for expedition created (less critical)', () => {
    const { result } = renderHook(() => useUpdateNotifications());

    const update: WebSocketUpdate = {
      type: 'EXPEDITION_CREATED',
      expedition_id: 1,
      expedition_name: 'New Expedition',
      timestamp: Date.now(),
    };

    result.current.notify(update);

    expect(hapticFeedback).toHaveBeenCalledWith('light');
    expect(showAlert).not.toHaveBeenCalled(); // shouldShow is false for this type
  });

  it('should handle both options disabled', () => {
    const { result } = renderHook(() =>
      useUpdateNotifications({ enableHaptic: false, enablePopups: false })
    );

    const update: WebSocketUpdate = {
      type: 'EXPEDITION_COMPLETED',
      expedition_id: 1,
      expedition_name: 'Test',
      timestamp: Date.now(),
    };

    result.current.notify(update);

    expect(hapticFeedback).not.toHaveBeenCalled();
    expect(showAlert).not.toHaveBeenCalled();
  });
});
