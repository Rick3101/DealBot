import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';

/**
 * Integration Test Helpers
 *
 * Utilities for testing container components with full provider setup
 */

// Mock WebSocket for integration tests
export const mockWebSocket = () => {
  const mockSocket = {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: WebSocket.OPEN,
  };

  global.WebSocket = vi.fn(() => mockSocket as any) as any;

  return mockSocket;
};

// Provider wrapper for integration tests
interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({ children }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
};

// Custom render for integration tests
export const renderWithProviders = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, { wrapper: AllTheProviders, ...options });
};

// Mock navigation for integration tests
export const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: '1' }),
  };
});

// API mock helpers for integration tests
export const createMockApiResponse = <T,>(data: T, delay = 0): Promise<T> => {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), delay);
  });
};

export const createMockApiError = (message: string, delay = 0): Promise<never> => {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error(message)), delay);
  });
};

// Wait for async updates
export const waitForAsync = (ms = 0) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Mock expedition data for integration tests
export const mockExpedition = {
  id: 1,
  name: 'Test Expedition',
  description: 'Test description',
  status: 'active' as const,
  deadline: '2025-12-31',
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  items: [
    {
      id: 1,
      product_id: 1,
      product_name: 'Test Product',
      quantity: 10,
      consumed: 3,
      quality_grade: 'B' as const,
      unit_price: 100,
    },
  ],
  consumptions: [
    {
      id: 1,
      expedition_id: 1,
      product_id: 1,
      consumer_name: 'TestPirate',
      quantity: 3,
      price: 100,
      consumed_at: '2025-01-02',
    },
  ],
  progress: {
    total_items: 10,
    total_consumed: 3,
    total_remaining: 7,
    total_value: 1000,
    total_cost: 700,
    completion_percentage: 30,
  },
};

// Mock product data
export const mockProducts = [
  {
    id: 1,
    name: 'Product 1',
    emoji: '📦',
    price: 100,
    is_hidden: false,
  },
  {
    id: 2,
    name: 'Product 2',
    emoji: '🎁',
    price: 200,
    is_hidden: false,
  },
];

// Mock timeline data
export const mockTimelineData = {
  active: 5,
  completed: 10,
  overdue: 2,
  total: 17,
};

// Mock pirate names
export const mockPirateNames = [
  { pirate_name: 'BlackBeard', product_count: 5 },
  { pirate_name: 'RedRum', product_count: 3 },
];

// Mock buyers
export const mockBuyers = [
  { username: 'buyer1' },
  { username: 'buyer2' },
  { username: 'buyer3' },
];
