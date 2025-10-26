/**
 * Product Transform Utilities
 *
 * Centralized data transformation functions for products.
 * These pure functions ensure consistent product data handling
 * across the application.
 */

import { Product } from '@/types/expedition';

/**
 * Product selection state type
 */
export type ProductSelectionState = Record<string, boolean>;

/**
 * Product with quantity and quality
 */
export interface ProductWithConfig {
  id: number;
  name: string;
  emoji?: string;
  quantity: number;
  quality: string;
  target_price?: number;
}

/**
 * Transforms product array to selection state
 *
 * @param products - Array of products
 * @param initiallySelected - Whether products should be initially selected
 * @returns Selection state object
 */
export const toSelectionState = (
  products: Product[],
  initiallySelected = false
): ProductSelectionState => {
  return products.reduce((acc, product) => {
    acc[product.id] = initiallySelected;
    return acc;
  }, {} as ProductSelectionState);
};

/**
 * Gets selected products from selection state
 *
 * @param products - Array of all products
 * @param selectionState - Selection state object
 * @returns Array of selected products
 */
export const getSelectedProducts = (
  products: Product[],
  selectionState: ProductSelectionState
): Product[] => {
  return products.filter(product => selectionState[product.id]);
};

/**
 * Gets selected product IDs
 *
 * @param selectionState - Selection state object
 * @returns Array of selected product IDs
 */
export const getSelectedProductIds = (selectionState: ProductSelectionState): string[] => {
  return Object.entries(selectionState)
    .filter(([, selected]) => selected)
    .map(([id]) => id);
};

/**
 * Counts selected products
 *
 * @param selectionState - Selection state object
 * @returns Number of selected products
 */
export const countSelectedProducts = (selectionState: ProductSelectionState): number => {
  return Object.values(selectionState).filter(Boolean).length;
};

/**
 * Checks if any products are selected
 *
 * @param selectionState - Selection state object
 * @returns true if at least one product is selected
 */
export const hasSelectedProducts = (selectionState: ProductSelectionState): boolean => {
  return Object.values(selectionState).some(Boolean);
};

/**
 * Toggles product selection
 *
 * @param selectionState - Current selection state
 * @param productId - Product ID to toggle
 * @returns New selection state
 */
export const toggleProductSelection = (
  selectionState: ProductSelectionState,
  productId: string
): ProductSelectionState => {
  return {
    ...selectionState,
    [productId]: !selectionState[productId],
  };
};

/**
 * Selects all products
 *
 * @param products - Array of products
 * @returns Selection state with all products selected
 */
export const selectAllProducts = (products: Product[]): ProductSelectionState => {
  return toSelectionState(products, true);
};

/**
 * Deselects all products
 *
 * @param products - Array of products
 * @returns Selection state with no products selected
 */
export const deselectAllProducts = (products: Product[]): ProductSelectionState => {
  return toSelectionState(products, false);
};

/**
 * Filters products by search query
 *
 * Searches in name and emoji
 *
 * @param products - Array of products
 * @param query - Search query
 * @returns Filtered products
 */
export const filterProductsBySearch = (products: Product[], query: string): Product[] => {
  const lowerQuery = query.toLowerCase().trim();

  if (!lowerQuery) return products;

  return products.filter(product =>
    product.name.toLowerCase().includes(lowerQuery) ||
    (product.emoji && product.emoji.includes(lowerQuery))
  );
};

/**
 * Filters products by availability
 *
 * @param products - Array of products
 * @param availableOnly - If true, only return products with stock > 0
 * @returns Filtered products
 */
export const filterProductsByAvailability = (
  products: Product[],
  availableOnly: boolean
): Product[] => {
  if (!availableOnly) return products;

  return products.filter(product =>
    product.stock !== undefined && product.stock > 0
  );
};

/**
 * Sorts products by name
 *
 * @param products - Array of products
 * @param ascending - Sort direction
 * @returns Sorted products
 */
export const sortProductsByName = (products: Product[], ascending = true): Product[] => {
  return [...products].sort((a, b) => {
    const comparison = a.name.localeCompare(b.name);
    return ascending ? comparison : -comparison;
  });
};

/**
 * Sorts products by stock
 *
 * @param products - Array of products
 * @param ascending - Sort direction (ascending = low to high)
 * @returns Sorted products
 */
export const sortProductsByStock = (products: Product[], ascending = false): Product[] => {
  return [...products].sort((a, b) => {
    const aStock = a.stock || 0;
    const bStock = b.stock || 0;
    const comparison = aStock - bStock;
    return ascending ? comparison : -comparison;
  });
};

/**
 * Groups products by availability
 *
 * @param products - Array of products
 * @returns Object with available and unavailable products
 */
export const groupProductsByAvailability = (products: Product[]): {
  available: Product[];
  unavailable: Product[];
} => {
  return {
    available: products.filter(p => p.stock !== undefined && p.stock > 0),
    unavailable: products.filter(p => !p.stock || p.stock === 0),
  };
};

/**
 * Creates product configuration with defaults
 *
 * @param product - Base product
 * @param quantity - Default quantity
 * @param quality - Default quality
 * @param targetPrice - Optional target price
 * @returns Product with configuration
 */
export const toProductWithConfig = (
  product: Product,
  quantity = 1,
  quality = 'medium',
  targetPrice?: number
): ProductWithConfig => {
  return {
    id: product.id,
    name: product.name,
    emoji: product.emoji,
    quantity,
    quality,
    target_price: targetPrice,
  };
};

/**
 * Validates product configuration
 *
 * @param config - Product configuration
 * @returns Validation errors or null if valid
 */
export const validateProductConfig = (
  config: ProductWithConfig
): { quantity?: string; quality?: string; targetPrice?: string } | null => {
  const errors: { quantity?: string; quality?: string; targetPrice?: string } = {};

  if (config.quantity <= 0) {
    errors.quantity = 'Quantity must be greater than 0';
  }

  if (!['low', 'medium', 'high'].includes(config.quality)) {
    errors.quality = 'Quality must be low, medium, or high';
  }

  if (config.target_price !== undefined && config.target_price <= 0) {
    errors.targetPrice = 'Target price must be greater than 0';
  }

  return Object.keys(errors).length > 0 ? errors : null;
};

/**
 * Calculates total target value for product configurations
 *
 * @param configs - Array of product configurations
 * @returns Total target value
 */
export const calculateTotalTargetValue = (configs: ProductWithConfig[]): number => {
  return configs.reduce((total, config) => {
    const itemValue = (config.target_price || 0) * config.quantity;
    return total + itemValue;
  }, 0);
};

/**
 * Filters product configs by quality
 *
 * @param configs - Array of product configurations
 * @param quality - Quality filter
 * @returns Filtered configurations
 */
export const filterConfigsByQuality = (
  configs: ProductWithConfig[],
  quality: 'low' | 'medium' | 'high'
): ProductWithConfig[] => {
  return configs.filter(config => config.quality === quality);
};

/**
 * Groups configs by quality
 *
 * @param configs - Array of product configurations
 * @returns Object with configs grouped by quality
 */
export const groupConfigsByQuality = (configs: ProductWithConfig[]): {
  low: ProductWithConfig[];
  medium: ProductWithConfig[];
  high: ProductWithConfig[];
} => {
  return {
    low: filterConfigsByQuality(configs, 'low'),
    medium: filterConfigsByQuality(configs, 'medium'),
    high: filterConfigsByQuality(configs, 'high'),
  };
};
