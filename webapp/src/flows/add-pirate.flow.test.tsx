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
 * Complete Flow Test: Add Pirate
 *
 * Tests the entire user journey for adding a pirate to an expedition.
 *
 * Flow steps:
 * 1. Open expedition details
 * 2. Navigate to pirates tab
 * 3. Click add pirate button
 * 4. View available buyers
 * 5. Select or enter pirate name
 * 6. Confirm addition
 * 7. See updated pirate list
 */

vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
  showAlert: vi.fn(),
}));

describe('Complete Flow: Add Pirate', () => {
  const mockRefresh = vi.fn();
  const mockLoadAvailableBuyers = vi.fn();
  const mockAddPirate = vi.fn();

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
      loadAvailableBuyers: mockLoadAvailableBuyers,
      addPirate: mockAddPirate,
    });

    vi.spyOn(useItemConsumptionModule, 'useItemConsumption').mockReturnValue({
      consuming: false,
      error: null,
      consumeItem: vi.fn(),
      clearError: vi.fn(),
    });
  });

  it('should complete entire add pirate flow successfully', async () => {
    const user = userEvent.setup();

    mockAddPirate.mockResolvedValue(undefined);

    // Render expedition details
    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    // STEP 1: Wait for expedition to load
    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // STEP 2: Navigate to pirates tab
    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /pirates/i, selected: true })).toBeInTheDocument();
    });

    // Verify existing pirates are displayed
    expect(screen.getByText('BlackBeard')).toBeInTheDocument();
    expect(screen.getByText('RedRum')).toBeInTheDocument();

    // STEP 3: Click add pirate button
    const addButton = screen.getByRole('button', { name: /add pirate/i });
    expect(addButton).toBeEnabled();
    await user.click(addButton);

    // STEP 4: Add pirate modal should open
    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Should load available buyers
    expect(mockLoadAvailableBuyers).toHaveBeenCalledTimes(1);

    // STEP 5: View available buyers in dropdown
    const pirateSelect = screen.getByLabelText(/pirate name/i);
    expect(pirateSelect).toBeInTheDocument();

    // Should show available buyers
    expect(screen.getByRole('option', { name: /buyer1/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /buyer2/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /buyer3/i })).toBeInTheDocument();

    // Select a buyer
    await user.selectOptions(pirateSelect, 'buyer1');
    expect(pirateSelect).toHaveValue('buyer1');

    // STEP 6: Confirm addition
    const addConfirmButton = screen.getByRole('button', { name: /add/i });
    expect(addConfirmButton).toBeEnabled();
    await user.click(addConfirmButton);

    // Verify API was called
    await waitFor(() => {
      expect(mockAddPirate).toHaveBeenCalledWith('buyer1');
    });

    // STEP 7: Expedition should be refreshed to show new pirate
    await waitFor(() => {
      expect(mockRefresh).toHaveBeenCalled();
    });

    // Modal should close
    await waitFor(() => {
      expect(screen.queryByText(/add new pirate/i)).not.toBeInTheDocument();
    });
  });

  it('should allow entering custom pirate name', async () => {
    const user = userEvent.setup();

    mockAddPirate.mockResolvedValue(undefined);

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // Navigate to pirates tab
    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    // Open add pirate modal
    const addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Enter custom name instead of selecting from dropdown
    const nameInput = screen.getByLabelText(/pirate name/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'CustomPirateName');

    expect(nameInput).toHaveValue('CustomPirateName');

    // Confirm
    const addConfirmButton = screen.getByRole('button', { name: /add/i });
    await user.click(addConfirmButton);

    await waitFor(() => {
      expect(mockAddPirate).toHaveBeenCalledWith('CustomPirateName');
    });
  });

  it('should validate pirate name is required', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // Navigate to pirates tab
    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    // Open add pirate modal
    const addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Try to add without entering name
    const addConfirmButton = screen.getByRole('button', { name: /add/i });

    // Should be disabled or validation error shown
    expect(addConfirmButton).toBeDisabled();
  });

  it('should handle add pirate error gracefully', async () => {
    const user = userEvent.setup();

    mockAddPirate.mockRejectedValue(new Error('Failed to add pirate'));

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // Navigate to pirates tab
    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    // Open add pirate modal
    const addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Select pirate
    const pirateSelect = screen.getByLabelText(/pirate name/i);
    await user.selectOptions(pirateSelect, 'buyer1');

    // Confirm
    const addConfirmButton = screen.getByRole('button', { name: /add/i });
    await user.click(addConfirmButton);

    // Should call API
    await waitFor(() => {
      expect(mockAddPirate).toHaveBeenCalled();
    });

    // Should not close modal on error
    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Should not refresh on error
    expect(mockRefresh).not.toHaveBeenCalled();
  });

  it('should allow canceling add pirate', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    // Navigate to pirates tab
    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    // Open add pirate modal
    const addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Select a pirate
    const pirateSelect = screen.getByLabelText(/pirate name/i);
    await user.selectOptions(pirateSelect, 'buyer1');

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    // Modal should close
    await waitFor(() => {
      expect(screen.queryByText(/add new pirate/i)).not.toBeInTheDocument();
    });

    // Should not add pirate
    expect(mockAddPirate).not.toHaveBeenCalled();
  });

  it('should show loading state while adding pirate', async () => {
    const user = userEvent.setup();

    // Mock adding state
    vi.spyOn(useExpeditionPiratesModule, 'useExpeditionPirates').mockReturnValue({
      pirateNames: mockPirateNames,
      availableBuyers: mockBuyers,
      loadingPirates: false,
      addingPirate: true,
      error: null,
      loadAvailableBuyers: mockLoadAvailableBuyers,
      addPirate: mockAddPirate,
    });

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    const addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Add button should show loading state
    const addConfirmButton = screen.getByRole('button', { name: /adding/i });
    expect(addConfirmButton).toBeDisabled();
  });

  it('should show loading state while fetching buyers', async () => {
    const user = userEvent.setup();

    // Mock loading state
    vi.spyOn(useExpeditionPiratesModule, 'useExpeditionPirates').mockReturnValue({
      pirateNames: mockPirateNames,
      availableBuyers: [],
      loadingPirates: true,
      addingPirate: false,
      error: null,
      loadAvailableBuyers: mockLoadAvailableBuyers,
      addPirate: mockAddPirate,
    });

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    const addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Should show loading indicator
    expect(screen.getByText(/loading buyers/i)).toBeInTheDocument();
  });

  it('should prevent duplicate pirate names', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    const addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Try to add a pirate that already exists
    const nameInput = screen.getByLabelText(/pirate name/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'BlackBeard'); // Already exists

    const addConfirmButton = screen.getByRole('button', { name: /add/i });

    // Should show validation error or disable button
    expect(screen.getByText(/already exists/i)).toBeInTheDocument();
    expect(addConfirmButton).toBeDisabled();
  });

  it('should clear modal state when reopening', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ExpeditionDetailsContainer expeditionId={1} />);

    await waitFor(() => {
      expect(screen.getByText(mockExpedition.name)).toBeInTheDocument();
    });

    const piratesTab = screen.getByRole('tab', { name: /pirates/i });
    await user.click(piratesTab);

    // Open modal and enter data
    let addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/pirate name/i);
    await user.type(nameInput, 'TestPirate');

    // Cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByText(/add new pirate/i)).not.toBeInTheDocument();
    });

    // Open modal again
    addButton = screen.getByRole('button', { name: /add pirate/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/add new pirate/i)).toBeInTheDocument();
    });

    // Input should be cleared
    const nameInputAgain = screen.getByLabelText(/pirate name/i) as HTMLInputElement;
    expect(nameInputAgain.value).toBe('');
  });
});
