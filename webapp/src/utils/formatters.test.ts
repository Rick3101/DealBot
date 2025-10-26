import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  formatCurrency,
  formatDateTime,
  formatDate,
  formatPercentage,
  formatNumber,
  formatRelativeTime
} from './formatters';

describe('formatters', () => {
  describe('formatCurrency', () => {
    it('should format positive numbers correctly', () => {
      expect(formatCurrency(1234.56)).toBe('R$\u00A01.234,56');
      expect(formatCurrency(100)).toBe('R$\u00A0100,00');
      expect(formatCurrency(0.99)).toBe('R$\u00A00,99');
    });

    it('should format zero correctly', () => {
      expect(formatCurrency(0)).toBe('R$\u00A00,00');
    });

    it('should format negative numbers correctly', () => {
      expect(formatCurrency(-1234.56)).toBe('-R$\u00A01.234,56');
    });

    it('should handle large numbers', () => {
      expect(formatCurrency(1234567.89)).toBe('R$\u00A01.234.567,89');
    });

    it('should round decimal places correctly', () => {
      expect(formatCurrency(1.995)).toBe('R$\u00A02,00');
      expect(formatCurrency(1.994)).toBe('R$\u00A01,99');
    });
  });

  describe('formatDateTime', () => {
    it('should format ISO date strings correctly', () => {
      const result = formatDateTime('2025-10-05T14:30:00Z');
      expect(result).toMatch(/05\/10\/2025/);
      expect(result).toContain(':');
    });

    it('should handle different date formats', () => {
      const result = formatDateTime('2025-01-15T09:05:00Z');
      expect(result).toMatch(/15\/01\/2025/);
      expect(result).toContain(':');
    });

    it('should format midnight correctly', () => {
      const result = formatDateTime('2025-10-05T00:00:00Z');
      // Date portion should be present, time portion depends on timezone
      expect(result).toContain('/10/2025');
      expect(result).toContain(':');
    });
  });

  describe('formatDate', () => {
    it('should format ISO date strings without time', () => {
      const result = formatDate('2025-10-05T14:30:00Z');
      expect(result).toMatch(/\/10\/2025$/);
    });

    it('should handle different dates', () => {
      const result1 = formatDate('2025-01-01T12:00:00Z');
      expect(result1).toMatch(/\/01\/2025$/);

      const result2 = formatDate('2025-12-31T12:00:00Z');
      expect(result2).toMatch(/31\/12\/2025$/);
    });
  });

  describe('formatPercentage', () => {
    it('should format decimal values (0-1) by default', () => {
      expect(formatPercentage(0.755)).toBe('75.5%');
      expect(formatPercentage(0.5)).toBe('50.0%');
      expect(formatPercentage(1)).toBe('100.0%');
      expect(formatPercentage(0)).toBe('0.0%');
    });

    it('should format percentage values (0-100) when isDecimal is false', () => {
      expect(formatPercentage(75.5, 1, false)).toBe('75.5%');
      expect(formatPercentage(100, 1, false)).toBe('100.0%');
    });

    it('should respect custom decimal places', () => {
      expect(formatPercentage(0.7555, 2)).toBe('75.55%');
      expect(formatPercentage(0.7555, 0)).toBe('76%');
      expect(formatPercentage(0.7555, 3)).toBe('75.550%');
    });

    it('should handle edge cases', () => {
      expect(formatPercentage(0.001, 1)).toBe('0.1%');
      expect(formatPercentage(1.5, 1)).toBe('150.0%');
    });
  });

  describe('formatNumber', () => {
    it('should format integers with thousand separators', () => {
      expect(formatNumber(1234)).toBe('1.234');
      expect(formatNumber(1234567)).toBe('1.234.567');
    });

    it('should format with custom decimal places', () => {
      expect(formatNumber(1234.56, 2)).toBe('1.234,56');
      expect(formatNumber(1234.567, 3)).toBe('1.234,567');
    });

    it('should default to zero decimals', () => {
      expect(formatNumber(1234.56)).toBe('1.235');
      expect(formatNumber(1234.4)).toBe('1.234');
    });

    it('should handle zero and negative numbers', () => {
      expect(formatNumber(0)).toBe('0');
      expect(formatNumber(-1234.56, 2)).toBe('-1.234,56');
    });
  });

  describe('formatRelativeTime', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should format future dates in days', () => {
      const now = new Date('2025-10-05T12:00:00Z');
      vi.setSystemTime(now);

      expect(formatRelativeTime('2025-10-07T12:00:00Z')).toBe('em 2 dias');
      expect(formatRelativeTime('2025-10-06T12:00:00Z')).toBe('em 1 dia');
    });

    it('should format past dates in days', () => {
      const now = new Date('2025-10-05T12:00:00Z');
      vi.setSystemTime(now);

      expect(formatRelativeTime('2025-10-03T12:00:00Z')).toBe('2 dias atrás');
      expect(formatRelativeTime('2025-10-04T12:00:00Z')).toBe('1 dia atrás');
    });

    it('should format future dates in hours for same day', () => {
      const now = new Date('2025-10-05T12:00:00Z');
      vi.setSystemTime(now);

      expect(formatRelativeTime('2025-10-05T15:00:00Z')).toBe('em 3 horas');
      expect(formatRelativeTime('2025-10-05T13:00:00Z')).toBe('em 1 hora');
    });

    it('should format past dates in hours for same day', () => {
      const now = new Date('2025-10-05T12:00:00Z');
      vi.setSystemTime(now);

      expect(formatRelativeTime('2025-10-05T09:00:00Z')).toBe('3 horas atrás');
      expect(formatRelativeTime('2025-10-05T11:00:00Z')).toBe('1 hora atrás');
    });

    it('should format future dates in minutes for same hour', () => {
      const now = new Date('2025-10-05T12:00:00Z');
      vi.setSystemTime(now);

      // Test 1 minute which is less likely to round to hours
      expect(formatRelativeTime('2025-10-05T12:01:00Z')).toBe('em 1 minuto');
      expect(formatRelativeTime('2025-10-05T12:15:00Z')).toMatch(/em \d+ minuto/);
    });

    it('should format past dates in minutes for same hour', () => {
      const now = new Date('2025-10-05T12:30:00Z');
      vi.setSystemTime(now);

      expect(formatRelativeTime('2025-10-05T12:00:00Z')).toBe('30 minutos atrás');
      expect(formatRelativeTime('2025-10-05T12:29:00Z')).toBe('1 minuto atrás');
    });

    it('should handle singular vs plural correctly', () => {
      const now = new Date('2025-10-05T12:00:00Z');
      vi.setSystemTime(now);

      expect(formatRelativeTime('2025-10-06T12:00:00Z')).toBe('em 1 dia');
      expect(formatRelativeTime('2025-10-07T12:00:00Z')).toBe('em 2 dias');
      expect(formatRelativeTime('2025-10-05T13:00:00Z')).toBe('em 1 hora');
      expect(formatRelativeTime('2025-10-05T14:00:00Z')).toBe('em 2 horas');
    });
  });
});
