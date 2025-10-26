import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExpeditionDetailsContainer } from '@/containers/ExpeditionDetailsContainer';
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
 * Complete Flow Test: Consume Item
 *
 * Tests the entire user journey for consuming an expedition item.
 *
 * Flow steps:
 * 1. Open expedition details
 * 2. Navigate to items tab
 * 3. Click consume button for an item
 * 4. Select pirate from dropdown
 * 5. Enter quantity and price
 * 6. Confirm consumption
 * 7. See updated expedition data
 */

vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
  showAlert: vi.fn(),
}));

describe('Complete Flow: Consume Item', () => {
  const mockRefresh = vi.fn();
  const mockConsumeItem = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    vi.spyOn(useExpeditionDetailsModule, 'useExpeditionDetails').mockReturnValue({
      expedition: mockExpedition,
      loading: false,
      refreshing: false,
      error: null,
      refresh: mockRefresh,
    });

    vi.spyOn(useExpeditionPiratesModule, 'useExpeditionPirates').mockReturnValue({
      pirateNames: mockPirateNames,
      availableBuyers: mockBuyers,
      loadingPirates: false,
      addingPirate: false,
      error: null,
      loadAvailableBuyers: vi.fn(),
      addPirate: vi.fn(),
    });

    vi.spyOn(useItemConsumptionModule, 'useItemConsumption').mockReturnValue({
      consuming: false,
      error: null,
      consumeItem: mockConsumeItem,
      clearError: vi.fn(),
    });
  });

  it('should complete entire item consumption flow successfully', async () => {
    const user = userEvent.setup();
    let onSuccessCallback: (() => Promise<void>) | undefined;

    // Mock consumeItem to capture the success callback
    mockConsumeItem.mockImplementation(async (data, onSuccess) => {
      onSuccessCallback = onSuccess;
      return Promise.resolve();
    });

    // Render expedition details
    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    // STEP 1: Wait for expedition to load
    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // STEP 2: Navigate to items tab
    const itemsTab = screen.getByRole('tab', { name: /items/i });
    await user.click(itemsTab);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /items/i, selected: true })).toBeInTheDocument();
    });

    // Verify item is displayed
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText(/10 units/i)).toBeInTheDocument(); // Total quantity
    expect(screen.getByText(/3 consumed/i)).toBeInTheDocument(); // Already consumed

    // STEP 3: Click consume button
    const consumeButton = screen.getByRole('button', { name: /consume/i });
    expect(consumeButton).toBeEnabled();
    await user.click(consumeButton);

    // STEP 4: Consume modal should open
    await waitFor(() => {
      expect(screen.getByText(/consume item/i)).toBeInTheDocument();
    });

    // Verify modal shows item details
    expect(screen.getByText(/test product/i)).toBeInTheDocument();
    expect(screen.getByText(/available: 7/i)).toBeInTheDocument(); // 10 - 3 consumed

    // STEP 5: Select pirate from dropdown
    const pirateSelect = screen.getByLabelText(/pirate/i);
    expect(pirateSelect).toBeInTheDocument();

    // Should have available pirates
    expect(screen.getByRole('option', { name: /blackbeard/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /redrum/i })).toBeInTheDocument();

    await user.selectOptions(pirateSelect, 'BlackBeard');
    expect(pirateSelect).toHaveValue('BlackBeard');

    // STEP 6: Enter quantity
    const quantityInput = screen.getByLabelText(/quantity/i) as HTMLInputElement;
    expect(quantityInput).toHaveValue(1); // Default value
    await user.clear(quantityInput);
    await user.type(quantityInput, '5');
    expect(quantityInput.value).toBe('5');

    // Enter price
    const priceInput = screen.getByLabelText(/price/i) as HTMLInputElement;
    await user.clear(priceInput);
    await user.type(priceInput, '150');
    expect(priceInput.value).toBe('150');

    // STEP 7: Confirm consumption
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    expect(confirmButton).toBeEnabled();
    await user.click(confirmButton);

    // Verify API was called with correct data
    await waitFor(() => {
      expect(mockConsumeItem).toHaveBeenCalledWith(
        {
          product_id: 1,
          pirate_name: 'BlackBeard',
          quantity: 5,
          price: 150,
        },
        expect.any(Function)
      );
    });

    // Trigger the success callback
    if (onSuccessCallback) {
      await onSuccessCallback();
    }

    // STEP 8: Verify expedition is refreshed after consumption
    await waitFor(() => {
      expect(mockRefresh).toHaveBeenCalled();
    });

    // Modal should be closed
    await waitFor(() => {
      expect(screen.queryByText(/consume item/i)).not.toBeInTheDocument();
    });
  });

  it('should validate consumption quantity', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // Navigate to items tab
    const itemsTab = screen.getByRole('tab', { name: /items/i });
    await user.click(itemsTab);

    // Open consume modal
    const consumeButton = screen.getByRole('button', { name: /consume/i });
    await user.click(consumeButton);

    await waitFor(() => {
      expect(screen.getByText(/consume item/i)).toBeInTheDocument();
    });

    const pirateSelect = screen.getByLabelText(/pirate/i);
    await user.selectOptions(pirateSelect, 'BlackBeard');

    // Try to consume more than available
    const quantityInput = screen.getByLabelText(/quantity/i);
    await user.clear(quantityInput);
    await user.type(quantityInput, '100'); // More than 7 available

    const confirmButton = screen.getByRole('button', { name: /confirm/i });

    // Should show validation error or disable button
    expect(confirmButton).toBeDisabled();
  });

  it('should require pirate selection', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // Navigate to items tab
    const itemsTab = screen.getByRole('tab', { name: /items/i });
    await user.click(itemsTab);

    // Open consume modal
    const consumeButton = screen.getByRole('button', { name: /consume/i });
    await user.click(consumeButton);

    await waitFor(() => {
      expect(screen.getByText(/consume item/i)).toBeInTheDocument();
    });

    // Enter quantity without selecting pirate
    const quantityInput = screen.getByLabelText(/quantity/i);
    await user.clear(quantityInput);
    await user.type(quantityInput, '2');

    const confirmButton = screen.getByRole('button', { name: /confirm/i });

    // Should be disabled without pirate selection
    expect(confirmButton).toBeDisabled();
  });

  it('should handle consumption error gracefully', async () => {
    const user = userEvent.setup();

    mockConsumeItem.mockRejectedValue(new Error('Consumption failed'));

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // Navigate to items and open consume modal
    const itemsTab = screen.getByRole('tab', { name: /items/i });
    await user.click(itemsTab);

    const consumeButton = screen.getByRole('button', { name: /consume/i });
    await user.click(consumeButton);

    await waitFor(() => {
      expect(screen.getByText(/consume item/i)).toBeInTheDocument();
    });

    // Fill form
    const pirateSelect = screen.getByLabelText(/pirate/i);
    await user.selectOptions(pirateSelect, 'BlackBeard');

    const quantityInput = screen.getByLabelText(/quantity/i);
    await user.clear(quantityInput);
    await user.type(quantityInput, '2');

    // Confirm
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    await user.click(confirmButton);

    // Should call API
    await waitFor(() => {
      expect(mockConsumeItem).toHaveBeenCalled();
    });

    // Should not close modal on error
    await waitFor(() => {
      expect(screen.getByText(/consume item/i)).toBeInTheDocument();
    });

    // Should not refresh on error
    expect(mockRefresh).not.toHaveBeenCalled();
  });

  it('should allow canceling consumption', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // Navigate to items tab
    const itemsTab = screen.getByRole('tab', { name: /items/i });
    await user.click(itemsTab);

    // Open consume modal
    const consumeButton = screen.getByRole('button', { name: /consume/i });
    await user.click(consumeButton);

    await waitFor(() => {
      expect(screen.getByText(/consume item/i)).toBeInTheDocument();
    });

    // Fill some data
    const pirateSelect = screen.getByLabelText(/pirate/i);
    await user.selectOptions(pirateSelect, 'BlackBeard');

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    // Modal should close
    await waitFor(() => {
      expect(screen.queryByText(/consume item/i)).not.toBeInTheDocument();
    });

    // Should not consume item
    expect(mockConsumeItem).not.toHaveBeenCalled();
  });

  it('should show loading state during consumption', async () => {
    const user = userEvent.setup();

    // Mock consuming state
    vi.spyOn(useItemConsumptionModule, 'useItemConsumption').mockReturnValue({
      consuming: true,
      error: null,
      consumeItem: mockConsumeItem,
      clearError: vi.fn(),
    });

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    const itemsTab = screen.getByRole('tab', { name: /items/i });
    await user.click(itemsTab);

    const consumeButton = screen.getByRole('button', { name: /consume/i });
    await user.click(consumeButton);

    await waitFor(() => {
      expect(screen.getByText(/consume item/i)).toBeInTheDocument();
    });

    // Confirm button should show loading state
    const confirmButton = screen.getByRole('button', { name: /consuming/i });
    expect(confirmButton).toBeDisabled();
  });

  it('should consume item with default price from item', async () => {
    const user = userEvent.setup();
    let capturedData: any;

    mockConsumeItem.mockImplementation(async (data, onSuccess) => {
      capturedData = data;
      await onSuccess();
    });

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    const itemsTab = screen.getByRole('tab', { name: /items/i });
    await user.click(itemsTab);

    const consumeButton = screen.getByRole('button', { name: /consume/i });
    await user.click(consumeButton);

    await waitFor(() => {
      expect(screen.getByText(/consume item/i)).toBeInTheDocument();
    });

    // Select pirate and quantity, but don't change price
    const pirateSelect = screen.getByLabelText(/pirate/i);
    await user.selectOptions(pirateSelect, 'BlackBeard');

    const quantityInput = screen.getByLabelText(/quantity/i);
    await user.clear(quantityInput);
    await user.type(quantityInput, '3');

    // Price should be pre-filled with unit_price from item (100)
    const priceInput = screen.getByLabelText(/price/i) as HTMLInputElement;
    expect(priceInput.value).toBe('100');

    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(mockConsumeItem).toHaveBeenCalled();
    });

    // Should use default price
    expect(capturedData.price).toBe(100);
  });
});
