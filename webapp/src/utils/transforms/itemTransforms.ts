import { ExpeditionItem, QualityGrade } from '@/types/expedition';

/**
 * Transformed item interface with standardized field names
 * Provides a consistent structure for UI components
 */
export interface TransformedItem {
  id: number;
  product_id: number;
  name: string;
  emoji: string;
  quantity: number;
  price: number;
  quality?: QualityGrade;
  consumed: number;
  available: number;
}

/**
 * Transforms expedition items from backend format to standardized UI format
 *
 * Handles field name variations:
 * - consumed/quantity_consumed
 * - quantity/quantity_needed
 * - price/unit_price
 *
 * Calculates available quantity when not provided by backend
 * Provides safe defaults for missing fields
 *
 * @param items - Array of expedition items from backend
 * @returns Array of transformed items with consistent structure
 *
 * @example
 * const transformed = transformExpeditionItems(expeditionItems);
 * <ItemsGrid items={transformed} />
 */
export const transformExpeditionItems = (
  items: ExpeditionItem[]
): TransformedItem[] => {
  return items.map(item => {
    // Handle field name variations - backend may use different names
    // Use backend-provided values, with fallbacks for consistency
    const consumed = item.consumed ?? item.quantity_consumed ?? 0;
    const quantity = item.quantity ?? item.quantity_needed;
    const price = item.price ?? item.unit_price;

    // Calculate available quantity
    // Prefer backend-calculated value if available, otherwise calculate locally
    const available = item.available ?? Math.max(0, quantity - consumed);

    return {
      id: item.id,
      product_id: item.product_id,
      name: item.product_name,
      emoji: item.product_emoji || '',
      quantity,
      price,
      quality: item.quality_grade as QualityGrade | undefined,
      consumed,
      available,
    };
  });
};

/**
 * Filters items to show only those with available stock
 * Useful for consumption flows where only available items should be shown
 *
 * @param items - Array of transformed items
 * @returns Array of items with available > 0
 */
export const getAvailableItems = (items: TransformedItem[]): TransformedItem[] => {
  return items.filter(item => item.available > 0);
};

/**
 * Calculates total value of items (quantity * price)
 *
 * @param items - Array of transformed items
 * @returns Total value of all items
 */
export const calculateTotalValue = (items: TransformedItem[]): number => {
  return items.reduce((total, item) => total + (item.quantity * item.price), 0);
};

/**
 * Calculates consumed value (consumed * price)
 *
 * @param items - Array of transformed items
 * @returns Total value of consumed items
 */
export const calculateConsumedValue = (items: TransformedItem[]): number => {
  return items.reduce((total, item) => total + (item.consumed * item.price), 0);
};

/**
 * Groups items by quality grade
 *
 * @param items - Array of transformed items
 * @returns Map of quality grade to items
 */
export const groupItemsByQuality = (
  items: TransformedItem[]
): Map<QualityGrade | 'ungraded', TransformedItem[]> => {
  const groups = new Map<QualityGrade | 'ungraded', TransformedItem[]>();

  items.forEach(item => {
    const key = item.quality || 'ungraded';
    const group = groups.get(key) || [];
    group.push(item);
    groups.set(key, group);
  });

  return groups;
};
