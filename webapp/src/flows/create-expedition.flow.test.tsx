import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateExpeditionContainer } from '@/containers/CreateExpeditionContainer';
import {
  renderWithProviders,
  mockNavigate,
  mockProducts,
} from '@/test/integration-helpers';
import { productService } from '@/services/api/productService';
import { expeditionItemsService } from '@/services/api/expeditionItemsService';
import * as useExpeditionsModule from '@/hooks/useExpeditions';

/**
 * Complete Flow Test: Create Expedition
 *
 * Tests the entire user journey from opening the wizard to successfully
 * creating an expedition with items.
 *
 * Flow steps:
 * 1. Open create expedition wizard
 * 2. Fill in expedition details (name, description, deadline)
 * 3. Select products from available list
 * 4. Configure product quantities, quality, and prices
 * 5. Review expedition summary
 * 6. Submit and navigate to expedition details
 */

vi.mock('@/services/api/productService');
vi.mock('@/services/api/expeditionItemsService');
vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
  showAlert: vi.fn(),
}));

describe('Complete Flow: Create Expedition', () => {
  const mockCreateExpedition = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();

    vi.spyOn(useExpeditionsModule, 'useExpeditions').mockReturnValue({
      expeditions: [],
      timelineData: null,
      loading: false,
      error: null,
      refreshing: false,
      createExpedition: mockCreateExpedition,
      updateExpedition: vi.fn(),
      deleteExpedition: vi.fn(),
      refreshExpeditions: vi.fn(),
    });

    vi.mocked(productService.getAll).mockResolvedValue(mockProducts);
  });

  it('should complete entire expedition creation flow successfully', async () => {
    const user = userEvent.setup();

    // Setup mocks
    const mockExpedition = {
      id: 42,
      name: 'Caribbean Treasure Hunt',
      description: 'Find the lost gold of Port Royal',
      status: 'active' as const,
      deadline: '2025-12-31',
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
      items: [],
      consumptions: [],
    };

    mockCreateExpedition.mockResolvedValue(mockExpedition);
    vi.mocked(expeditionItemsService.addItems).mockResolvedValue(undefined);

    // Render wizard
    renderWithProviders(<CreateExpeditionContainer />);

    // STEP 1: Fill expedition details
    await waitFor(() => {
      expect(screen.getByText(/expedition details/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/expedition name/i);
    await user.type(nameInput, 'Caribbean Treasure Hunt');

    const descInput = screen.getByLabelText(/description/i);
    await user.type(descInput, 'Find the lost gold of Port Royal');

    const deadlineInput = screen.getByLabelText(/deadline/i);
    await user.type(deadlineInput, '2025-12-31');

    // Verify step 1 data is entered
    expect(nameInput).toHaveValue('Caribbean Treasure Hunt');
    expect(descInput).toHaveValue('Find the lost gold of Port Royal');
    expect(deadlineInput).toHaveValue('2025-12-31');

    // Navigate to step 2
    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeEnabled();
    await user.click(nextButton);

    // STEP 2: Select products
    await waitFor(() => {
      expect(screen.getByText(/select products/i)).toBeInTheDocument();
    });

    // Select Product 1
    const product1Checkbox = screen.getByRole('checkbox', { name: /product 1/i });
    await user.click(product1Checkbox);
    expect(product1Checkbox).toBeChecked();

    // Select Product 2
    const product2Checkbox = screen.getByRole('checkbox', { name: /product 2/i });
    await user.click(product2Checkbox);
    expect(product2Checkbox).toBeChecked();

    // Navigate to step 3
    const nextButton2 = screen.getByRole('button', { name: /next/i });
    expect(nextButton2).toBeEnabled();
    await user.click(nextButton2);

    // STEP 3: Configure products
    await waitFor(() => {
      expect(screen.getByText(/configure products/i)).toBeInTheDocument();
    });

    // Configure Product 1
    const product1QuantityInput = screen.getAllByLabelText(/quantity/i)[0];
    await user.clear(product1QuantityInput);
    await user.type(product1QuantityInput, '10');

    const product1QualitySelect = screen.getAllByLabelText(/quality/i)[0];
    await user.selectOptions(product1QualitySelect, 'A');

    const product1PriceInput = screen.getAllByLabelText(/price/i)[0];
    await user.clear(product1PriceInput);
    await user.type(product1PriceInput, '120');

    // Configure Product 2
    const product2QuantityInput = screen.getAllByLabelText(/quantity/i)[1];
    await user.clear(product2QuantityInput);
    await user.type(product2QuantityInput, '5');

    const product2QualitySelect = screen.getAllByLabelText(/quality/i)[1];
    await user.selectOptions(product2QualitySelect, 'B');

    const product2PriceInput = screen.getAllByLabelText(/price/i)[1];
    await user.clear(product2PriceInput);
    await user.type(product2PriceInput, '180');

    // Navigate to step 4
    const nextButton3 = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton3);

    // STEP 4: Review and submit
    await waitFor(() => {
      expect(screen.getByText(/review/i)).toBeInTheDocument();
    });

    // Verify summary displays correct information
    expect(screen.getByText('Caribbean Treasure Hunt')).toBeInTheDocument();
    expect(screen.getByText('Find the lost gold of Port Royal')).toBeInTheDocument();
    expect(screen.getByText(/product 1/i)).toBeInTheDocument();
    expect(screen.getByText(/product 2/i)).toBeInTheDocument();

    // Submit the expedition
    const submitButton = screen.getByRole('button', { name: /create expedition/i });
    expect(submitButton).toBeEnabled();
    await user.click(submitButton);

    // Verify API calls
    await waitFor(() => {
      // Should create expedition
      expect(mockCreateExpedition).toHaveBeenCalledWith({
        name: 'Caribbean Treasure Hunt',
        description: 'Find the lost gold of Port Royal',
        deadline: '2025-12-31',
      });

      // Should add items to expedition
      expect(expeditionItemsService.addItems).toHaveBeenCalledWith(42, {
        items: [
          {
            product_id: 1,
            quantity: 10,
            quality_grade: 'A',
          },
          {
            product_id: 2,
            quantity: 5,
            quality_grade: 'B',
          },
        ],
      });
    });

    // Should navigate to expedition details
    expect(mockNavigate).toHaveBeenCalledWith('/expedition/42');
  });

  it('should handle back navigation while preserving data', async () => {
    const user = userEvent.setup();

    renderWithProviders(<CreateExpeditionContainer />);

    // Fill step 1
    await waitFor(() => {
      expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/expedition name/i);
    await user.type(nameInput, 'Test Expedition');

    // Go to step 2
    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/select products/i)).toBeInTheDocument();
    });

    // Select a product
    const productCheckbox = screen.getByRole('checkbox', { name: /product 1/i });
    await user.click(productCheckbox);

    // Go to step 3
    const nextButton2 = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton2);

    await waitFor(() => {
      expect(screen.getByText(/configure products/i)).toBeInTheDocument();
    });

    // Go back to step 2
    const previousButton = screen.getByRole('button', { name: /previous/i });
    await user.click(previousButton);

    await waitFor(() => {
      expect(screen.getByText(/select products/i)).toBeInTheDocument();
    });

    // Product should still be selected
    const productCheckboxAgain = screen.getByRole('checkbox', { name: /product 1/i });
    expect(productCheckboxAgain).toBeChecked();

    // Go back to step 1
    const previousButton2 = screen.getByRole('button', { name: /previous/i });
    await user.click(previousButton2);

    await waitFor(() => {
      expect(screen.getByText(/expedition details/i)).toBeInTheDocument();
    });

    // Name should still be filled
    const nameInputAgain = screen.getByLabelText(/expedition name/i) as HTMLInputElement;
    expect(nameInputAgain.value).toBe('Test Expedition');
  });

  it('should handle API error during creation gracefully', async () => {
    const user = userEvent.setup();

    mockCreateExpedition.mockRejectedValue(new Error('Server error'));

    renderWithProviders(<CreateExpeditionContainer />);

    // Quick fill all steps
    await waitFor(() => {
      expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/expedition name/i);
    await user.type(nameInput, 'Test Expedition');

    let nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/select products/i)).toBeInTheDocument();
    });

    const productCheckbox = screen.getByRole('checkbox', { name: /product 1/i });
    await user.click(productCheckbox);

    nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/configure products/i)).toBeInTheDocument();
    });

    nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/review/i)).toBeInTheDocument();
    });

    const submitButton = screen.getByRole('button', { name: /create expedition/i });
    await user.click(submitButton);

    // Should attempt creation
    await waitFor(() => {
      expect(mockCreateExpedition).toHaveBeenCalled();
    });

    // Should not navigate on error
    expect(mockNavigate).not.toHaveBeenCalled();

    // User should still be on review step
    expect(screen.getByText(/review/i)).toBeInTheDocument();
  });

  it('should validate each step before allowing navigation', async () => {
    const user = userEvent.setup();

    renderWithProviders(<CreateExpeditionContainer />);

    await waitFor(() => {
      expect(screen.getByText(/expedition details/i)).toBeInTheDocument();
    });

    // Step 1: Next button should be disabled without name
    let nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeDisabled();

    // Enter name
    const nameInput = screen.getByLabelText(/expedition name/i);
    await user.type(nameInput, 'Test Expedition');

    // Now next button should be enabled
    await waitFor(() => {
      expect(nextButton).toBeEnabled();
    });

    await user.click(nextButton);

    // Step 2: Next button should be disabled without products
    await waitFor(() => {
      expect(screen.getByText(/select products/i)).toBeInTheDocument();
    });

    nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeDisabled();

    // Select a product
    const productCheckbox = screen.getByRole('checkbox', { name: /product 1/i });
    await user.click(productCheckbox);

    // Now next button should be enabled
    await waitFor(() => {
      expect(nextButton).toBeEnabled();
    });
  });

  it('should allow creating expedition with minimal data', async () => {
    const user = userEvent.setup();

    const mockExpedition = {
      id: 99,
      name: 'Minimal Expedition',
      status: 'active' as const,
    };

    mockCreateExpedition.mockResolvedValue(mockExpedition);

    renderWithProviders(<CreateExpeditionContainer />);

    await waitFor(() => {
      expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
    });

    // Only fill name (description and deadline are optional)
    const nameInput = screen.getByLabelText(/expedition name/i);
    await user.type(nameInput, 'Minimal Expedition');

    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    // Skip to review without selecting products (if allowed by validation)
    // This tests the minimum viable expedition creation

    // Should create expedition with minimal data
    await waitFor(() => {
      expect(mockCreateExpedition).toHaveBeenCalledWith({
        name: 'Minimal Expedition',
        description: '',
        deadline: undefined,
      });
    });
  });
});
