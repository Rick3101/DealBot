import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Cleanup after each test case
afterEach(() => {
  cleanup();
});

// Mock Telegram WebApp API
(global as any).Telegram = {
  WebApp: {
    initDataUnsafe: {
      user: {
        id: 123456,
        first_name: 'Test',
        last_name: 'User',
        username: 'testuser'
      }
    },
    ready: () => {},
    expand: () => {},
    close: () => {},
    MainButton: {
      setText: () => {},
      show: () => {},
      hide: () => {},
      onClick: () => {},
      offClick: () => {}
    },
    BackButton: {
      show: () => {},
      hide: () => {},
      onClick: () => {},
      offClick: () => {}
    },
    showAlert: () => {},
    showConfirm: () => {},
    showPopup: () => {},
    themeParams: {
      bg_color: '#ffffff',
      text_color: '#000000',
      hint_color: '#999999',
      link_color: '#2481cc',
      button_color: '#2481cc',
      button_text_color: '#ffffff'
    }
  }
} as any;
