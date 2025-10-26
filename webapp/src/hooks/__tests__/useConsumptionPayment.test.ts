import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useConsumptionPayment } from '../useConsumptionPayment';
import { expeditionItemsService } from '@/services/api/expeditionItemsService';
import { ItemConsumption } from '@/types/expedition';

// Mock the expedition items service
vi.mock('@/services/api/expeditionItemsService', () => ({
  expeditionItemsService: {
    payConsumption: vi.fn(),
  },
}));

describe('useConsumptionPayment', () => {
  const mockConsumption: ItemConsumption = {
    id: 1,
    consumer_name: 'Blackbeard',
    product_name: 'Rum',
    quantity: 5,
    unit_price: 10,
    total_price: 50,
    amount_paid: 0,
    payment_status: 'pending',
    consumed_at: '2025-01-01T00:00:00Z',
  };

  const mockPartiallyPaidConsumption: ItemConsumption = {
    ...mockConsumption,
    id: 2,
    amount_paid: 20,
    payment_status: 'partial',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should initialize with correct default values', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      expect(result.current.payingConsumptionId).toBeNull();
      expect(result.current.paymentAmount).toBe('');
      expect(result.current.processing).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('calculatePaymentDetails', () => {
    it('should correctly calculate payment details for unpaid consumption', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      const details = result.current.calculatePaymentDetails(mockConsumption);

      expect(details.totalPrice).toBe(50);
      expect(details.amountPaid).toBe(0);
      expect(details.remainingAmount).toBe(50);
      expect(details.isFullyPaid).toBe(false);
    });

    it('should correctly calculate payment details for partially paid consumption', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      const details = result.current.calculatePaymentDetails(mockPartiallyPaidConsumption);

      expect(details.totalPrice).toBe(50);
      expect(details.amountPaid).toBe(20);
      expect(details.remainingAmount).toBe(30);
      expect(details.isFullyPaid).toBe(false);
    });

    it('should handle fully paid consumption', () => {
      const fullyPaid: ItemConsumption = {
        ...mockConsumption,
        amount_paid: 50,
        payment_status: 'paid',
      };
      const { result } = renderHook(() => useConsumptionPayment());

      const details = result.current.calculatePaymentDetails(fullyPaid);

      expect(details.remainingAmount).toBe(0);
      expect(details.isFullyPaid).toBe(true);
    });

    it('should handle invalid numbers gracefully', () => {
      const invalidConsumption: ItemConsumption = {
        ...mockConsumption,
        total_price: NaN,
        amount_paid: NaN,
      };
      const { result } = renderHook(() => useConsumptionPayment());

      const details = result.current.calculatePaymentDetails(invalidConsumption);

      // When numbers are invalid, remaining amount should be 0
      // and treated as fully paid to prevent payment attempts
      expect(details.remainingAmount).toBe(0);
      expect(details.isFullyPaid).toBe(true);
    });
  });

  describe('validatePaymentAmount', () => {
    it('should validate correct payment amount', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      expect(result.current.validatePaymentAmount('25', 50)).toBe(true);
      expect(result.current.validatePaymentAmount('50', 50)).toBe(true);
      expect(result.current.validatePaymentAmount('0.01', 50)).toBe(true);
    });

    it('should reject invalid payment amounts', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      // Zero or negative
      expect(result.current.validatePaymentAmount('0', 50)).toBe(false);
      expect(result.current.validatePaymentAmount('-10', 50)).toBe(false);

      // Exceeds maximum
      expect(result.current.validatePaymentAmount('51', 50)).toBe(false);
      expect(result.current.validatePaymentAmount('100', 50)).toBe(false);

      // Invalid format
      expect(result.current.validatePaymentAmount('abc', 50)).toBe(false);
      expect(result.current.validatePaymentAmount('', 50)).toBe(false);
    });
  });

  describe('startPayment', () => {
    it('should initialize payment state correctly', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      act(() => {
        result.current.startPayment(mockConsumption);
      });

      expect(result.current.payingConsumptionId).toBe(1);
      expect(result.current.paymentAmount).toBe('50.00');
      expect(result.current.error).toBeNull();
    });

    it('should set payment amount to remaining balance for partial payment', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      act(() => {
        result.current.startPayment(mockPartiallyPaidConsumption);
      });

      expect(result.current.payingConsumptionId).toBe(2);
      expect(result.current.paymentAmount).toBe('30.00');
    });
  });

  describe('processPayment', () => {
    it('should successfully process payment', async () => {
      const onSuccess = vi.fn();
      vi.mocked(expeditionItemsService.payConsumption).mockResolvedValue(undefined);

      const { result } = renderHook(() => useConsumptionPayment(onSuccess));

      await act(async () => {
        await result.current.processPayment(1, 50);
      });

      expect(expeditionItemsService.payConsumption).toHaveBeenCalledWith({
        consumption_id: 1,
        amount: 50,
      });
      expect(result.current.payingConsumptionId).toBeNull();
      expect(result.current.paymentAmount).toBe('');
      expect(result.current.processing).toBe(false);
      expect(onSuccess).toHaveBeenCalled();
    });

    it('should handle payment failure', async () => {
      const errorMessage = 'Payment failed';
      vi.mocked(expeditionItemsService.payConsumption).mockRejectedValue(
        new Error(errorMessage)
      );

      const { result } = renderHook(() => useConsumptionPayment());

      // Start payment first
      act(() => {
        result.current.startPayment(mockConsumption);
      });

      await act(async () => {
        await result.current.processPayment(1, 50);
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.processing).toBe(false);
      // Payment UI should remain open for retry
      expect(result.current.payingConsumptionId).toBe(1);
    });

    it('should set processing flag during payment', async () => {
      vi.mocked(expeditionItemsService.payConsumption).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      const { result } = renderHook(() => useConsumptionPayment());

      act(() => {
        result.current.processPayment(1, 50);
      });

      expect(result.current.processing).toBe(true);

      await waitFor(() => {
        expect(result.current.processing).toBe(false);
      });
    });
  });

  describe('cancelPayment', () => {
    it('should reset payment state', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      // Start payment first
      act(() => {
        result.current.startPayment(mockConsumption);
      });

      expect(result.current.payingConsumptionId).toBe(1);
      expect(result.current.paymentAmount).toBe('50.00');

      // Cancel payment
      act(() => {
        result.current.cancelPayment();
      });

      expect(result.current.payingConsumptionId).toBeNull();
      expect(result.current.paymentAmount).toBe('');
      expect(result.current.error).toBeNull();
    });
  });

  describe('setPaymentAmount', () => {
    it('should update payment amount', () => {
      const { result } = renderHook(() => useConsumptionPayment());

      act(() => {
        result.current.setPaymentAmount('25.50');
      });

      expect(result.current.paymentAmount).toBe('25.50');
    });
  });

  describe('Integration: Complete Payment Flow', () => {
    it('should handle complete payment flow from start to finish', async () => {
      const onSuccess = vi.fn();
      vi.mocked(expeditionItemsService.payConsumption).mockResolvedValue(undefined);

      const { result } = renderHook(() => useConsumptionPayment(onSuccess));

      // Step 1: Start payment
      act(() => {
        result.current.startPayment(mockConsumption);
      });
      expect(result.current.payingConsumptionId).toBe(1);
      expect(result.current.paymentAmount).toBe('50.00');

      // Step 2: Modify payment amount
      act(() => {
        result.current.setPaymentAmount('25.00');
      });
      expect(result.current.paymentAmount).toBe('25.00');

      // Step 3: Validate amount
      const isValid = result.current.validatePaymentAmount(
        result.current.paymentAmount,
        50
      );
      expect(isValid).toBe(true);

      // Step 4: Process payment
      await act(async () => {
        await result.current.processPayment(1, 25);
      });

      expect(expeditionItemsService.payConsumption).toHaveBeenCalledWith({
        consumption_id: 1,
        amount: 25,
      });
      expect(result.current.payingConsumptionId).toBeNull();
      expect(onSuccess).toHaveBeenCalled();
    });
  });
});
