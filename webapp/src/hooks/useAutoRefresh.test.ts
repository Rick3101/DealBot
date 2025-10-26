import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAutoRefresh } from './useAutoRefresh';

describe('useAutoRefresh', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should call onRefresh at specified intervals when enabled', () => {
    const onRefresh = vi.fn();

    renderHook(() =>
      useAutoRefresh({
        enabled: true,
        interval: 1000,
        onRefresh,
      })
    );

    // Should not call immediately
    expect(onRefresh).not.toHaveBeenCalled();

    // Advance time by 1 second
    vi.advanceTimersByTime(1000);
    expect(onRefresh).toHaveBeenCalledTimes(1);

    // Advance time by another second
    vi.advanceTimersByTime(1000);
    expect(onRefresh).toHaveBeenCalledTimes(2);

    // Advance time by 3 more seconds
    vi.advanceTimersByTime(3000);
    expect(onRefresh).toHaveBeenCalledTimes(5);
  });

  it('should not call onRefresh when disabled', () => {
    const onRefresh = vi.fn();

    renderHook(() =>
      useAutoRefresh({
        enabled: false,
        interval: 1000,
        onRefresh,
      })
    );

    vi.advanceTimersByTime(5000);
    expect(onRefresh).not.toHaveBeenCalled();
  });

  it('should use default interval of 30 seconds', () => {
    const onRefresh = vi.fn();

    renderHook(() =>
      useAutoRefresh({
        enabled: true,
        onRefresh,
      })
    );

    // Should not trigger before 30 seconds
    vi.advanceTimersByTime(29000);
    expect(onRefresh).not.toHaveBeenCalled();

    // Should trigger at 30 seconds
    vi.advanceTimersByTime(1000);
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('should cleanup interval on unmount', () => {
    const onRefresh = vi.fn();

    const { unmount } = renderHook(() =>
      useAutoRefresh({
        enabled: true,
        interval: 1000,
        onRefresh,
      })
    );

    vi.advanceTimersByTime(1000);
    expect(onRefresh).toHaveBeenCalledTimes(1);

    unmount();

    // After unmount, should not call onRefresh
    vi.advanceTimersByTime(5000);
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('should restart interval when interval changes', () => {
    const onRefresh = vi.fn();

    const { rerender } = renderHook(
      ({ interval }) => useAutoRefresh({ enabled: true, interval, onRefresh }),
      { initialProps: { interval: 1000 } }
    );

    vi.advanceTimersByTime(1000);
    expect(onRefresh).toHaveBeenCalledTimes(1);

    // Change interval to 2 seconds
    rerender({ interval: 2000 });

    vi.advanceTimersByTime(1000);
    expect(onRefresh).toHaveBeenCalledTimes(1); // Should not trigger yet

    vi.advanceTimersByTime(1000);
    expect(onRefresh).toHaveBeenCalledTimes(2); // Should trigger at 2 seconds
  });

  it('should stop interval when disabled after being enabled', () => {
    const onRefresh = vi.fn();

    const { rerender } = renderHook(
      ({ enabled }) => useAutoRefresh({ enabled, interval: 1000, onRefresh }),
      { initialProps: { enabled: true } }
    );

    vi.advanceTimersByTime(1000);
    expect(onRefresh).toHaveBeenCalledTimes(1);

    // Disable auto-refresh
    rerender({ enabled: false });

    vi.advanceTimersByTime(5000);
    expect(onRefresh).toHaveBeenCalledTimes(1); // Should not call again
  });

  it('should update onRefresh function without restarting interval', () => {
    const onRefresh1 = vi.fn();
    const onRefresh2 = vi.fn();

    const { rerender } = renderHook(
      ({ onRefresh }) => useAutoRefresh({ enabled: true, interval: 1000, onRefresh }),
      { initialProps: { onRefresh: onRefresh1 } }
    );

    vi.advanceTimersByTime(1000);
    expect(onRefresh1).toHaveBeenCalledTimes(1);
    expect(onRefresh2).not.toHaveBeenCalled();

    // Change onRefresh function
    rerender({ onRefresh: onRefresh2 });

    vi.advanceTimersByTime(1000);
    expect(onRefresh1).toHaveBeenCalledTimes(1);
    expect(onRefresh2).toHaveBeenCalledTimes(1);
  });

  it('should handle async onRefresh functions', () => {
    const onRefresh = vi.fn().mockResolvedValue(undefined);

    renderHook(() =>
      useAutoRefresh({
        enabled: true,
        interval: 1000,
        onRefresh,
      })
    );

    vi.advanceTimersByTime(1000);

    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
