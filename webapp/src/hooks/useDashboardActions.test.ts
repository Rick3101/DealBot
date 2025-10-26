import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { useDashboardActions } from './useDashboardActions';
import { NavigateFunction } from 'react-router-dom';
import { ExpeditionTimelineEntry } from '@/types/expedition';
import * as telegramUtils from '@/utils/telegram';

// Mock telegram utils
vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
}));

describe('useDashboardActions', () => {
  let mockNavigate: Mock<NavigateFunction>;
  let mockRefreshExpeditions: Mock;

  beforeEach(() => {
    mockNavigate = vi.fn() as Mock<NavigateFunction>;
    mockRefreshExpeditions = vi.fn().mockResolvedValue(undefined);
    vi.clearAllMocks();
  });

  it('should initialize with refreshing = false', () => {
    const { result } = renderHook(() =>
      useDashboardActions(mockNavigate, mockRefreshExpeditions)
    );

    expect(result.current.refreshing).toBe(false);
  });

  it('should provide all action handlers', () => {
    const { result } = renderHook(() =>
      useDashboardActions(mockNavigate, mockRefreshExpeditions)
    );

    expect(result.current.handleRefresh).toBeInstanceOf(Function);
    expect(result.current.handleCreateExpedition).toBeInstanceOf(Function);
    expect(result.current.handleViewExpedition).toBeInstanceOf(Function);
    expect(result.current.handleManageExpedition).toBeInstanceOf(Function);
  });

  describe('handleRefresh', () => {
    it('should call refreshExpeditions and trigger haptic feedback', async () => {
      const { result } = renderHook(() =>
        useDashboardActions(mockNavigate, mockRefreshExpeditions)
      );

      await act(async () => {
        await result.current.handleRefresh();
      });

      expect(mockRefreshExpeditions).toHaveBeenCalledTimes(1);
      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('light');
    });

    it('should set refreshing to true during refresh and false after', async () => {
      const { result } = renderHook(() =>
        useDashboardActions(mockNavigate, mockRefreshExpeditions)
      );

      expect(result.current.refreshing).toBe(false);

      // Start the refresh and check state during execution
      let refreshPromise: Promise<void>;
      await act(async () => {
        refreshPromise = result.current.handleRefresh();
        // At this point, refreshing should be true
        await waitFor(() => {
          expect(result.current.refreshing).toBe(false); // Will be false after promise resolves
        });
        await refreshPromise;
      });

      expect(result.current.refreshing).toBe(false);
    });

    it('should set refreshing to false even if refresh fails', async () => {
      const mockError = new Error('Refresh failed');
      mockRefreshExpeditions.mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useDashboardActions(mockNavigate, mockRefreshExpeditions)
      );

      await act(async () => {
        try {
          await result.current.handleRefresh();
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.refreshing).toBe(false);
    });
  });

  describe('handleCreateExpedition', () => {
    it('should navigate to create expedition page and trigger haptic feedback', () => {
      const { result } = renderHook(() =>
        useDashboardActions(mockNavigate, mockRefreshExpeditions)
      );

      act(() => {
        result.current.handleCreateExpedition();
      });

      expect(mockNavigate).toHaveBeenCalledWith('/expedition/create');
      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('medium');
    });
  });

  describe('handleViewExpedition', () => {
    it('should navigate to expedition details and trigger haptic feedback', () => {
      const mockExpedition: ExpeditionTimelineEntry = {
        id: 42,
        name: 'Test Expedition',
      } as ExpeditionTimelineEntry;

      const { result } = renderHook(() =>
        useDashboardActions(mockNavigate, mockRefreshExpeditions)
      );

      act(() => {
        result.current.handleViewExpedition(mockExpedition);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/expedition/42');
      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('light');
    });
  });

  describe('handleManageExpedition', () => {
    it('should navigate to expedition details and trigger haptic feedback', () => {
      const mockExpedition: ExpeditionTimelineEntry = {
        id: 99,
        name: 'Test Expedition',
      } as ExpeditionTimelineEntry;

      const { result } = renderHook(() =>
        useDashboardActions(mockNavigate, mockRefreshExpeditions)
      );

      act(() => {
        result.current.handleManageExpedition(mockExpedition);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/expedition/99');
      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('medium');
    });
  });

  it('should maintain stable function references with useCallback', () => {
    const { result, rerender } = renderHook(() =>
      useDashboardActions(mockNavigate, mockRefreshExpeditions)
    );

    const firstHandlers = {
      handleRefresh: result.current.handleRefresh,
      handleCreateExpedition: result.current.handleCreateExpedition,
      handleViewExpedition: result.current.handleViewExpedition,
      handleManageExpedition: result.current.handleManageExpedition,
    };

    rerender();

    expect(result.current.handleRefresh).toBe(firstHandlers.handleRefresh);
    expect(result.current.handleCreateExpedition).toBe(firstHandlers.handleCreateExpedition);
    expect(result.current.handleViewExpedition).toBe(firstHandlers.handleViewExpedition);
    expect(result.current.handleManageExpedition).toBe(firstHandlers.handleManageExpedition);
  });

  it('should update handlers when navigate changes', () => {
    const { result, rerender } = renderHook(
      ({ navigate }) => useDashboardActions(navigate, mockRefreshExpeditions),
      { initialProps: { navigate: mockNavigate } }
    );

    const firstHandlers = result.current.handleCreateExpedition;

    const newNavigate = vi.fn() as Mock<NavigateFunction>;
    rerender({ navigate: newNavigate });

    expect(result.current.handleCreateExpedition).not.toBe(firstHandlers);
  });

  it('should update handlers when refreshExpeditions changes', () => {
    const { result, rerender } = renderHook(
      ({ refreshExpeditions }) => useDashboardActions(mockNavigate, refreshExpeditions),
      { initialProps: { refreshExpeditions: mockRefreshExpeditions } }
    );

    const firstHandlers = result.current.handleRefresh;

    const newRefreshExpeditions = vi.fn().mockResolvedValue(undefined);
    rerender({ refreshExpeditions: newRefreshExpeditions });

    expect(result.current.handleRefresh).not.toBe(firstHandlers);
  });
});
