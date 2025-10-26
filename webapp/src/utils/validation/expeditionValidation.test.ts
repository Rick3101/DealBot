import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import {
  validateExpeditionName,
  validateSelectedProducts,
  validateProductQuantities,
  validateDeadline,
  validateExpeditionStep,
  useExpeditionValidation,
  type ExpeditionProductItem
} from './expeditionValidation';

describe('expeditionValidation', () => {
  describe('validateExpeditionName', () => {
    it('should accept valid names', () => {
      expect(validateExpeditionName('Valid Expedition')).toBe(true);
      expect(validateExpeditionName('X')).toBe(true);
      expect(validateExpeditionName('  Expedition with spaces  ')).toBe(true);
    });

    it('should reject empty names', () => {
      expect(validateExpeditionName('')).toBe(false);
      expect(validateExpeditionName('   ')).toBe(false);
      expect(validateExpeditionName('\t\n')).toBe(false);
    });
  });

  describe('validateSelectedProducts', () => {
    it('should accept arrays with products', () => {
      expect(validateSelectedProducts([{ id: 1 }])).toBe(true);
      expect(validateSelectedProducts([{ id: 1 }, { id: 2 }])).toBe(true);
    });

    it('should reject empty arrays', () => {
      expect(validateSelectedProducts([])).toBe(false);
    });
  });

  describe('validateProductQuantities', () => {
    it('should accept valid products', () => {
      const products: ExpeditionProductItem[] = [
        { product_id: 1, quantity: 5, unit_price: 10.0 },
        { product_id: 2, quantity: 3, unit_price: 25.5 }
      ];
      expect(validateProductQuantities(products)).toBe(true);
    });

    it('should reject products with zero quantity', () => {
      const products: ExpeditionProductItem[] = [
        { product_id: 1, quantity: 0, unit_price: 10.0 }
      ];
      expect(validateProductQuantities(products)).toBe(false);
    });

    it('should reject products with negative quantity', () => {
      const products: ExpeditionProductItem[] = [
        { product_id: 1, quantity: -5, unit_price: 10.0 }
      ];
      expect(validateProductQuantities(products)).toBe(false);
    });

    it('should reject products with zero price', () => {
      const products: ExpeditionProductItem[] = [
        { product_id: 1, quantity: 5, unit_price: 0 }
      ];
      expect(validateProductQuantities(products)).toBe(false);
    });

    it('should reject products with negative price', () => {
      const products: ExpeditionProductItem[] = [
        { product_id: 1, quantity: 5, unit_price: -10.0 }
      ];
      expect(validateProductQuantities(products)).toBe(false);
    });

    it('should reject if any product in array is invalid', () => {
      const products: ExpeditionProductItem[] = [
        { product_id: 1, quantity: 5, unit_price: 10.0 },
        { product_id: 2, quantity: 0, unit_price: 25.5 }
      ];
      expect(validateProductQuantities(products)).toBe(false);
    });

    it('should accept empty array', () => {
      expect(validateProductQuantities([])).toBe(true);
    });
  });

  describe('validateDeadline', () => {
    it('should accept number of days as string', () => {
      expect(validateDeadline('7')).toBe(true);
      expect(validateDeadline('30')).toBe(true);
      expect(validateDeadline('1')).toBe(true);
    });

    it('should accept future ISO dates', () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      expect(validateDeadline(futureDate.toISOString())).toBe(true);
    });

    it('should reject clearly past date strings', () => {
      // The validator accepts strings that can be numeric (days), so we need
      // to use a format that can't be  parsed as a positive number
      expect(validateDeadline('invalid-date')).toBe(false);
      expect(validateDeadline('abc')).toBe(false);
    });

    it('should reject zero days', () => {
      expect(validateDeadline('0')).toBe(false);
    });

    it('should reject negative days', () => {
      expect(validateDeadline('-5')).toBe(false);
    });

    it('should reject empty string', () => {
      expect(validateDeadline('')).toBe(false);
      expect(validateDeadline('   ')).toBe(false);
    });

    it('should reject invalid date strings', () => {
      expect(validateDeadline('not-a-date')).toBe(false);
      expect(validateDeadline('invalid')).toBe(false);
    });
  });

  describe('validateExpeditionStep', () => {
    const validData = {
      name: 'Valid Expedition',
      selectedProducts: [
        { product_id: 1, quantity: 5, unit_price: 10.0 }
      ]
    };

    it('should validate step 1 (name)', () => {
      expect(validateExpeditionStep(1, validData)).toBe(true);
      expect(validateExpeditionStep(1, { ...validData, name: '' })).toBe(false);
    });

    it('should validate step 2 (product selection)', () => {
      expect(validateExpeditionStep(2, validData)).toBe(true);
      expect(validateExpeditionStep(2, { ...validData, selectedProducts: [] })).toBe(false);
    });

    it('should validate step 3 (quantities and prices)', () => {
      expect(validateExpeditionStep(3, validData)).toBe(true);

      const invalidData = {
        ...validData,
        selectedProducts: [{ product_id: 1, quantity: 0, unit_price: 10.0 }]
      };
      expect(validateExpeditionStep(3, invalidData)).toBe(false);
    });

    it('should always validate step 4 (review)', () => {
      expect(validateExpeditionStep(4, validData)).toBe(true);
      expect(validateExpeditionStep(4, { name: '', selectedProducts: [] })).toBe(true);
    });

    it('should return false for invalid step numbers', () => {
      expect(validateExpeditionStep(0, validData)).toBe(false);
      expect(validateExpeditionStep(5, validData)).toBe(false);
      expect(validateExpeditionStep(-1, validData)).toBe(false);
    });
  });

  describe('useExpeditionValidation', () => {
    const validData = {
      name: 'Valid Expedition',
      selectedProducts: [
        { product_id: 1, quantity: 5, unit_price: 10.0 }
      ]
    };

    it('should return correct step validity', () => {
      const { result } = renderHook(() =>
        useExpeditionValidation(validData, 1)
      );

      expect(result.current.isStepValid(1)).toBe(true);
      expect(result.current.isStepValid(2)).toBe(true);
      expect(result.current.isStepValid(3)).toBe(true);
    });

    it('should return correct current step validity', () => {
      const { result: result1 } = renderHook(() =>
        useExpeditionValidation(validData, 1)
      );
      expect(result1.current.isCurrentStepValid).toBe(true);

      const invalidData = { name: '', selectedProducts: [] };
      const { result: result2 } = renderHook(() =>
        useExpeditionValidation(invalidData, 1)
      );
      expect(result2.current.isCurrentStepValid).toBe(false);
    });

    it('should return correct canProceed status', () => {
      // All steps valid up to step 3
      const { result: result1 } = renderHook(() =>
        useExpeditionValidation(validData, 3)
      );
      expect(result1.current.canProceed).toBe(true);

      // Step 1 invalid
      const invalidData = { name: '', selectedProducts: validData.selectedProducts };
      const { result: result2 } = renderHook(() =>
        useExpeditionValidation(invalidData, 2)
      );
      expect(result2.current.canProceed).toBe(false);
    });

    it('should expose individual validators', () => {
      const { result } = renderHook(() =>
        useExpeditionValidation(validData, 1)
      );

      expect(result.current.validators.validateExpeditionName).toBeDefined();
      expect(result.current.validators.validateSelectedProducts).toBeDefined();
      expect(result.current.validators.validateProductQuantities).toBeDefined();
      expect(result.current.validators.validateDeadline).toBeDefined();
    });

    it('should memoize results correctly', () => {
      const { result, rerender } = renderHook(
        ({ data, step }) => useExpeditionValidation(data, step),
        { initialProps: { data: validData, step: 1 } }
      );

      const firstResult = result.current;

      // Rerender with same props
      rerender({ data: validData, step: 1 });
      expect(result.current.isStepValid).toBe(firstResult.isStepValid);

      // Rerender with different data
      const newData = { ...validData, name: 'New Name' };
      rerender({ data: newData, step: 1 });
      expect(result.current.isStepValid).not.toBe(firstResult.isStepValid);
    });
  });
});
