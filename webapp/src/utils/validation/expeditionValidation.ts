/**
 * Expedition Validation Utilities
 *
 * Centralized validation functions for expedition creation and management.
 * These pure functions ensure data integrity and provide consistent validation
 * across the application.
 */

import { useMemo } from 'react';

/**
 * Product item interface for validation
 */
export interface ExpeditionProductItem {
  product_id: number;
  quantity: number;
  unit_price: number;
}

/**
 * Validates expedition name
 *
 * @param name - The expedition name to validate
 * @returns true if name is valid (not empty after trimming)
 *
 * @example
 * validateExpeditionName("  My Expedition  ") // true
 * validateExpeditionName("   ") // false
 * validateExpeditionName("") // false
 */
export const validateExpeditionName = (name: string): boolean => {
  return name.trim().length > 0;
};

/**
 * Validates that at least one product is selected
 *
 * @param selectedProducts - Array of selected products
 * @returns true if at least one product is selected
 *
 * @example
 * validateSelectedProducts([{...}]) // true
 * validateSelectedProducts([]) // false
 */
export const validateSelectedProducts = (selectedProducts: any[]): boolean => {
  return selectedProducts.length > 0;
};

/**
 * Validates that all products have valid quantities and prices
 *
 * @param selectedProducts - Array of products with quantities and prices
 * @returns true if all products have quantity > 0 and unit_price > 0
 *
 * @example
 * validateProductQuantities([
 *   { product_id: 1, quantity: 5, unit_price: 10.0 }
 * ]) // true
 *
 * validateProductQuantities([
 *   { product_id: 1, quantity: 0, unit_price: 10.0 }
 * ]) // false
 */
export const validateProductQuantities = (selectedProducts: ExpeditionProductItem[]): boolean => {
  return selectedProducts.every(item =>
    item.quantity > 0 && item.unit_price > 0
  );
};

/**
 * Validates expedition deadline
 *
 * @param deadline - The deadline string (ISO date or number of days)
 * @returns true if deadline is valid
 *
 * @example
 * validateDeadline("2025-12-31") // true
 * validateDeadline("7") // true
 * validateDeadline("") // false
 */
export const validateDeadline = (deadline: string): boolean => {
  if (!deadline || deadline.trim().length === 0) {
    return false;
  }

  // Check if it's a number (days)
  const days = parseInt(deadline);
  if (!isNaN(days) && days > 0) {
    return true;
  }

  // Check if it's a valid date
  const date = new Date(deadline);
  return !isNaN(date.getTime()) && date > new Date();
};

/**
 * Validates a complete expedition step based on step number
 *
 * @param step - The current step number (1-4)
 * @param data - The expedition data to validate
 * @returns true if the current step is valid
 *
 * @example
 * validateExpeditionStep(1, { name: "My Expedition", ... }) // true
 * validateExpeditionStep(2, { selectedProducts: [{ ... }], ... }) // true
 */
export const validateExpeditionStep = (
  step: number,
  data: {
    name: string;
    selectedProducts: ExpeditionProductItem[];
  }
): boolean => {
  switch (step) {
    case 1:
      // Step 1: Expedition details - validate name
      return validateExpeditionName(data.name);

    case 2:
      // Step 2: Product selection - validate at least one product selected
      return validateSelectedProducts(data.selectedProducts);

    case 3:
      // Step 3: Quantities and prices - validate all products have valid values
      return validateProductQuantities(data.selectedProducts);

    case 4:
      // Step 4: Review - all validations should already be done
      return true;

    default:
      return false;
  }
};

/**
 * React hook for expedition validation
 *
 * Provides memoized validation functions and current step validation
 *
 * @param expeditionData - The expedition data to validate
 * @param currentStep - The current wizard step
 * @returns Validation functions and current step validity
 *
 * @example
 * const { isCurrentStepValid, isStepValid, canProceed } = useExpeditionValidation(
 *   expeditionData,
 *   currentStep
 * );
 */
export const useExpeditionValidation = (
  expeditionData: {
    name: string;
    selectedProducts: ExpeditionProductItem[];
  },
  currentStep: number
) => {
  // Memoize step validation function
  const isStepValid = useMemo(() => {
    return (step: number): boolean => {
      return validateExpeditionStep(step, expeditionData);
    };
  }, [expeditionData]);

  // Current step validity
  const isCurrentStepValid = useMemo(() => {
    return isStepValid(currentStep);
  }, [isStepValid, currentStep]);

  // Check if all previous steps are valid
  const canProceed = useMemo(() => {
    for (let step = 1; step <= currentStep; step++) {
      if (!isStepValid(step)) {
        return false;
      }
    }
    return true;
  }, [isStepValid, currentStep]);

  return {
    isStepValid,
    isCurrentStepValid,
    canProceed,
    // Individual validators exposed for granular checks
    validators: {
      validateExpeditionName,
      validateSelectedProducts,
      validateProductQuantities,
      validateDeadline,
    }
  };
};
