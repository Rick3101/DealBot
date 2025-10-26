import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, Mock, afterEach } from 'vitest';
import { useAppInitialization, useTelegramFeatures } from './useAppInitialization';
import * as telegramModule from '@/utils/telegram';
import * as loggerModule from '@/services/loggerService';

// Mock dependencies
vi.mock('@/utils/telegram', () => ({
  telegramWebApp: {
    isAvailable: vi.fn(),
    getWebApp: vi.fn(),
  },
  validateInitData: vi.fn(),
}));

vi.mock('@/services/loggerService', () => ({
  logger: {
    info: vi.fn().mockResolvedValue(undefined),
    warn: vi.fn().mockResolvedValue(undefined),
    error: vi.fn().mockResolvedValue(undefined),
  },
}));

describe('useAppInitialization', () => {
  const mockWebApp = {
    ready: vi.fn(),
    expand: vi.fn(),
    setHeaderColor: vi.fn(),
    enableClosingConfirmation: vi.fn(),
    MainButton: {
      setText: vi.fn(),
      show: vi.fn(),
      hide: vi.fn(),
      onClick: vi.fn(),
    },
    BackButton: {
      show: vi.fn(),
      hide: vi.fn(),
      onClick: vi.fn(),
    },
    HapticFeedback: {
      impactOccurred: vi.fn(),
      notificationOccurred: vi.fn(),
    },
    close: vi.fn(),
    initDataUnsafe: {
      user: {
        id: 123,
        first_name: 'Test',
        last_name: 'User',
        username: 'testuser',
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(false);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(null);
    (telegramModule.validateInitData as Mock).mockReturnValue(true);
    document.body.className = '';
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with loading state', () => {
    const { result } = renderHook(() =>
      useAppInitialization({ loadingDelay: 0 })
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isInitialized).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.telegramAvailable).toBe(false);
  });

  it('should initialize successfully in standalone mode', async () => {
    const { result } = renderHook(() =>
      useAppInitialization({ loadingDelay: 0 })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isInitialized).toBe(true);
    expect(result.current.telegramAvailable).toBe(false);
    expect(result.current.error).toBeNull();
    expect(document.body.classList.contains('app-ready')).toBe(true);
  });

  it('should initialize successfully with Telegram WebApp', async () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);
    (telegramModule.validateInitData as Mock).mockReturnValue(true);

    const { result } = renderHook(() =>
      useAppInitialization({ loadingDelay: 0 })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isInitialized).toBe(true);
    expect(result.current.telegramAvailable).toBe(true);
    expect(mockWebApp.ready).toHaveBeenCalled();
    expect(mockWebApp.expand).toHaveBeenCalled();
    expect(mockWebApp.setHeaderColor).toHaveBeenCalledWith('#F5E6D3');
    expect(mockWebApp.enableClosingConfirmation).toHaveBeenCalled();
  });

  it('should handle loading delay', async () => {
    const { result } = renderHook(() =>
      useAppInitialization({ loadingDelay: 50 })
    );

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    }, { timeout: 1000 });

    expect(result.current.isInitialized).toBe(true);
  });

  it('should handle validation failure with strict validation', async () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.validateInitData as Mock).mockReturnValue(false);

    const { result } = renderHook(() =>
      useAppInitialization({ loadingDelay: 0, strictValidation: true })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isInitialized).toBe(false);
    expect(result.current.error).toBe('Telegram data validation failed');
    expect(result.current.telegramAvailable).toBe(false);
  });

  it('should continue despite validation failure without strict validation', async () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);
    (telegramModule.validateInitData as Mock).mockReturnValue(false);

    const { result } = renderHook(() =>
      useAppInitialization({ loadingDelay: 0, strictValidation: false })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isInitialized).toBe(true);
    expect(result.current.telegramAvailable).toBe(true);
    expect(loggerModule.logger.warn).toHaveBeenCalled();
  });

  it('should call onSuccess callback when initialization succeeds', async () => {
    const onSuccess = vi.fn();

    renderHook(() =>
      useAppInitialization({ loadingDelay: 0, onSuccess })
    );

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it('should call onError callback when initialization fails', async () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.validateInitData as Mock).mockReturnValue(false);

    const onError = vi.fn();

    renderHook(() =>
      useAppInitialization({ loadingDelay: 0, strictValidation: true, onError })
    );

    await waitFor(() => {
      expect(onError).toHaveBeenCalledTimes(1);
    });

    expect(onError).toHaveBeenCalledWith(expect.any(Error));
  });

  it('should support retry functionality', async () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.validateInitData as Mock).mockReturnValue(false);

    const { result } = renderHook(() =>
      useAppInitialization({ loadingDelay: 0, strictValidation: true })
    );

    await waitFor(() => {
      expect(result.current.isInitialized).toBe(false);
    });

    expect(result.current.error).toBe('Telegram data validation failed');

    // Fix the validation and retry
    (telegramModule.validateInitData as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    act(() => {
      result.current.retry();
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isInitialized).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should add app-ready class to body on successful initialization', async () => {
    expect(document.body.classList.contains('app-ready')).toBe(false);

    renderHook(() =>
      useAppInitialization({ loadingDelay: 0 })
    );

    await waitFor(() => {
      expect(document.body.classList.contains('app-ready')).toBe(true);
    });
  });

  it('should log initialization steps', async () => {
    renderHook(() =>
      useAppInitialization({ loadingDelay: 0 })
    );

    await waitFor(() => {
      expect(loggerModule.logger.info).toHaveBeenCalledWith(
        'Initializing Pirates Expedition Mini App',
        'useAppInitialization'
      );
    });
  });
});

describe('useTelegramFeatures', () => {
  const mockWebApp = {
    MainButton: {
      setText: vi.fn(),
      show: vi.fn(),
      hide: vi.fn(),
      onClick: vi.fn(),
    },
    BackButton: {
      show: vi.fn(),
      hide: vi.fn(),
      onClick: vi.fn(),
    },
    HapticFeedback: {
      impactOccurred: vi.fn(),
      notificationOccurred: vi.fn(),
    },
    close: vi.fn(),
    initDataUnsafe: {
      user: {
        id: 123,
        first_name: 'Test',
        last_name: 'User',
        username: 'testuser',
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return isAvailable as false when Telegram is not available', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(false);

    const { result } = renderHook(() => useTelegramFeatures());

    expect(result.current.isAvailable).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('should return isAvailable as true when Telegram is available', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result } = renderHook(() => useTelegramFeatures());

    expect(result.current.isAvailable).toBe(true);
  });

  it('should provide user info when available', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result } = renderHook(() => useTelegramFeatures());

    expect(result.current.user).toEqual({
      id: 123,
      firstName: 'Test',
      lastName: 'User',
      username: 'testuser',
    });
  });

  it('should show main button', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result } = renderHook(() => useTelegramFeatures());
    const onClick = vi.fn();

    result.current.showMainButton('Submit', onClick);

    expect(mockWebApp.MainButton.setText).toHaveBeenCalledWith('Submit');
    expect(mockWebApp.MainButton.show).toHaveBeenCalled();
    expect(mockWebApp.MainButton.onClick).toHaveBeenCalledWith(onClick);
  });

  it('should hide main button', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result } = renderHook(() => useTelegramFeatures());

    result.current.hideMainButton();

    expect(mockWebApp.MainButton.hide).toHaveBeenCalled();
  });

  it('should show back button', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result } = renderHook(() => useTelegramFeatures());
    const onClick = vi.fn();

    result.current.showBackButton(onClick);

    expect(mockWebApp.BackButton.show).toHaveBeenCalled();
    expect(mockWebApp.BackButton.onClick).toHaveBeenCalledWith(onClick);
  });

  it('should hide back button', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result } = renderHook(() => useTelegramFeatures());

    result.current.hideBackButton();

    expect(mockWebApp.BackButton.hide).toHaveBeenCalled();
  });

  it('should trigger impact haptic feedback', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result } = renderHook(() => useTelegramFeatures());

    result.current.haptic('light');
    expect(mockWebApp.HapticFeedback.impactOccurred).toHaveBeenCalledWith('light');

    result.current.haptic('medium');
    expect(mockWebApp.HapticFeedback.impactOccurred).toHaveBeenCalledWith('medium');

    result.current.haptic('heavy');
    expect(mockWebApp.HapticFeedback.impactOccurred).toHaveBeenCalledWith('heavy');
  });

  it('should trigger notification haptic feedback', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result} = renderHook(() => useTelegramFeatures());

    result.current.haptic('success');
    expect(mockWebApp.HapticFeedback.notificationOccurred).toHaveBeenCalledWith('success');

    result.current.haptic('warning');
    expect(mockWebApp.HapticFeedback.notificationOccurred).toHaveBeenCalledWith('warning');

    result.current.haptic('error');
    expect(mockWebApp.HapticFeedback.notificationOccurred).toHaveBeenCalledWith('error');
  });

  it('should close mini app', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(true);
    (telegramModule.telegramWebApp.getWebApp as Mock).mockReturnValue(mockWebApp);

    const { result } = renderHook(() => useTelegramFeatures());

    result.current.close();

    expect(mockWebApp.close).toHaveBeenCalled();
  });

  it('should handle missing WebApp gracefully', () => {
    (telegramModule.telegramWebApp.isAvailable as Mock).mockReturnValue(false);

    const { result } = renderHook(() => useTelegramFeatures());

    // Should not throw errors
    expect(() => result.current.showMainButton('Test', vi.fn())).not.toThrow();
    expect(() => result.current.hideMainButton()).not.toThrow();
    expect(() => result.current.showBackButton(vi.fn())).not.toThrow();
    expect(() => result.current.hideBackButton()).not.toThrow();
    expect(() => result.current.haptic('light')).not.toThrow();
    expect(() => result.current.close()).not.toThrow();
  });
});
