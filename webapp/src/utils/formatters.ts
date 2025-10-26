/**
 * Centralized formatting utilities for the Pirates Expedition Mini App
 *
 * This module provides consistent formatting functions for currency, dates, and other data types
 * across the entire application. All formatting logic should be centralized here to ensure
 * consistency and maintainability.
 */

/**
 * Formats a number as Brazilian Real (BRL) currency
 *
 * @param value - The numeric value to format
 * @returns Formatted currency string (e.g., "R$ 1.234,56")
 *
 * @example
 * formatCurrency(1234.56) // "R$ 1.234,56"
 * formatCurrency(0) // "R$ 0,00"
 */
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

/**
 * Formats a date string as a localized date with time
 *
 * @param dateString - ISO date string or any valid date format
 * @returns Formatted date string (e.g., "05/10/2025 14:30")
 *
 * @example
 * formatDateTime("2025-10-05T14:30:00Z") // "05/10/2025 14:30"
 */
export const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Formats a date string as a localized date only (no time)
 *
 * @param dateString - ISO date string or any valid date format
 * @returns Formatted date string (e.g., "05/10/2025")
 *
 * @example
 * formatDate("2025-10-05T14:30:00Z") // "05/10/2025"
 */
export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

/**
 * Formats a number as a percentage with specified decimal places
 *
 * @param value - The numeric value to format (0-1 or 0-100 depending on isDecimal)
 * @param decimals - Number of decimal places (default: 1)
 * @param isDecimal - Whether the value is in decimal form (0-1) or percentage form (0-100) (default: true)
 * @returns Formatted percentage string (e.g., "75.5%")
 *
 * @example
 * formatPercentage(0.755) // "75.5%"
 * formatPercentage(75.5, 1, false) // "75.5%"
 * formatPercentage(0.7555, 2) // "75.55%"
 */
export const formatPercentage = (value: number, decimals: number = 1, isDecimal: boolean = true): string => {
  const percentage = isDecimal ? value * 100 : value;
  return `${percentage.toFixed(decimals)}%`;
};

/**
 * Formats a number with thousands separators
 *
 * @param value - The numeric value to format
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted number string (e.g., "1.234,56")
 *
 * @example
 * formatNumber(1234.56) // "1.235"
 * formatNumber(1234.56, 2) // "1.234,56"
 */
export const formatNumber = (value: number, decimals: number = 0): string => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Formats a relative time difference (e.g., "2 days ago", "in 3 hours")
 *
 * @param dateString - ISO date string or any valid date format
 * @returns Human-readable relative time string
 *
 * @example
 * formatRelativeTime("2025-10-03T14:30:00Z") // "2 days ago" (if today is Oct 5)
 * formatRelativeTime("2025-10-07T14:30:00Z") // "in 2 days" (if today is Oct 5)
 */
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.round(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.round(diffMs / (1000 * 60));

  if (Math.abs(diffDays) > 0) {
    return diffDays > 0
      ? `em ${diffDays} dia${diffDays !== 1 ? 's' : ''}`
      : `${Math.abs(diffDays)} dia${Math.abs(diffDays) !== 1 ? 's' : ''} atrás`;
  } else if (Math.abs(diffHours) > 0) {
    return diffHours > 0
      ? `em ${diffHours} hora${diffHours !== 1 ? 's' : ''}`
      : `${Math.abs(diffHours)} hora${Math.abs(diffHours) !== 1 ? 's' : ''} atrás`;
  } else {
    return diffMinutes > 0
      ? `em ${diffMinutes} minuto${diffMinutes !== 1 ? 's' : ''}`
      : `${Math.abs(diffMinutes)} minuto${Math.abs(diffMinutes) !== 1 ? 's' : ''} atrás`;
  }
};
