/**
 * Product Transform Utilities Tests
 *
 * Comprehensive test suite for product transformation functions
 */

import { describe, it, expect } from 'vitest';
import {
  toSelectionState,
  getSelectedProducts,
  getSelectedProductIds,
  countSelectedProducts,
  hasSelectedProducts,
  toggleProductSelection,
  selectAllProducts,
  deselectAllProducts,
  filterProductsBySearch,
  filterProductsByAvailability,
  sortProductsByName,
  sortProductsByStock,
  groupProductsByAvailability,
  toProductWithConfig,
  validateProductConfig,
  calculateTotalTargetValue,
  filterConfigsByQuality,
  groupConfigsByQuality,
  ProductSelectionState,
  ProductWithConfig,
} from './productTransforms';

// Mock product data
const mockProducts = [
  { id: '1', name: 'Rum', emoji: '🍾', price: 10, stock: 50, status: 'active' },
  { id: '2', name: 'Treasure Map', emoji: '🗺️', price: 100, stock: 5, status: 'active' },
  { id: '3', name: 'Compass', emoji: '🧭', price: 25, stock: 0, status: 'inactive' },
  { id: '4', name: 'Sword', emoji: '⚔️', price: 75, stock: 15, status: 'active' },
  { id: '5', name: 'Parrot', emoji: '🦜', price: 200, stock: 3, status: 'active' },
];

describe('productTransforms', () => {
  describe('Selection State Management', () => {
    describe('toSelectionState', () => {
      it('should create selection state with all false by default', () => {
        const state = toSelectionState(mockProducts);

        expect(state).toEqual({
          '1': false,
          '2': false,
          '3': false,
          '4': false,
          '5': false,
        });
      });

      it('should create selection state with all true when initiallySelected is true', () => {
        const state = toSelectionState(mockProducts, true);

        expect(Object.values(state).every(v => v === true)).toBe(true);
      });

      it('should handle empty products array', () => {
        const state = toSelectionState([]);

        expect(state).toEqual({});
      });
    });

    describe('getSelectedProducts', () => {
      it('should return only selected products', () => {
        const selectionState: ProductSelectionState = {
          '1': true,
          '2': false,
          '3': true,
          '4': false,
          '5': false,
        };

        const selected = getSelectedProducts(mockProducts, selectionState);

        expect(selected).toHaveLength(2);
        expect(selected[0].id).toBe('1');
        expect(selected[1].id).toBe('3');
      });

      it('should return empty array when nothing is selected', () => {
        const selectionState = toSelectionState(mockProducts, false);
        const selected = getSelectedProducts(mockProducts, selectionState);

        expect(selected).toEqual([]);
      });

      it('should return all products when all are selected', () => {
        const selectionState = toSelectionState(mockProducts, true);
        const selected = getSelectedProducts(mockProducts, selectionState);

        expect(selected).toHaveLength(mockProducts.length);
      });
    });

    describe('getSelectedProductIds', () => {
      it('should return IDs of selected products', () => {
        const selectionState: ProductSelectionState = {
          '1': true,
          '2': false,
          '3': true,
          '4': true,
          '5': false,
        };

        const ids = getSelectedProductIds(selectionState);

        expect(ids).toEqual(['1', '3', '4']);
      });

      it('should return empty array when nothing is selected', () => {
        const selectionState = toSelectionState(mockProducts, false);
        const ids = getSelectedProductIds(selectionState);

        expect(ids).toEqual([]);
      });
    });

    describe('countSelectedProducts', () => {
      it('should count selected products correctly', () => {
        const selectionState: ProductSelectionState = {
          '1': true,
          '2': false,
          '3': true,
          '4': true,
          '5': false,
        };

        const count = countSelectedProducts(selectionState);

        expect(count).toBe(3);
      });

      it('should return 0 when nothing is selected', () => {
        const selectionState = toSelectionState(mockProducts, false);
        const count = countSelectedProducts(selectionState);

        expect(count).toBe(0);
      });

      it('should count all when all are selected', () => {
        const selectionState = toSelectionState(mockProducts, true);
        const count = countSelectedProducts(selectionState);

        expect(count).toBe(mockProducts.length);
      });
    });

    describe('hasSelectedProducts', () => {
      it('should return true when at least one product is selected', () => {
        const selectionState: ProductSelectionState = {
          '1': false,
          '2': true,
          '3': false,
        };

        expect(hasSelectedProducts(selectionState)).toBe(true);
      });

      it('should return false when no products are selected', () => {
        const selectionState = toSelectionState(mockProducts, false);

        expect(hasSelectedProducts(selectionState)).toBe(false);
      });
    });

    describe('toggleProductSelection', () => {
      it('should toggle product from false to true', () => {
        const selectionState: ProductSelectionState = { '1': false, '2': false };

        const newState = toggleProductSelection(selectionState, '1');

        expect(newState['1']).toBe(true);
        expect(newState['2']).toBe(false);
      });

      it('should toggle product from true to false', () => {
        const selectionState: ProductSelectionState = { '1': true, '2': false };

        const newState = toggleProductSelection(selectionState, '1');

        expect(newState['1']).toBe(false);
      });

      it('should not mutate original state', () => {
        const selectionState: ProductSelectionState = { '1': false };

        toggleProductSelection(selectionState, '1');

        expect(selectionState['1']).toBe(false);
      });
    });

    describe('selectAllProducts', () => {
      it('should select all products', () => {
        const state = selectAllProducts(mockProducts);

        expect(Object.values(state).every(v => v === true)).toBe(true);
        expect(Object.keys(state)).toHaveLength(mockProducts.length);
      });
    });

    describe('deselectAllProducts', () => {
      it('should deselect all products', () => {
        const state = deselectAllProducts(mockProducts);

        expect(Object.values(state).every(v => v === false)).toBe(true);
        expect(Object.keys(state)).toHaveLength(mockProducts.length);
      });
    });
  });

  describe('Filtering', () => {
    describe('filterProductsBySearch', () => {
      it('should filter by product name (case insensitive)', () => {
        const filtered = filterProductsBySearch(mockProducts, 'rum');

        expect(filtered).toHaveLength(1);
        expect(filtered[0].name).toBe('Rum');
      });

      it('should filter by emoji', () => {
        const filtered = filterProductsBySearch(mockProducts, '🗺️');

        expect(filtered).toHaveLength(1);
        expect(filtered[0].name).toBe('Treasure Map');
      });

      it('should return all products when query is empty', () => {
        const filtered = filterProductsBySearch(mockProducts, '');

        expect(filtered).toHaveLength(mockProducts.length);
      });

      it('should return all products when query is whitespace', () => {
        const filtered = filterProductsBySearch(mockProducts, '   ');

        expect(filtered).toHaveLength(mockProducts.length);
      });

      it('should return empty array when no matches', () => {
        const filtered = filterProductsBySearch(mockProducts, 'nonexistent');

        expect(filtered).toEqual([]);
      });

      it('should filter by partial name match', () => {
        const filtered = filterProductsBySearch(mockProducts, 'rea'); // Matches "Treasure"

        expect(filtered).toHaveLength(1);
        expect(filtered[0].name).toBe('Treasure Map');
      });
    });

    describe('filterProductsByAvailability', () => {
      it('should return only products with stock > 0 when availableOnly is true', () => {
        const filtered = filterProductsByAvailability(mockProducts, true);

        expect(filtered).toHaveLength(4);
        expect(filtered.every(p => p.stock > 0)).toBe(true);
      });

      it('should return all products when availableOnly is false', () => {
        const filtered = filterProductsByAvailability(mockProducts, false);

        expect(filtered).toHaveLength(mockProducts.length);
      });
    });
  });

  describe('Sorting', () => {
    describe('sortProductsByName', () => {
      it('should sort products by name ascending', () => {
        const sorted = sortProductsByName(mockProducts, true);

        expect(sorted[0].name).toBe('Compass');
        expect(sorted[sorted.length - 1].name).toBe('Treasure Map');
      });

      it('should sort products by name descending', () => {
        const sorted = sortProductsByName(mockProducts, false);

        expect(sorted[0].name).toBe('Treasure Map');
        expect(sorted[sorted.length - 1].name).toBe('Compass');
      });

      it('should not mutate original array', () => {
        const original = [...mockProducts];
        sortProductsByName(mockProducts, true);

        expect(mockProducts).toEqual(original);
      });
    });

    describe('sortProductsByStock', () => {
      it('should sort products by stock descending (default)', () => {
        const sorted = sortProductsByStock(mockProducts);

        expect(sorted[0].stock).toBe(50); // Rum
        expect(sorted[sorted.length - 1].stock).toBe(0); // Compass
      });

      it('should sort products by stock ascending', () => {
        const sorted = sortProductsByStock(mockProducts, true);

        expect(sorted[0].stock).toBe(0); // Compass
        expect(sorted[sorted.length - 1].stock).toBe(50); // Rum
      });

      it('should handle undefined stock as 0', () => {
        const productsWithUndefined = [
          { id: '1', name: 'A', emoji: '🅰️', price: 10, stock: 5, status: 'active' },
          { id: '2', name: 'B', emoji: '🅱️', price: 10, stock: undefined as any, status: 'active' },
        ];

        const sorted = sortProductsByStock(productsWithUndefined, true);

        expect(sorted[0].id).toBe('2'); // Undefined treated as 0
      });
    });
  });

  describe('Grouping', () => {
    describe('groupProductsByAvailability', () => {
      it('should group products into available and unavailable', () => {
        const grouped = groupProductsByAvailability(mockProducts);

        expect(grouped.available).toHaveLength(4);
        expect(grouped.unavailable).toHaveLength(1);
        expect(grouped.unavailable[0].name).toBe('Compass');
      });

      it('should handle all products available', () => {
        const availableProducts = mockProducts.filter(p => p.stock > 0);
        const grouped = groupProductsByAvailability(availableProducts);

        expect(grouped.available).toHaveLength(4);
        expect(grouped.unavailable).toHaveLength(0);
      });

      it('should handle all products unavailable', () => {
        const unavailableProducts = mockProducts.map(p => ({ ...p, stock: 0 }));
        const grouped = groupProductsByAvailability(unavailableProducts);

        expect(grouped.available).toHaveLength(0);
        expect(grouped.unavailable).toHaveLength(mockProducts.length);
      });
    });
  });

  describe('Product Configuration', () => {
    describe('toProductWithConfig', () => {
      it('should create product config with defaults', () => {
        const config = toProductWithConfig(mockProducts[0]);

        expect(config).toEqual({
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: 1,
          quality: 'medium',
          target_price: undefined,
        });
      });

      it('should create product config with custom values', () => {
        const config = toProductWithConfig(mockProducts[0], 5, 'high', 50);

        expect(config).toEqual({
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: 5,
          quality: 'high',
          target_price: 50,
        });
      });

      it('should handle product without emoji', () => {
        const productNoEmoji = { ...mockProducts[0], emoji: undefined };
        const config = toProductWithConfig(productNoEmoji);

        expect(config.emoji).toBeUndefined();
      });
    });

    describe('validateProductConfig', () => {
      it('should return null for valid config', () => {
        const config: ProductWithConfig = {
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: 5,
          quality: 'high',
          target_price: 50,
        };

        const errors = validateProductConfig(config);

        expect(errors).toBeNull();
      });

      it('should return error for quantity <= 0', () => {
        const config: ProductWithConfig = {
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: 0,
          quality: 'medium',
        };

        const errors = validateProductConfig(config);

        expect(errors).not.toBeNull();
        expect(errors?.quantity).toBe('Quantity must be greater than 0');
      });

      it('should return error for negative quantity', () => {
        const config: ProductWithConfig = {
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: -5,
          quality: 'medium',
        };

        const errors = validateProductConfig(config);

        expect(errors?.quantity).toBe('Quantity must be greater than 0');
      });

      it('should return error for invalid quality', () => {
        const config: ProductWithConfig = {
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: 1,
          quality: 'invalid' as any,
        };

        const errors = validateProductConfig(config);

        expect(errors?.quality).toBe('Quality must be low, medium, or high');
      });

      it('should return error for target_price <= 0', () => {
        const config: ProductWithConfig = {
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: 1,
          quality: 'medium',
          target_price: 0,
        };

        const errors = validateProductConfig(config);

        expect(errors?.targetPrice).toBe('Target price must be greater than 0');
      });

      it('should return multiple errors when multiple fields are invalid', () => {
        const config: ProductWithConfig = {
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: -1,
          quality: 'invalid' as any,
          target_price: -50,
        };

        const errors = validateProductConfig(config);

        expect(errors).not.toBeNull();
        expect(errors?.quantity).toBeDefined();
        expect(errors?.quality).toBeDefined();
        expect(errors?.targetPrice).toBeDefined();
      });

      it('should accept undefined target_price', () => {
        const config: ProductWithConfig = {
          id: '1',
          name: 'Rum',
          emoji: '🍾',
          quantity: 5,
          quality: 'medium',
          target_price: undefined,
        };

        const errors = validateProductConfig(config);

        expect(errors).toBeNull();
      });
    });

    describe('calculateTotalTargetValue', () => {
      it('should calculate total value from configs', () => {
        const configs: ProductWithConfig[] = [
          { id: '1', name: 'Rum', emoji: '🍾', quantity: 5, quality: 'medium', target_price: 10 },
          { id: '2', name: 'Map', emoji: '🗺️', quantity: 2, quality: 'high', target_price: 100 },
          { id: '3', name: 'Sword', emoji: '⚔️', quantity: 3, quality: 'low', target_price: 25 },
        ];

        const total = calculateTotalTargetValue(configs);

        expect(total).toBe(5 * 10 + 2 * 100 + 3 * 25); // 50 + 200 + 75 = 325
      });

      it('should handle configs without target_price', () => {
        const configs: ProductWithConfig[] = [
          { id: '1', name: 'Rum', emoji: '🍾', quantity: 5, quality: 'medium', target_price: 10 },
          { id: '2', name: 'Map', emoji: '🗺️', quantity: 2, quality: 'high' },
        ];

        const total = calculateTotalTargetValue(configs);

        expect(total).toBe(50); // Only first item counts
      });

      it('should return 0 for empty array', () => {
        const total = calculateTotalTargetValue([]);

        expect(total).toBe(0);
      });
    });

    describe('filterConfigsByQuality', () => {
      const configs: ProductWithConfig[] = [
        { id: '1', name: 'Rum', emoji: '🍾', quantity: 5, quality: 'low' },
        { id: '2', name: 'Map', emoji: '🗺️', quantity: 2, quality: 'high' },
        { id: '3', name: 'Sword', emoji: '⚔️', quantity: 3, quality: 'medium' },
        { id: '4', name: 'Compass', emoji: '🧭', quantity: 1, quality: 'high' },
      ];

      it('should filter by low quality', () => {
        const filtered = filterConfigsByQuality(configs, 'low');

        expect(filtered).toHaveLength(1);
        expect(filtered[0].name).toBe('Rum');
      });

      it('should filter by medium quality', () => {
        const filtered = filterConfigsByQuality(configs, 'medium');

        expect(filtered).toHaveLength(1);
        expect(filtered[0].name).toBe('Sword');
      });

      it('should filter by high quality', () => {
        const filtered = filterConfigsByQuality(configs, 'high');

        expect(filtered).toHaveLength(2);
        expect(filtered[0].name).toBe('Map');
        expect(filtered[1].name).toBe('Compass');
      });
    });

    describe('groupConfigsByQuality', () => {
      it('should group configs by quality', () => {
        const configs: ProductWithConfig[] = [
          { id: '1', name: 'Rum', emoji: '🍾', quantity: 5, quality: 'low' },
          { id: '2', name: 'Map', emoji: '🗺️', quantity: 2, quality: 'high' },
          { id: '3', name: 'Sword', emoji: '⚔️', quantity: 3, quality: 'medium' },
          { id: '4', name: 'Compass', emoji: '🧭', quantity: 1, quality: 'high' },
        ];

        const grouped = groupConfigsByQuality(configs);

        expect(grouped.low).toHaveLength(1);
        expect(grouped.medium).toHaveLength(1);
        expect(grouped.high).toHaveLength(2);
        expect(grouped.low[0].name).toBe('Rum');
        expect(grouped.medium[0].name).toBe('Sword');
        expect(grouped.high[0].name).toBe('Map');
      });

      it('should handle empty arrays for missing qualities', () => {
        const configs: ProductWithConfig[] = [
          { id: '1', name: 'Rum', emoji: '🍾', quantity: 5, quality: 'high' },
        ];

        const grouped = groupConfigsByQuality(configs);

        expect(grouped.low).toEqual([]);
        expect(grouped.medium).toEqual([]);
        expect(grouped.high).toHaveLength(1);
      });
    });
  });
});
