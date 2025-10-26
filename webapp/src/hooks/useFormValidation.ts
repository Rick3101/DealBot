import { useMemo } from 'react';

export interface NumericValidationResult {
  isValid: boolean;
  value: number;
  errors: string[];
}

export interface StringValidationResult {
  isValid: boolean;
  value: string;
  errors: string[];
}

/**
 * Hook for validating numeric input values
 * Provides comprehensive validation with min/max bounds checking
 *
 * @param value - The value to validate (string or number)
 * @param options - Validation options
 * @returns Validation result with parsed value and error messages
 *
 * @example
 * const validation = useNumericValidation(inputValue, { min: 0, max: 100, required: true });
 * if (!validation.isValid) {
 *   console.error(validation.errors);
 * }
 */
export const useNumericValidation = (
  value: string | number,
  options?: {
    min?: number;
    max?: number;
    required?: boolean;
    integer?: boolean;
    positive?: boolean;
  }
): NumericValidationResult => {
  return useMemo(() => {
    const errors: string[] = [];
    const stringValue = typeof value === 'number' ? value.toString() : value;

    // Check if required
    if (options?.required && (!stringValue || stringValue.trim() === '')) {
      errors.push('This field is required');
      return {
        isValid: false,
        value: 0,
        errors,
      };
    }

    // If empty and not required, it's valid
    if (!stringValue || stringValue.trim() === '') {
      return {
        isValid: true,
        value: 0,
        errors: [],
      };
    }

    // Parse the number
    const numericValue = parseFloat(stringValue);

    // Check if it's a valid number
    if (isNaN(numericValue) || !isFinite(numericValue)) {
      errors.push('Must be a valid number');
      return {
        isValid: false,
        value: 0,
        errors,
      };
    }

    // Check if integer is required
    if (options?.integer && !Number.isInteger(numericValue)) {
      errors.push('Must be a whole number');
    }

    // Check if positive is required
    if (options?.positive && numericValue <= 0) {
      errors.push('Must be a positive number');
    }

    // Check minimum value
    if (options?.min !== undefined && numericValue < options.min) {
      errors.push(`Must be at least ${options.min}`);
    }

    // Check maximum value
    if (options?.max !== undefined && numericValue > options.max) {
      errors.push(`Must be at most ${options.max}`);
    }

    return {
      isValid: errors.length === 0,
      value: numericValue,
      errors,
    };
  }, [value, options?.min, options?.max, options?.required, options?.integer, options?.positive]);
};

/**
 * Hook for validating string input values
 * Provides validation for common string requirements
 *
 * @param value - The string value to validate
 * @param options - Validation options
 * @returns Validation result with trimmed value and error messages
 *
 * @example
 * const validation = useStringValidation(username, {
 *   required: true,
 *   minLength: 3,
 *   maxLength: 20,
 *   pattern: /^[a-zA-Z0-9]+$/
 * });
 */
export const useStringValidation = (
  value: string,
  options?: {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    patternMessage?: string;
  }
): StringValidationResult => {
  return useMemo(() => {
    const errors: string[] = [];
    const trimmedValue = value.trim();

    // Check if required
    if (options?.required && trimmedValue === '') {
      errors.push('This field is required');
      return {
        isValid: false,
        value: trimmedValue,
        errors,
      };
    }

    // If empty and not required, it's valid
    if (trimmedValue === '') {
      return {
        isValid: true,
        value: trimmedValue,
        errors: [],
      };
    }

    // Check minimum length
    if (options?.minLength !== undefined && trimmedValue.length < options.minLength) {
      errors.push(`Must be at least ${options.minLength} characters`);
    }

    // Check maximum length
    if (options?.maxLength !== undefined && trimmedValue.length > options.maxLength) {
      errors.push(`Must be at most ${options.maxLength} characters`);
    }

    // Check pattern
    if (options?.pattern && !options.pattern.test(trimmedValue)) {
      errors.push(options.patternMessage || 'Invalid format');
    }

    return {
      isValid: errors.length === 0,
      value: trimmedValue,
      errors,
    };
  }, [value, options?.required, options?.minLength, options?.maxLength, options?.pattern, options?.patternMessage]);
};

/**
 * Hook for validating email addresses
 * Uses a standard email regex pattern
 *
 * @param value - The email value to validate
 * @param required - Whether the field is required
 * @returns Validation result
 */
export const useEmailValidation = (
  value: string,
  required: boolean = false
): StringValidationResult => {
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  return useStringValidation(value, {
    required,
    pattern: emailPattern,
    patternMessage: 'Must be a valid email address',
  });
};

/**
 * Hook for validating price/currency values
 * Ensures positive numbers with up to 2 decimal places
 *
 * @param value - The price value to validate
 * @param options - Additional validation options
 * @returns Validation result
 */
export const usePriceValidation = (
  value: string | number,
  options?: {
    min?: number;
    max?: number;
    required?: boolean;
  }
): NumericValidationResult => {
  const result = useNumericValidation(value, {
    ...options,
    positive: true,
  });

  // Additional check for decimal places (max 2)
  if (result.isValid && result.value > 0) {
    const decimalPlaces = (result.value.toString().split('.')[1] || '').length;
    if (decimalPlaces > 2) {
      return {
        ...result,
        isValid: false,
        errors: [...result.errors, 'Maximum 2 decimal places allowed'],
      };
    }
  }

  return result;
};

/**
 * Hook for validating quantity values
 * Ensures positive integers
 *
 * @param value - The quantity value to validate
 * @param options - Additional validation options
 * @returns Validation result
 */
export const useQuantityValidation = (
  value: string | number,
  options?: {
    min?: number;
    max?: number;
    required?: boolean;
  }
): NumericValidationResult => {
  return useNumericValidation(value, {
    ...options,
    integer: true,
    positive: true,
    min: options?.min ?? 1, // Default minimum is 1
  });
};
