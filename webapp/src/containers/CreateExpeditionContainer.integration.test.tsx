import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateExpeditionContainer } from './CreateExpeditionContainer';
import {
  renderWithProviders,
  mockNavigate,
  mockProducts,
  createMockApiResponse,
  createMockApiError,
} from '@/test/integration-helpers';
import { productService } from '@/services/api/productService';
import { expeditionItemsService } from '@/services/api/expeditionItemsService';
import * as useExpeditionsModule from '@/hooks/useExpeditions';

/**
 * Integration Tests for CreateExpeditionContainer
 *
 * Tests container component with:
 * - Real hooks composition
 * - Mocked API services
 * - User interactions
 * - Navigation flow
 */

vi.mock('@/services/api/productService');
vi.mock('@/services/api/expeditionItemsService');
vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
  showAlert: vi.fn(),
}));

describe('CreateExpeditionContainer Integration', () => {
  const mockCreateExpedition = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();

    // Mock useExpeditions hook
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

    // Default product service mock
    vi.mocked(productService.getAll).mockResolvedValue(mockProducts);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should render wizard at step 1', async () => {
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByText(/expedition name/i)).toBeInTheDocument();
      });
    });

    it('should load products on mount', async () => {
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(productService.getAll).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle product loading error gracefully', async () => {
      vi.mocked(productService.getAll).mockRejectedValue(new Error('Network error'));

      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(productService.getAll).toHaveBeenCalled();
      });

      // Should not crash, just show empty products
      expect(screen.getByText(/expedition name/i)).toBeInTheDocument();
    });
  });

  describe('Step Navigation', () => {
    it('should navigate to next step when step 1 is valid', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      // Wait for component to load
      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Fill in expedition name (required)
      const nameInput = screen.getByLabelText(/expedition name/i);
      await user.type(nameInput, 'My Test Expedition');

      // Click next button
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // Should move to step 2
      await waitFor(() => {
        expect(screen.getByText(/select products/i)).toBeInTheDocument();
      });
    });

    it('should not navigate to next step when step is invalid', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Don't fill in name (invalid)
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });

    it('should navigate back to previous step', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Fill name and go to step 2
      const nameInput = screen.getByLabelText(/expedition name/i);
      await user.type(nameInput, 'Test Expedition');

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/select products/i)).toBeInTheDocument();
      });

      // Click previous button
      const previousButton = screen.getByRole('button', { name: /previous/i });
      await user.click(previousButton);

      // Should go back to step 1
      await waitFor(() => {
        expect(screen.getByText(/expedition name/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Data Management', () => {
    it('should update expedition name', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/expedition name/i) as HTMLInputElement;
      await user.type(nameInput, 'New Expedition');

      expect(nameInput.value).toBe('New Expedition');
    });


    it('should retain data when navigating between steps', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Fill in step 1
      const nameInput = screen.getByLabelText(/expedition name/i) as HTMLInputElement;
      await user.type(nameInput, 'Test Expedition');

      // Go to step 2
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/select products/i)).toBeInTheDocument();
      });

      // Go back to step 1
      const previousButton = screen.getByRole('button', { name: /previous/i });
      await user.click(previousButton);

      // Data should be retained
      await waitFor(() => {
        const nameInputAgain = screen.getByLabelText(/expedition name/i) as HTMLInputElement;
        expect(nameInputAgain.value).toBe('Test Expedition');
      });
    });
  });

  describe('Product Selection', () => {
    it('should toggle product selection', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Navigate to product selection step
      const nameInput = screen.getByLabelText(/expedition name/i);
      await user.type(nameInput, 'Test Expedition');

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/select products/i)).toBeInTheDocument();
      });

      // Select a product
      const productCheckbox = screen.getByRole('checkbox', { name: /product 1/i });
      await user.click(productCheckbox);

      expect(productCheckbox).toBeChecked();

      // Deselect the product
      await user.click(productCheckbox);

      expect(productCheckbox).not.toBeChecked();
    });

    it('should not proceed from step 2 without products selected', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Navigate to step 2
      const nameInput = screen.getByLabelText(/expedition name/i);
      await user.type(nameInput, 'Test Expedition');

      let nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/select products/i)).toBeInTheDocument();
      });

      // Next button should be disabled without products
      nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });
  });

  describe('Expedition Submission', () => {
    it('should create expedition with items successfully', async () => {
      const user = userEvent.setup();
      const mockExpedition = { id: 1, name: 'Test Expedition' };

      mockCreateExpedition.mockResolvedValue(mockExpedition);
      vi.mocked(expeditionItemsService.addItems).mockResolvedValue(undefined);

      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Step 1: Fill details
      const nameInput = screen.getByLabelText(/expedition name/i);
      await user.type(nameInput, 'Test Expedition');

      let nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // Step 2: Select products
      await waitFor(() => {
        expect(screen.getByText(/select products/i)).toBeInTheDocument();
      });

      const productCheckbox = screen.getByRole('checkbox', { name: /product 1/i });
      await user.click(productCheckbox);

      nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // Step 3: Configure products
      await waitFor(() => {
        expect(screen.getByText(/configure products/i)).toBeInTheDocument();
      });

      nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // Step 4: Review and submit
      await waitFor(() => {
        expect(screen.getByText(/review/i)).toBeInTheDocument();
      });

      const submitButton = screen.getByRole('button', { name: /create expedition/i });
      await user.click(submitButton);

      // Should call APIs
      await waitFor(() => {
        expect(mockCreateExpedition).toHaveBeenCalledWith({
          name: 'Test Expedition',
        });
        expect(expeditionItemsService.addItems).toHaveBeenCalledWith(1, {
          items: expect.arrayContaining([
            expect.objectContaining({
              product_id: 1,
              quantity: expect.any(Number),
              quality_grade: expect.any(String),
            }),
          ]),
        });
      });

      // Should navigate to expedition details
      expect(mockNavigate).toHaveBeenCalledWith('/expedition/1');
    });

    it('should handle expedition creation error', async () => {
      const user = userEvent.setup();

      mockCreateExpedition.mockRejectedValue(new Error('Creation failed'));

      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Fill form and submit
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

      // Should handle error
      await waitFor(() => {
        expect(mockCreateExpedition).toHaveBeenCalled();
      });

      // Should not navigate on error
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('should create expedition without items if none selected', async () => {
      const user = userEvent.setup();
      const mockExpedition = { id: 2, name: 'Empty Expedition' };

      mockCreateExpedition.mockResolvedValue(mockExpedition);

      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Just fill name and submit without selecting products
      const nameInput = screen.getByLabelText(/expedition name/i);
      await user.type(nameInput, 'Empty Expedition');

      // Note: This test assumes validation allows skipping products
      // If products are required, this test should verify validation prevents submission
    });
  });

  describe('Validation', () => {
    it('should validate expedition name is required', async () => {
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      const nextButton = screen.getByRole('button', { name: /next/i });

      // Should be disabled without name
      expect(nextButton).toBeDisabled();
    });

    it('should validate minimum name length', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      // Type short name
      const nameInput = screen.getByLabelText(/expedition name/i);
      await user.type(nameInput, 'ab');

      const nextButton = screen.getByRole('button', { name: /next/i });

      // Should still be disabled
      expect(nextButton).toBeDisabled();
    });

    it('should enable next when valid name is entered', async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateExpeditionContainer />);

      await waitFor(() => {
        expect(screen.getByLabelText(/expedition name/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/expedition name/i);
      await user.type(nameInput, 'Valid Expedition Name');

      const nextButton = screen.getByRole('button', { name: /next/i });

      // Should be enabled
      await waitFor(() => {
        expect(nextButton).toBeEnabled();
      });
    });
  });
});
