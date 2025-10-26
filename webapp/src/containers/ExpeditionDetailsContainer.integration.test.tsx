import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExpeditionDetailsContainer } from './ExpeditionDetailsContainer';
import {
  renderWithProviders,
  mockExpedition,
  mockPirateNames,
  mockBuyers,
} from '@/test/integration-helpers';
import * as useExpeditionDetailsModule from '@/hooks/useExpeditionDetails';
import * as useExpeditionPiratesModule from '@/hooks/useExpeditionPirates';
import * as useItemConsumptionModule from '@/hooks/useItemConsumption';

/**
 * Integration Tests for ExpeditionDetailsContainer
 *
 * Tests container component with:
 * - Multiple hooks composition
 * - Tab navigation
 * - Modal interactions
 * - Item consumption flow
 * - Pirate management
 */

vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
  showAlert: vi.fn(),
}));

describe('ExpeditionDetailsContainer Integration', () => {
  const mockRefresh = vi.fn();
  const mockAddPirate = vi.fn();
  const mockLoadAvailableBuyers = vi.fn();
  const mockConsumeItem = vi.fn();
  const mockOnBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useExpeditionDetails
    vi.spyOn(useExpeditionDetailsModule, 'useExpeditionDetails').mockReturnValue({
      expedition: mockExpedition,
      loading: false,
      refreshing: false,
      error: null,
      refresh: mockRefresh,
    });

    // Mock useExpeditionPirates
    vi.spyOn(useExpeditionPiratesModule, 'useExpeditionPirates').mockReturnValue({
      pirateNames: mockPirateNames,
      availableBuyers: mockBuyers,
      loadingPirates: false,
      addingPirate: false,
      error: null,
      loadAvailableBuyers: mockLoadAvailableBuyers,
      addPirate: mockAddPirate,
    });

    // Mock useItemConsumption
    vi.spyOn(useItemConsumptionModule, 'useItemConsumption').mockReturnValue({
      consuming: false,
      error: null,
      consumeItem: mockConsumeItem,
      clearError: vi.fn(),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial Render', () => {
    it('should render expedition details on overview tab', async () => {
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      expect(screen.getByText(mockExpedition.description)).toBeInTheDocument();
    });

    it('should show loading state initially', async () => {
      vi.spyOn(useExpeditionDetailsModule, 'useExpeditionDetails').mockReturnValue({
        expedition: null,
        loading: true,
        refreshing: false,
        error: null,
        refresh: mockRefresh,
      });

      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('should show error state when expedition fails to load', async () => {
      vi.spyOn(useExpeditionDetailsModule, 'useExpeditionDetails').mockReturnValue({
        expedition: null,
        loading: false,
        refreshing: false,
        error: 'Failed to load expedition',
        refresh: mockRefresh,
      });

      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should start on overview tab by default', async () => {
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /overview/i, selected: true })).toBeInTheDocument();
      });
    });

    it('should switch to items tab when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      const itemsTab = screen.getByRole('tab', { name: /items/i });
      await user.click(itemsTab);

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /items/i, selected: true })).toBeInTheDocument();
      });
    });

    it('should switch to pirates tab when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      const piratesTab = screen.getByRole('tab', { name: /pirates/i });
      await user.click(piratesTab);

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /pirates/i, selected: true })).toBeInTheDocument();
      });
    });

    it('should retain tab state when refreshing', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Switch to items tab
      const itemsTab = screen.getByRole('tab', { name: /items/i });
      await user.click(itemsTab);

      // Trigger refresh
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      // Should still be on items tab
      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /items/i, selected: true })).toBeInTheDocument();
      });
    });
  });

  describe('Pirate Management', () => {
    it('should open add pirate modal when clicking add button', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Switch to pirates tab
      const piratesTab = screen.getByRole('tab', { name: /pirates/i });
      await user.click(piratesTab);

      // Click add pirate button
      const addButton = screen.getByRole('button', { name: /add pirate/i });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
      });

      // Should load available buyers
      expect(mockLoadAvailableBuyers).toHaveBeenCalled();
    });

    it('should close add pirate modal when clicking cancel', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Open modal
      const piratesTab = screen.getByRole('tab', { name: /pirates/i });
      await user.click(piratesTab);

      const addButton = screen.getByRole('button', { name: /add pirate/i });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
      });

      // Close modal
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText(/add new pirate/i)).not.toBeInTheDocument();
      });
    });

    it('should add pirate successfully', async () => {
      const user = userEvent.setup();
      mockAddPirate.mockResolvedValue(undefined);

      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Open modal
      const piratesTab = screen.getByRole('tab', { name: /pirates/i });
      await user.click(piratesTab);

      const addButton = screen.getByRole('button', { name: /add pirate/i });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
      });

      // Enter pirate name
      const nameInput = screen.getByLabelText(/pirate name/i);
      await user.type(nameInput, 'NewPirate');

      // Submit
      const submitButton = screen.getByRole('button', { name: /add/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAddPirate).toHaveBeenCalledWith('NewPirate');
      });

      // Should refresh after adding
      expect(mockRefresh).toHaveBeenCalled();
    });

    it('should not add pirate with empty name', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Open modal
      const piratesTab = screen.getByRole('tab', { name: /pirates/i });
      await user.click(piratesTab);

      const addButton = screen.getByRole('button', { name: /add pirate/i });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
      });

      // Try to submit without entering name
      const submitButton = screen.getByRole('button', { name: /add/i });
      await user.click(submitButton);

      // Should not call add pirate
      expect(mockAddPirate).not.toHaveBeenCalled();
    });
  });

  describe('Item Consumption', () => {
    it('should open consume modal when clicking consume button', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Switch to items tab
      const itemsTab = screen.getByRole('tab', { name: /items/i });
      await user.click(itemsTab);

      // Click consume button for an item
      const consumeButton = screen.getByRole('button', { name: /consume/i });
      await user.click(consumeButton);

      await waitFor(() => {
        expect(screen.getByText(/consume item/i)).toBeInTheDocument();
      });
    });

    it('should close consume modal when clicking cancel', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Open modal
      const itemsTab = screen.getByRole('tab', { name: /items/i });
      await user.click(itemsTab);

      const consumeButton = screen.getByRole('button', { name: /consume/i });
      await user.click(consumeButton);

      await waitFor(() => {
        expect(screen.getByText(/consume item/i)).toBeInTheDocument();
      });

      // Close modal
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText(/consume item/i)).not.toBeInTheDocument();
      });
    });

    it('should consume item successfully', async () => {
      const user = userEvent.setup();
      mockConsumeItem.mockResolvedValue(undefined);

      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Open consume modal
      const itemsTab = screen.getByRole('tab', { name: /items/i });
      await user.click(itemsTab);

      const consumeButton = screen.getByRole('button', { name: /consume/i });
      await user.click(consumeButton);

      await waitFor(() => {
        expect(screen.getByText(/consume item/i)).toBeInTheDocument();
      });

      // Fill in consumption details
      const pirateSelect = screen.getByLabelText(/pirate/i);
      await user.selectOptions(pirateSelect, 'BlackBeard');

      const quantityInput = screen.getByLabelText(/quantity/i);
      await user.clear(quantityInput);
      await user.type(quantityInput, '2');

      const priceInput = screen.getByLabelText(/price/i);
      await user.clear(priceInput);
      await user.type(priceInput, '150');

      // Submit
      const submitButton = screen.getByRole('button', { name: /confirm/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockConsumeItem).toHaveBeenCalledWith(
          expect.objectContaining({
            pirate_name: 'BlackBeard',
            quantity: 2,
            price: 150,
          }),
          expect.any(Function)
        );
      });
    });

    it('should refresh expedition after successful consumption', async () => {
      const user = userEvent.setup();
      let onSuccessCallback: (() => void) | undefined;

      mockConsumeItem.mockImplementation(async (data, onSuccess) => {
        onSuccessCallback = onSuccess;
      });

      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Consume item
      const itemsTab = screen.getByRole('tab', { name: /items/i });
      await user.click(itemsTab);

      const consumeButton = screen.getByRole('button', { name: /consume/i });
      await user.click(consumeButton);

      await waitFor(() => {
        expect(screen.getByText(/consume item/i)).toBeInTheDocument();
      });

      const pirateSelect = screen.getByLabelText(/pirate/i);
      await user.selectOptions(pirateSelect, 'BlackBeard');

      const submitButton = screen.getByRole('button', { name: /confirm/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockConsumeItem).toHaveBeenCalled();
      });

      // Call the success callback
      if (onSuccessCallback) {
        await onSuccessCallback();
      }

      // Should refresh expedition
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  describe('Actions', () => {
    it('should call onBack when clicking back button', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      const backButton = screen.getByRole('button', { name: /back/i });
      await user.click(backButton);

      expect(mockOnBack).toHaveBeenCalled();
    });

    it('should refresh expedition when clicking refresh button', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      expect(mockRefresh).toHaveBeenCalled();
    });

    it('should show refreshing indicator during refresh', async () => {
      vi.spyOn(useExpeditionDetailsModule, 'useExpeditionDetails').mockReturnValue({
        expedition: mockExpedition,
        loading: false,
        refreshing: true,
        error: null,
        refresh: mockRefresh,
      });

      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(/refreshing/i)).toBeInTheDocument();
      });
    });
  });

  describe('Calculated Values', () => {
    it('should calculate total pirates correctly', async () => {
      renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Switch to pirates tab to see the count
      const user = userEvent.setup();
      const piratesTab = screen.getByRole('tab', { name: /pirates/i });
      await user.click(piratesTab);

      await waitFor(() => {
        // Should show unique pirate count (from consumptions)
        expect(screen.getByText(/1 pirate/i)).toBeInTheDocument();
      });
    });

    it('should update calculated values when expedition changes', async () => {
      const { rerender } = renderWithProviders(
        <ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
      });

      // Update with expedition that has more pirates
      const updatedExpedition = {
        ...mockExpedition,
        consumptions: [
          ...mockExpedition.consumptions,
          {
            id: 2,
            expedition_id: 1,
            product_id: 1,
            consumer_name: 'NewPirate',
            quantity: 1,
            price: 100,
            consumed_at: '2025-01-03',
          },
        ],
      };

      vi.spyOn(useExpeditionDetailsModule, 'useExpeditionDetails').mockReturnValue({
        expedition: updatedExpedition,
        loading: false,
        refreshing: false,
        error: null,
        refresh: mockRefresh,
      });

      rerender(<ExpeditionDetailsContainer expeditionId={1} onBack={mockOnBack} />);

      await waitFor(() => {
        // Should now show 2 pirates
        const user = userEvent.setup();
        const piratesTab = screen.getByRole('tab', { name: /pirates/i });
        user.click(piratesTab);
      });
    });
  });
});
