/**
 * Consumer (Pirate) Transform Utilities
 *
 * Centralized data transformation functions for expedition consumers/pirates.
 * These pure functions handle consumption aggregation and pirate statistics.
 */

/**
 * Item consumption record
 */
export interface ItemConsumption {
  id: string;
  expedition_id: string;
  pirate_name: string;
  product_name: string;
  product_emoji: string;
  quantity: number;
  consumed_at: string;
  cost?: number;
}

/**
 * Pirate consumption summary
 */
export interface PirateConsumptionSummary {
  pirate_name: string;
  total_items: number;
  total_cost: number;
  items: {
    product_name: string;
    product_emoji: string;
    quantity: number;
    cost: number;
  }[];
  first_consumption: string;
  last_consumption: string;
  consumption_count: number;
}

/**
 * Product consumption summary
 */
export interface ProductConsumptionSummary {
  product_name: string;
  product_emoji: string;
  total_quantity: number;
  total_cost: number;
  consumed_by: {
    pirate_name: string;
    quantity: number;
    cost: number;
  }[];
  unique_consumers: number;
}

/**
 * Aggregates consumptions by pirate
 *
 * @param consumptions - Array of consumption records
 * @returns Array of pirate summaries
 */
export const aggregateByPirate = (
  consumptions: ItemConsumption[]
): PirateConsumptionSummary[] => {
  const pirateMap = new Map<string, PirateConsumptionSummary>();

  consumptions.forEach(consumption => {
    const existing = pirateMap.get(consumption.pirate_name);

    if (!existing) {
      pirateMap.set(consumption.pirate_name, {
        pirate_name: consumption.pirate_name,
        total_items: consumption.quantity,
        total_cost: consumption.cost || 0,
        items: [{
          product_name: consumption.product_name,
          product_emoji: consumption.product_emoji,
          quantity: consumption.quantity,
          cost: consumption.cost || 0,
        }],
        first_consumption: consumption.consumed_at,
        last_consumption: consumption.consumed_at,
        consumption_count: 1,
      });
    } else {
      existing.total_items += consumption.quantity;
      existing.total_cost += consumption.cost || 0;
      existing.consumption_count += 1;

      // Update time range
      if (consumption.consumed_at < existing.first_consumption) {
        existing.first_consumption = consumption.consumed_at;
      }
      if (consumption.consumed_at > existing.last_consumption) {
        existing.last_consumption = consumption.consumed_at;
      }

      // Add or update product item
      const existingItem = existing.items.find(
        item => item.product_name === consumption.product_name
      );

      if (existingItem) {
        existingItem.quantity += consumption.quantity;
        existingItem.cost += consumption.cost || 0;
      } else {
        existing.items.push({
          product_name: consumption.product_name,
          product_emoji: consumption.product_emoji,
          quantity: consumption.quantity,
          cost: consumption.cost || 0,
        });
      }
    }
  });

  return Array.from(pirateMap.values());
};

/**
 * Aggregates consumptions by product
 *
 * @param consumptions - Array of consumption records
 * @returns Array of product summaries
 */
export const aggregateByProduct = (
  consumptions: ItemConsumption[]
): ProductConsumptionSummary[] => {
  const productMap = new Map<string, ProductConsumptionSummary>();

  consumptions.forEach(consumption => {
    const existing = productMap.get(consumption.product_name);

    if (!existing) {
      productMap.set(consumption.product_name, {
        product_name: consumption.product_name,
        product_emoji: consumption.product_emoji,
        total_quantity: consumption.quantity,
        total_cost: consumption.cost || 0,
        consumed_by: [{
          pirate_name: consumption.pirate_name,
          quantity: consumption.quantity,
          cost: consumption.cost || 0,
        }],
        unique_consumers: 1,
      });
    } else {
      existing.total_quantity += consumption.quantity;
      existing.total_cost += consumption.cost || 0;

      // Add or update consumer
      const existingConsumer = existing.consumed_by.find(
        c => c.pirate_name === consumption.pirate_name
      );

      if (existingConsumer) {
        existingConsumer.quantity += consumption.quantity;
        existingConsumer.cost += consumption.cost || 0;
      } else {
        existing.consumed_by.push({
          pirate_name: consumption.pirate_name,
          quantity: consumption.quantity,
          cost: consumption.cost || 0,
        });
        existing.unique_consumers += 1;
      }
    }
  });

  return Array.from(productMap.values());
};

/**
 * Calculates top consumers by total items
 *
 * @param summaries - Array of pirate summaries
 * @param limit - Number of top consumers to return
 * @returns Top consumers sorted by total items
 */
export const getTopConsumersByItems = (
  summaries: PirateConsumptionSummary[],
  limit = 5
): PirateConsumptionSummary[] => {
  return [...summaries]
    .sort((a, b) => b.total_items - a.total_items)
    .slice(0, limit);
};

/**
 * Calculates top consumers by total cost
 *
 * @param summaries - Array of pirate summaries
 * @param limit - Number of top consumers to return
 * @returns Top consumers sorted by total cost
 */
export const getTopConsumersByCost = (
  summaries: PirateConsumptionSummary[],
  limit = 5
): PirateConsumptionSummary[] => {
  return [...summaries]
    .sort((a, b) => b.total_cost - a.total_cost)
    .slice(0, limit);
};

/**
 * Calculates most consumed products
 *
 * @param summaries - Array of product summaries
 * @param limit - Number of top products to return
 * @returns Top products sorted by total quantity
 */
export const getMostConsumedProducts = (
  summaries: ProductConsumptionSummary[],
  limit = 5
): ProductConsumptionSummary[] => {
  return [...summaries]
    .sort((a, b) => b.total_quantity - a.total_quantity)
    .slice(0, limit);
};

/**
 * Filters consumptions by date range
 *
 * @param consumptions - Array of consumption records
 * @param startDate - Start date (ISO string)
 * @param endDate - End date (ISO string)
 * @returns Filtered consumptions
 */
export const filterByDateRange = (
  consumptions: ItemConsumption[],
  startDate: string,
  endDate: string
): ItemConsumption[] => {
  const start = new Date(startDate).getTime();
  const end = new Date(endDate).getTime();

  return consumptions.filter(consumption => {
    const consumedAt = new Date(consumption.consumed_at).getTime();
    return consumedAt >= start && consumedAt <= end;
  });
};

/**
 * Filters consumptions by pirate name
 *
 * @param consumptions - Array of consumption records
 * @param pirateName - Pirate name to filter by
 * @returns Filtered consumptions
 */
export const filterByPirate = (
  consumptions: ItemConsumption[],
  pirateName: string
): ItemConsumption[] => {
  return consumptions.filter(c => c.pirate_name === pirateName);
};

/**
 * Filters consumptions by product
 *
 * @param consumptions - Array of consumption records
 * @param productName - Product name to filter by
 * @returns Filtered consumptions
 */
export const filterByProduct = (
  consumptions: ItemConsumption[],
  productName: string
): ItemConsumption[] => {
  return consumptions.filter(c => c.product_name === productName);
};

/**
 * Calculates consumption statistics
 *
 * @param consumptions - Array of consumption records
 * @returns Consumption statistics
 */
export const calculateConsumptionStats = (consumptions: ItemConsumption[]): {
  total_consumptions: number;
  total_items: number;
  total_cost: number;
  unique_pirates: number;
  unique_products: number;
  average_items_per_consumption: number;
  average_cost_per_consumption: number;
} => {
  const uniquePirates = new Set(consumptions.map(c => c.pirate_name)).size;
  const uniqueProducts = new Set(consumptions.map(c => c.product_name)).size;
  const totalItems = consumptions.reduce((sum, c) => sum + c.quantity, 0);
  const totalCost = consumptions.reduce((sum, c) => sum + (c.cost || 0), 0);

  return {
    total_consumptions: consumptions.length,
    total_items: totalItems,
    total_cost: totalCost,
    unique_pirates: uniquePirates,
    unique_products: uniqueProducts,
    average_items_per_consumption: consumptions.length > 0
      ? totalItems / consumptions.length
      : 0,
    average_cost_per_consumption: consumptions.length > 0
      ? totalCost / consumptions.length
      : 0,
  };
};

/**
 * Sorts consumptions by date
 *
 * @param consumptions - Array of consumption records
 * @param ascending - Sort direction (true = oldest first)
 * @returns Sorted consumptions
 */
export const sortByDate = (
  consumptions: ItemConsumption[],
  ascending = false
): ItemConsumption[] => {
  return [...consumptions].sort((a, b) => {
    const aTime = new Date(a.consumed_at).getTime();
    const bTime = new Date(b.consumed_at).getTime();
    return ascending ? aTime - bTime : bTime - aTime;
  });
};

/**
 * Groups consumptions by date
 *
 * @param consumptions - Array of consumption records
 * @returns Object with consumptions grouped by date (YYYY-MM-DD)
 */
export const groupByDate = (
  consumptions: ItemConsumption[]
): Record<string, ItemConsumption[]> => {
  const grouped: Record<string, ItemConsumption[]> = {};

  consumptions.forEach(consumption => {
    const date = consumption.consumed_at.split('T')[0]; // Get YYYY-MM-DD
    if (!grouped[date]) {
      grouped[date] = [];
    }
    grouped[date].push(consumption);
  });

  return grouped;
};

/**
 * Calculates daily consumption totals
 *
 * @param consumptions - Array of consumption records
 * @returns Array of daily totals
 */
export const getDailyTotals = (consumptions: ItemConsumption[]): {
  date: string;
  total_items: number;
  total_cost: number;
  consumption_count: number;
}[] => {
  const grouped = groupByDate(consumptions);

  return Object.entries(grouped).map(([date, items]) => ({
    date,
    total_items: items.reduce((sum, item) => sum + item.quantity, 0),
    total_cost: items.reduce((sum, item) => sum + (item.cost || 0), 0),
    consumption_count: items.length,
  })).sort((a, b) => a.date.localeCompare(b.date));
};

/**
 * Finds pirate with most diverse consumption
 *
 * (Most different products consumed)
 *
 * @param summaries - Array of pirate summaries
 * @returns Pirate with most diverse consumption or null
 */
export const getMostDiverseConsumer = (
  summaries: PirateConsumptionSummary[]
): PirateConsumptionSummary | null => {
  if (summaries.length === 0) return null;

  return summaries.reduce((most, current) =>
    current.items.length > most.items.length ? current : most
  );
};

/**
 * Calculates consumption velocity (items per day)
 *
 * @param consumptions - Array of consumption records
 * @returns Items per day
 */
export const calculateConsumptionVelocity = (
  consumptions: ItemConsumption[]
): number => {
  if (consumptions.length === 0) return 0;

  const sortedConsumptions = sortByDate(consumptions, true);
  const firstDate = new Date(sortedConsumptions[0].consumed_at);
  const lastDate = new Date(sortedConsumptions[sortedConsumptions.length - 1].consumed_at);

  const daysDiff = Math.max(1, Math.ceil(
    (lastDate.getTime() - firstDate.getTime()) / (1000 * 60 * 60 * 24)
  ));

  const totalItems = consumptions.reduce((sum, c) => sum + c.quantity, 0);

  return totalItems / daysDiff;
};
