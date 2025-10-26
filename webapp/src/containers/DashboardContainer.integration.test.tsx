import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DashboardContainer } from './DashboardContainer';
import {
  renderWithProviders,
  mockNavigate,
  mockExpedition,
  mockTimelineData,
} from '@/test/integration-helpers';
import * as useExpeditionsModule from '@/hooks/useExpeditions';

/**
 * Integration Tests for DashboardContainer
 *
 * Tests container component with:
 * - Real hooks composition
 * - Statistics calculation
 * - Timeline transformation
 * - User interactions
 */

describe('DashboardContainer Integration', () => {
  const mockRefreshExpeditions = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();

    // Default mock for useExpeditions
    vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
      expeditions: [mockExpedition],
      timelineData: mockTimelineData,
      loading: false,
      error: null,
      refreshing: false,
      createExpedition: vi.fn(),
      updateExpedition: vi.fn(),
      deleteExpedition: vi.fn(),
      refreshExpeditions: mockRefreshExpeditions,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial Render', () => {
    it('should render dashboard with stats', async () => {
      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(/active expeditions/i)).toBeInTheDocument();
      });

      // Stats should be visible
      expect(screen.getByText('5')).toBeInTheDocument(); // active count
      expect(screen.getByText('10')).toBeInTheDocument(); // completed count
    });

    it('should render timeline of expeditions', async () => {
      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });
    });

    it('should show loading state initially', async () => {
      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [],
        timelineData: null,
        loading: true,
        error: null,
        refreshing: false,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: vi.fn(),
      });

      renderWithProviders(<DashboardContainer />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('should show error state when expeditions fail to load', async () => {
      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [],
        timelineData: null,
        loading: false,
        error: 'Failed to load expeditions',
        refreshing: false,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: vi.fn(),
      });

      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Calculation', () => {
    it('should calculate stats from timeline data', async () => {
      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        // Active expeditions
        expect(screen.getByText('5')).toBeInTheDocument();
        // Completed expeditions
        expect(screen.getByText('10')).toBeInTheDocument();
        // Overdue expeditions
        expect(screen.getByText('2')).toBeInTheDocument();
      });
    });

    it('should show fallback stats when timeline data is null', async () => {
      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [mockExpedition],
        timelineData: null,
        loading: false,
        error: null,
        refreshing: false,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: mockRefreshExpeditions,
      });

      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        // Should show expedition count as fallback
        expect(screen.getByText('1')).toBeInTheDocument();
      });
    });

    it('should calculate completion rate correctly', async () => {
      const customTimelineData = {
        active: 3,
        completed: 7,
        overdue: 0,
        total: 10,
      };

      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [],
        timelineData: customTimelineData,
        loading: false,
        error: null,
        refreshing: false,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: mockRefreshExpeditions,
      });

      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        // 70% completion rate (7/10)
        expect(screen.getByText(/70%/i)).toBeInTheDocument();
      });
    });
  });

  describe('Timeline Display', () => {
    it('should display expeditions in timeline', async () => {
      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
        expect(screen.getByText(mockExpedition.description)).toBeInTheDocument();
      });
    });

    it('should show empty state when no expeditions', async () => {
      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [],
        timelineData: { active: 0, completed: 0, overdue: 0, total: 0 },
        loading: false,
        error: null,
        refreshing: false,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: mockRefreshExpeditions,
      });

      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(/no expeditions/i)).toBeInTheDocument();
      });
    });

    it('should display overdue badge for overdue expeditions', async () => {
      const overdueExpedition = {
        ...mockExpedition,
        deadline: '2020-01-01', // Past date
      };

      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [overdueExpedition],
        timelineData: mockTimelineData,
        loading: false,
        error: null,
        refreshing: false,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: mockRefreshExpeditions,
      });

      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(/overdue/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Actions', () => {
    it('should navigate to create expedition when clicking new button', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(/active expeditions/i)).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /new expedition/i });
      await user.click(createButton);

      expect(mockNavigate).toHaveBeenCalledWith('/expedition/new');
    });

    it('should navigate to expedition details when clicking expedition', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      const expeditionCard = screen.getByText(mockExpedition.name);
      await user.click(expeditionCard);

      expect(mockNavigate).toHaveBeenCalledWith(`/expedition/${mockExpedition.id}`);
    });

    it('should refresh expeditions when clicking refresh button', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(/active expeditions/i)).toBeInTheDocument();
      });

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      expect(mockRefreshExpeditions).toHaveBeenCalledTimes(1);
    });

    it('should show refreshing indicator during manual refresh', async () => {
      const user = userEvent.setup();

      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [mockExpedition],
        timelineData: mockTimelineData,
        loading: false,
        error: null,
        refreshing: true,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: mockRefreshExpeditions,
      });

      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(/refreshing/i)).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Updates', () => {
    it('should enable real-time updates by default', async () => {
      const spy = vi.spyOn(useExpeditionsModule, 'useExpeditions');

      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(spy).toHaveBeenCalledWith({
          autoRefresh: true,
          refreshInterval: 30000,
          realTimeUpdates: true,
        });
      });
    });

    it('should reflect updated expedition data from real-time updates', async () => {
      const { rerender } = renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Simulate real-time update with new data
      const updatedExpedition = {
        ...mockExpedition,
        name: 'Updated Expedition Name',
      };

      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [updatedExpedition],
        timelineData: mockTimelineData,
        loading: false,
        error: null,
        refreshing: false,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: mockRefreshExpeditions,
      });

      rerender(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText('Updated Expedition Name')).toBeInTheDocument();
      });
    });
  });

  describe('Auto-refresh', () => {
    it('should configure auto-refresh with 30 second interval', async () => {
      const spy = vi.spyOn(useExpeditionsModule, 'useExpeditions');

      renderWithProviders(<DashboardContainer />);

      expect(spy).toHaveBeenCalledWith(
        expect.objectContaining({
          autoRefresh: true,
          refreshInterval: 30000,
        })
      );
    });
  });

  describe('Error Recovery', () => {
    it('should allow retry when error occurs', async () => {
      const user = userEvent.setup();

      vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
        expeditions: [],
        timelineData: null,
        loading: false,
        error: 'Network error',
        refreshing: false,
        createExpedition: vi.fn(),
        updateExpedition: vi.fn(),
        deleteExpedition: vi.fn(),
        refreshExpeditions: mockRefreshExpeditions,
      });

      renderWithProviders(<DashboardContainer />);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(mockRefreshExpeditions).toHaveBeenCalled();
    });
  });
});
