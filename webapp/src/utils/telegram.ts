import { TelegramWebApp, WebAppUser } from '@/types/telegram';

class TelegramWebAppService {
  private webApp: TelegramWebApp | null = null;
  private isInitialized = false;

  constructor() {
    this.initializeWebApp();
  }

  private initializeWebApp(): void {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      this.webApp = window.Telegram.WebApp;
      this.setupWebApp();
      this.isInitialized = true;
    } else {
      console.warn('Telegram WebApp is not available - running in development mode');
      // In development, create a mock user for testing
      if (import.meta.env.DEV) {
        console.log('Development mode: Using mock Telegram data');
      }
    }
  }

  private setupWebApp(): void {
    if (!this.webApp) return;

    try {
      // Configure WebApp
      this.webApp.ready();
      this.webApp.expand();

      // Set theme colors for pirate theme
      this.webApp.setHeaderColor('#8B4513');
      this.webApp.setBackgroundColor('#F5DEB3');

      // Enable closing confirmation for important actions
      this.webApp.enableClosingConfirmation();

      // Configure main button
      this.webApp.MainButton.setParams({
        color: '#DAA520',
        text_color: '#FFFFFF',
        is_active: true,
        is_visible: false
      });

      // Set up haptic feedback
      this.setupHapticFeedback();

      console.log('Telegram WebApp initialized successfully');
    } catch (error) {
      console.error('Error setting up Telegram WebApp:', error);
    }
  }

  private setupHapticFeedback(): void {
    // Haptic feedback is now called explicitly where needed
    // Removed global click listener to prevent issues with preventDefault
  }

  // Public methods
  public isAvailable(): boolean {
    return this.isInitialized && this.webApp !== null;
  }

  public getWebApp(): TelegramWebApp | null {
    return this.webApp;
  }

  public getUser(): WebAppUser | null {
    try {
      return this.webApp?.initDataUnsafe?.user || null;
    } catch (error) {
      console.error('getUser: Error accessing user data:', error);
      return null;
    }
  }

  public getUserId(): number | null {
    try {
      const user = this.getUser();
      if (user?.id) {
        return user.id;
      }

      // Fallback for when Telegram is not available
      if (import.meta.env.DEV) {
        console.warn('getUserId: Using mock owner ID for development (Morty)');
        return 5094426438; // Mock owner ID for development
      }

      console.warn('getUserId: No user ID available (Telegram not initialized)');
      return null;
    } catch (error) {
      console.error('getUserId: Error getting user ID:', error);
      return null;
    }
  }

  public getInitData(): string {
    try {
      return this.webApp?.initData || '';
    } catch (error) {
      console.error('getInitData: Error accessing initData:', error);
      return '';
    }
  }

  public getChatId(): number | null {
    try {
      const user = this.getUser();
      if (user?.id) {
        return user.id;
      }

      // Fallback for when Telegram is not available
      if (import.meta.env.DEV) {
        console.warn('getChatId: Using mock owner chat ID for development (Morty)');
        return 5094426438; // Mock owner chat ID for development
      }

      console.warn('getChatId: No chat ID available (Telegram not initialized)');
      return null;
    } catch (error) {
      console.error('getChatId: Error getting chat ID:', error);
      return null;
    }
  }

  public getStartParam(): string | null {
    return this.webApp?.initDataUnsafe?.start_param || null;
  }

  public showMainButton(text: string, onClick: () => void): void {
    if (!this.webApp) return;

    this.webApp.MainButton
      .setText(text)
      .onClick(onClick)
      .show();
  }

  public hideMainButton(): void {
    if (!this.webApp) return;
    this.webApp.MainButton.hide();
  }

  public showBackButton(onClick: () => void): void {
    if (!this.webApp) return;

    this.webApp.BackButton
      .onClick(onClick)
      .show();
  }

  public hideBackButton(): void {
    if (!this.webApp) return;
    this.webApp.BackButton.hide();
  }

  public hapticFeedback(type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' = 'light'): void {
    if (!this.webApp?.HapticFeedback) return;

    try {
      if (type === 'success' || type === 'warning' || type === 'error') {
        this.webApp.HapticFeedback.notificationOccurred(type);
      } else {
        this.webApp.HapticFeedback.impactOccurred(type);
      }
    } catch (error) {
      console.warn('Haptic feedback not supported:', error);
    }
  }

  public showAlert(message: string): Promise<void> {
    return new Promise((resolve) => {
      if (!this.webApp) {
        alert(message);
        resolve();
        return;
      }

      this.webApp.showAlert(message, () => {
        resolve();
      });
    });
  }

  public showConfirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.webApp) {
        resolve(confirm(message));
        return;
      }

      this.webApp.showConfirm(message, (confirmed) => {
        resolve(confirmed);
      });
    });
  }

  public showPopup(title: string, message: string, buttons?: Array<{id: string, text: string, type?: 'default' | 'ok' | 'close' | 'cancel' | 'destructive'}>): Promise<string | null> {
    return new Promise((resolve) => {
      if (!this.webApp) {
        alert(`${title}\n\n${message}`);
        resolve('ok');
        return;
      }

      const popupButtons = buttons || [{ id: 'ok', text: 'OK', type: 'default' as const }];

      this.webApp.showPopup({
        title,
        message,
        buttons: popupButtons
      }, (buttonId) => {
        resolve(buttonId || null);
      });
    });
  }

  public openLink(url: string, tryInstantView = false): void {
    if (!this.webApp) {
      window.open(url, '_blank');
      return;
    }

    this.webApp.openLink(url, { try_instant_view: tryInstantView });
  }

  public sendData(data: any): void {
    if (!this.webApp) {
      console.warn('Cannot send data: Telegram WebApp not available');
      return;
    }

    const dataString = typeof data === 'string' ? data : JSON.stringify(data);
    this.webApp.sendData(dataString);
  }

  public close(): void {
    if (!this.webApp) return;
    this.webApp.close();
  }

  // Cloud storage helpers
  public setCloudStorage(key: string, value: string): Promise<boolean> {
    return new Promise((resolve) => {
      // Check if Cloud Storage is available and supported
      if (!this.webApp?.CloudStorage) {
        console.warn('[CloudStorage] Not available, using localStorage fallback');
        try {
          localStorage.setItem(key, value);
          resolve(true);
        } catch (e) {
          console.error('[CloudStorage] localStorage fallback failed:', e);
          resolve(false);
        }
        return;
      }

      // Check if method is supported (version >= 6.9)
      if (!this.isVersionAtLeast('6.9')) {
        console.warn('[CloudStorage] Telegram version too old (< 6.9), using localStorage fallback');
        try {
          localStorage.setItem(key, value);
          resolve(true);
        } catch (e) {
          console.error('[CloudStorage] localStorage fallback failed:', e);
          resolve(false);
        }
        return;
      }

      // Try Cloud Storage with error handling
      try {
        this.webApp.CloudStorage.setItem(key, value, (error, stored) => {
          if (error) {
            console.warn('[CloudStorage] setItem failed:', error, '- falling back to localStorage');
            try {
              localStorage.setItem(key, value);
              resolve(true); // Fallback succeeded
            } catch (e) {
              console.error('[CloudStorage] localStorage fallback failed:', e);
              resolve(false);
            }
          } else {
            console.log('[CloudStorage] Successfully saved to Telegram Cloud Storage');
            resolve(stored || false);
          }
        });
      } catch (error) {
        console.warn('[CloudStorage] Exception during setItem:', error, '- falling back to localStorage');
        try {
          localStorage.setItem(key, value);
          resolve(true);
        } catch (e) {
          console.error('[CloudStorage] localStorage fallback failed:', e);
          resolve(false);
        }
      }
    });
  }

  public getCloudStorage(key: string): Promise<string | null> {
    return new Promise((resolve) => {
      // Check if Cloud Storage is available
      if (!this.webApp?.CloudStorage) {
        console.warn('[CloudStorage] Not available, using localStorage fallback');
        try {
          resolve(localStorage.getItem(key));
        } catch (e) {
          console.error('[CloudStorage] localStorage fallback failed:', e);
          resolve(null);
        }
        return;
      }

      // Check if method is supported (version >= 6.9)
      if (!this.isVersionAtLeast('6.9')) {
        console.warn('[CloudStorage] Telegram version too old (< 6.9), using localStorage fallback');
        try {
          resolve(localStorage.getItem(key));
        } catch (e) {
          console.error('[CloudStorage] localStorage fallback failed:', e);
          resolve(null);
        }
        return;
      }

      // Try Cloud Storage with error handling
      try {
        this.webApp.CloudStorage.getItem(key, (error, value) => {
          if (error) {
            console.warn('[CloudStorage] getItem failed:', error, '- falling back to localStorage');
            try {
              resolve(localStorage.getItem(key));
            } catch (e) {
              console.error('[CloudStorage] localStorage fallback failed:', e);
              resolve(null);
            }
          } else {
            console.log('[CloudStorage] Successfully retrieved from Telegram Cloud Storage');
            resolve(value || null);
          }
        });
      } catch (error) {
        console.warn('[CloudStorage] Exception during getItem:', error, '- falling back to localStorage');
        try {
          resolve(localStorage.getItem(key));
        } catch (e) {
          console.error('[CloudStorage] localStorage fallback failed:', e);
          resolve(null);
        }
      }
    });
  }

  // Check if Cloud Storage is supported
  public isCloudStorageSupported(): boolean {
    return !!(this.webApp?.CloudStorage && this.isVersionAtLeast('6.9'));
  }

  // Theme helpers
  public getThemeParams(): Record<string, string> {
    if (!this.webApp) {
      return {
        bg_color: '#F5DEB3',
        text_color: '#8B4513',
        hint_color: '#999999',
        link_color: '#DAA520',
        button_color: '#8B4513',
        button_text_color: '#F5DEB3',
        secondary_bg_color: '#F4E4BC'
      };
    }

    return (this.webApp.themeParams || {}) as Record<string, string>;
  }

  public isDarkMode(): boolean {
    return this.webApp?.colorScheme === 'dark';
  }

  public getViewportHeight(): number {
    return this.webApp?.viewportHeight || window.innerHeight;
  }

  public getStableViewportHeight(): number {
    return this.webApp?.viewportStableHeight || window.innerHeight;
  }

  // Version checking
  public isVersionAtLeast(version: string): boolean {
    return this.webApp?.isVersionAtLeast(version) || false;
  }

  // Event handling
  public onMainButtonClick(callback: () => void): void {
    if (!this.webApp) return;
    this.webApp.MainButton.onClick(callback);
  }

  public onBackButtonClick(callback: () => void): void {
    if (!this.webApp) return;
    this.webApp.BackButton.onClick(callback);
  }

  public onViewportChanged(callback: () => void): void {
    if (!this.webApp) return;
    this.webApp.onEvent('viewportChanged', callback);
  }

  public onThemeChanged(callback: () => void): void {
    if (!this.webApp) return;
    this.webApp.onEvent('themeChanged', callback);
  }

  // Utility methods
  public validateInitData(): boolean {
    const initData = this.getInitData();
    const user = this.getUser();

    return !!(initData && user && user.id);
  }

  public getAuthHeaders(): Record<string, string> {
    const chatId = this.getChatId();
    const initData = this.getInitData();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (chatId) {
      headers['X-Chat-ID'] = chatId.toString();
    }

    if (initData) {
      headers['X-Telegram-Init-Data'] = initData;
    }

    return headers;
  }

  public formatUserDisplay(): string {
    const user = this.getUser();
    if (!user) {
      // In development mode, return mock user display
      if (import.meta.env.DEV) {
        return 'Morty (Dev Mode)';
      }
      return 'Unknown User';
    }

    const parts = [];
    if (user.first_name) parts.push(user.first_name);
    if (user.last_name) parts.push(user.last_name);

    if (parts.length === 0 && user.username) {
      return `@${user.username}`;
    }

    return parts.join(' ') || 'User';
  }
}

// Create singleton instance
export const telegramWebApp = new TelegramWebAppService();

// Export utility functions with proper binding
export const isAvailable = () => telegramWebApp.isAvailable();
export const getUser = () => telegramWebApp.getUser();
export const getUserId = () => telegramWebApp.getUserId();
export const getChatId = () => telegramWebApp.getChatId();
export const getInitData = () => telegramWebApp.getInitData();
export const showMainButton = (text: string, onClick: () => void) => telegramWebApp.showMainButton(text, onClick);
export const hideMainButton = () => telegramWebApp.hideMainButton();
export const showBackButton = (onClick: () => void) => telegramWebApp.showBackButton(onClick);
export const hideBackButton = () => telegramWebApp.hideBackButton();
export const hapticFeedback = (type?: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error') => telegramWebApp.hapticFeedback(type);
export const showAlert = (message: string) => telegramWebApp.showAlert(message);
export const showConfirm = (message: string) => telegramWebApp.showConfirm(message);
export const showPopup = (title: string, message: string, buttons?: Array<{id: string, text: string, type?: 'default' | 'ok' | 'close' | 'cancel' | 'destructive'}>) => telegramWebApp.showPopup(title, message, buttons);
export const openLink = (url: string, tryInstantView?: boolean) => telegramWebApp.openLink(url, tryInstantView);
export const close = () => telegramWebApp.close();
export const getAuthHeaders = () => telegramWebApp.getAuthHeaders();
export const validateInitData = () => telegramWebApp.validateInitData();
export const formatUserDisplay = () => telegramWebApp.formatUserDisplay();
export const isDarkMode = () => telegramWebApp.isDarkMode();
export const getThemeParams = () => telegramWebApp.getThemeParams();
export const isCloudStorageSupported = () => telegramWebApp.isCloudStorageSupported();