import { useState, useCallback } from 'react';
import { ItemConsumption } from '@/types/expedition';
import { expeditionItemsService } from '@/services/api/expeditionItemsService';

export interface PaymentCalculations {
  totalPrice: number;
  amountPaid: number;
  remainingAmount: number;
  isFullyPaid: boolean;
}

export interface UseConsumptionPaymentReturn {
  // State
  payingConsumptionId: number | null;
  paymentAmount: string;
  processing: boolean;
  error: string | null;

  // Actions
  startPayment: (consumption: ItemConsumption) => void;
  processPayment: (consumptionId: number, amount: number) => Promise<void>;
  cancelPayment: () => void;
  setPaymentAmount: (amount: string) => void;

  // Utilities
  calculatePaymentDetails: (consumption: ItemConsumption) => PaymentCalculations;
  validatePaymentAmount: (amount: string, maxAmount: number) => boolean;
}

/**
 * Custom hook for managing consumption payment logic
 * Extracts all payment-related business logic from presentation components
 */
export const useConsumptionPayment = (
  onPaymentSuccess?: () => void
): UseConsumptionPaymentReturn => {
  const [payingConsumptionId, setPayingConsumptionId] = useState<number | null>(null);
  const [paymentAmount, setPaymentAmount] = useState<string>('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Pure calculation function for payment details
   */
  const calculatePaymentDetails = useCallback((
    consumption: ItemConsumption
  ): PaymentCalculations => {
    const totalPrice = Number(consumption.total_price) || 0;
    const amountPaid = Number(consumption.amount_paid) || 0;
    const remainingAmount = totalPrice - amountPaid;

    // Validate the result
    if (isNaN(remainingAmount) || !isFinite(remainingAmount)) {
      console.error('Invalid remaining amount calculation:', {
        total_price: consumption.total_price,
        amount_paid: consumption.amount_paid,
        totalPrice,
        amountPaid,
        remainingAmount
      });
      return {
        totalPrice,
        amountPaid,
        remainingAmount: 0,
        isFullyPaid: false
      };
    }

    const finalRemainingAmount = Math.max(0, remainingAmount);

    return {
      totalPrice,
      amountPaid,
      remainingAmount: finalRemainingAmount,
      isFullyPaid: finalRemainingAmount === 0
    };
  }, []);

  /**
   * Validates payment amount against maximum allowed
   */
  const validatePaymentAmount = useCallback((
    amount: string,
    maxAmount: number
  ): boolean => {
    const numAmount = parseFloat(amount);

    if (isNaN(numAmount)) return false;
    if (numAmount <= 0) return false;
    if (numAmount > maxAmount) return false;

    return true;
  }, []);

  /**
   * Initializes payment flow for a consumption
   */
  const startPayment = useCallback((consumption: ItemConsumption) => {
    console.log('Payment click - consumption data:', consumption);

    const { remainingAmount } = calculatePaymentDetails(consumption);
    console.log('Remaining amount:', remainingAmount);

    setPayingConsumptionId(consumption.id);
    setPaymentAmount(remainingAmount.toFixed(2));
    setError(null);
  }, [calculatePaymentDetails]);

  /**
   * Processes the payment via API
   */
  const processPayment = useCallback(async (
    consumptionId: number,
    amount: number
  ) => {
    console.log('[useConsumptionPayment] Starting payment process', { consumptionId, amount });
    setProcessing(true);
    setError(null);

    try {
      // Execute the payment
      console.log('[useConsumptionPayment] Calling payConsumption API');
      await expeditionItemsService.payConsumption({
        consumption_id: consumptionId,
        amount,
      });
      console.log('[useConsumptionPayment] Payment API call succeeded');

      // Wait for the refresh to complete before resetting state
      if (onPaymentSuccess) {
        console.log('[useConsumptionPayment] Calling onPaymentSuccess callback');
        await onPaymentSuccess();
        console.log('[useConsumptionPayment] onPaymentSuccess callback completed');
      }

      // Reset state after refresh completes
      console.log('[useConsumptionPayment] Resetting payment UI state');
      setPayingConsumptionId(null);
      setPaymentAmount('');
      console.log('[useConsumptionPayment] Payment process completed successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Payment failed';
      console.error('[useConsumptionPayment] Payment failed:', err);
      setError(errorMessage);
      // Keep payment UI open on error so user can retry
    } finally {
      setProcessing(false);
    }
  }, [onPaymentSuccess]);

  /**
   * Cancels the payment flow and resets state
   */
  const cancelPayment = useCallback(() => {
    setPayingConsumptionId(null);
    setPaymentAmount('');
    setError(null);
  }, []);

  return {
    // State
    payingConsumptionId,
    paymentAmount,
    processing,
    error,

    // Actions
    startPayment,
    processPayment,
    cancelPayment,
    setPaymentAmount,

    // Utilities
    calculatePaymentDetails,
    validatePaymentAmount,
  };
};
