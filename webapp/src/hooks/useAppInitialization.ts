/**
 * useAppInitialization Hook
 *
 * Handles application initialization logic including Telegram validation,
 * WebApp configuration, and loading states.
 */

import { useState, useEffect } from 'react';
import { telegramWebApp, validateInitData } from '@/utils/telegram';
import { logger } from '@/services/loggerService';

export interface AppInitializationState {
  /**
   * Whether app is still loading
   */
  isLoading: boolean;

  /**
   * Whether initialization completed successfully
   */
  isInitialized: boolean;

  /**
   * Initialization error if any
   */
  error: Error | null;

  /**
   * Whether Telegram WebApp is available
   */
  telegramAvailable: boolean;

  /**
   * Retry initialization
   */
  retry: () => void;
}

export interface AppInitializationOptions {
  /**
   * Simulated loading delay in ms
   */
  loadingDelay?: number;

  /**
   * Whether to validate Telegram data strictly
   */
  strictValidation?: boolean;

  /**
   * Callback when initialization succeeds
   */
  onSuccess?: () => void;

  /**
   * Callback when initialization fails
   */
  onError?: (error: Error) => void;
}

/**
 * Hook for app initialization
 *
 * @param options - Initialization options
 * @returns Initialization state and controls
 */
export function useAppInitialization(
  options: AppInitializationOptions = {}
): AppInitializationState {
  const {
    loadingDelay = 1500,
    strictValidation = false,
    onSuccess,
    onError,
  } = options;

  const [state, setState] = useState<{
    isLoading: boolean;
    isInitialized: boolean;
    error: Error | null;
    telegramAvailable: boolean;
  }>({
    isLoading: true,
    isInitialized: false,
    error: null,
    telegramAvailable: false,
  });

  const [retryTrigger, setRetryTrigger] = useState(0);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        console.log('[INIT] Starting initialization');
        setState(prev => ({
          ...prev,
          isLoading: true,
          error: null,
        }));

        // Log non-blocking (don't await)
        logger.info('Initializing Pirates Expedition Mini App', 'useAppInitialization');

        // Check if Telegram WebApp is available
        console.log('[INIT] Checking Telegram availability');
        const telegramAvailable = telegramWebApp.isAvailable();
        console.log('[INIT] Telegram available:', telegramAvailable);
        logger.info(`Telegram WebApp available: ${telegramAvailable}`, 'useAppInitialization');

        if (telegramAvailable) {
          console.log('[INIT] Validating Telegram data');
          // Validate init data if running in Telegram
          const isValidated = validateInitData();
          logger.info(`Telegram data validated: ${isValidated}`, 'useAppInitialization');

          if (!isValidated) {
            if (strictValidation) {
              throw new Error('Telegram data validation failed');
            } else {
              logger.warn(
                'Telegram init data validation failed, but continuing',
                'useAppInitialization'
              );
            }
          }

          console.log('[INIT] Configuring Telegram WebApp');
          // Configure Telegram WebApp
          const webApp = telegramWebApp.getWebApp();
          if (webApp) {
            webApp.ready();
            webApp.expand();

            // Set header color
            webApp.setHeaderColor('#F5E6D3'); // Parchment color

            // Enable closing confirmation
            webApp.enableClosingConfirmation();

            logger.info('Telegram WebApp configured', 'useAppInitialization');
          }
        } else {
          console.log('[INIT] Running in standalone mode');
          logger.info(
            'Running in standalone mode (not in Telegram)',
            'useAppInitialization'
          );
        }

        // Simulate loading time for better UX
        console.log('[INIT] Waiting for loading delay:', loadingDelay);
        if (loadingDelay > 0) {
          await new Promise(resolve => setTimeout(resolve, loadingDelay));
        }
        console.log('[INIT] Loading delay complete');

        console.log('[INIT] Setting state to initialized');
        setState({
          isLoading: false,
          isInitialized: true,
          error: null,
          telegramAvailable,
        });

        // Mark app as ready (removes loading screen)
        document.body.classList.add('app-ready');

        logger.info('App initialization complete', 'useAppInitialization');
        console.log('[INIT] Initialization complete!');

        onSuccess?.();
      } catch (error) {
        console.error('[INIT] Initialization error:', error);
        logger.error(
          'Failed to initialize app',
          'useAppInitialization',
          error as Error
        );

        const errorObj = error instanceof Error
          ? error
          : new Error('Failed to initialize app');

        setState({
          isLoading: false,
          isInitialized: false,
          error: errorObj,
          telegramAvailable: false,
        });

        onError?.(errorObj);
      }
    };

    initializeApp();
  }, [retryTrigger, loadingDelay, strictValidation, onSuccess, onError]);

  const retry = () => {
    setRetryTrigger(prev => prev + 1);
  };

  return {
    ...state,
    retry,
  };
}

/**
 * Hook for Telegram WebApp features
 *
 * Provides access to Telegram-specific functionality
 */
export interface TelegramFeatures {
  /**
   * Whether Telegram is available
   */
  isAvailable: boolean;

  /**
   * Show main button
   */
  showMainButton: (text: string, onClick: () => void) => void;

  /**
   * Hide main button
   */
  hideMainButton: () => void;

  /**
   * Show back button
   */
  showBackButton: (onClick: () => void) => void;

  /**
   * Hide back button
   */
  hideBackButton: () => void;

  /**
   * Trigger haptic feedback
   */
  haptic: (type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error') => void;

  /**
   * Close mini app
   */
  close: () => void;

  /**
   * Get user info
   */
  user: {
    id?: number;
    firstName?: string;
    lastName?: string;
    username?: string;
  } | null;
}

export function useTelegramFeatures(): TelegramFeatures {
  const isAvailable = telegramWebApp.isAvailable();
  const webApp = isAvailable ? telegramWebApp.getWebApp() : null;

  const showMainButton = (text: string, onClick: () => void) => {
    if (!webApp) return;

    webApp.MainButton.setText(text);
    webApp.MainButton.show();
    webApp.MainButton.onClick(onClick);
  };

  const hideMainButton = () => {
    if (!webApp) return;
    webApp.MainButton.hide();
  };

  const showBackButton = (onClick: () => void) => {
    if (!webApp) return;
    webApp.BackButton.show();
    webApp.BackButton.onClick(onClick);
  };

  const hideBackButton = () => {
    if (!webApp) return;
    webApp.BackButton.hide();
  };

  const haptic = (type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error') => {
    if (!webApp || !webApp.HapticFeedback) return;

    switch (type) {
      case 'light':
      case 'medium':
      case 'heavy':
        webApp.HapticFeedback.impactOccurred(type);
        break;
      case 'success':
      case 'warning':
      case 'error':
        webApp.HapticFeedback.notificationOccurred(type);
        break;
    }
  };

  const close = () => {
    if (!webApp) return;
    webApp.close();
  };

  const user = webApp?.initDataUnsafe?.user
    ? {
        id: webApp.initDataUnsafe.user.id,
        firstName: webApp.initDataUnsafe.user.first_name,
        lastName: webApp.initDataUnsafe.user.last_name,
        username: webApp.initDataUnsafe.user.username,
      }
    : null;

  return {
    isAvailable,
    showMainButton,
    hideMainButton,
    showBackButton,
    hideBackButton,
    haptic,
    close,
    user,
  };
}
