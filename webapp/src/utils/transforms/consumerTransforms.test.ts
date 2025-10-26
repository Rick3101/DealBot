/**
 * Consumer Transform Utilities Tests
 *
 * Comprehensive test suite for consumption aggregation and pirate statistics
 */

import { describe, it, expect } from 'vitest';
import {
  aggregateByPirate,
  aggregateByProduct,
  getTopConsumersByItems,
  getTopConsumersByCost,
  getMostConsumedProducts,
  filterByDateRange,
  filterByPirate,
  filterByProduct,
  calculateConsumptionStats,
  sortByDate,
  groupByDate,
  getDailyTotals,
  getMostDiverseConsumer,
  calculateConsumptionVelocity,
  ItemConsumption,
  PirateConsumptionSummary,
  ProductConsumptionSummary,
} from './consumerTransforms';

// Mock consumption data
const mockConsumptions: ItemConsumption[] = [
  {
    id: '1',
    expedition_id: 'exp1',
    pirate_name: 'Captain Hook',
    product_name: 'Rum',
    product_emoji: '🍾',
    quantity: 5,
    consumed_at: '2025-01-15T10:00:00Z',
    cost: 50,
  },
  {
    id: '2',
    expedition_id: 'exp1',
    pirate_name: 'Blackbeard',
    product_name: 'Rum',
    product_emoji: '🍾',
    quantity: 3,
    consumed_at: '2025-01-15T11:00:00Z',
    cost: 30,
  },
  {
    id: '3',
    expedition_id: 'exp1',
    pirate_name: 'Captain Hook',
    product_name: 'Treasure Map',
    product_emoji: '🗺️',
    quantity: 1,
    consumed_at: '2025-01-16T10:00:00Z',
    cost: 100,
  },
  {
    id: '4',
    expedition_id: 'exp1',
    pirate_name: 'Captain Hook',
    product_name: 'Rum',
    product_emoji: '🍾',
    quantity: 2,
    consumed_at: '2025-01-17T10:00:00Z',
    cost: 20,
  },
  {
    id: '5',
    expedition_id: 'exp1',
    pirate_name: 'Anne Bonny',
    product_name: 'Sword',
    product_emoji: '⚔️',
    quantity: 1,
    consumed_at: '2025-01-17T12:00:00Z',
    cost: 75,
  },
];

describe('consumerTransforms', () => {
  describe('Aggregation', () => {
    describe('aggregateByPirate', () => {
      it('should aggregate consumptions by pirate', () => {
        const aggregated = aggregateByPirate(mockConsumptions);

        expect(aggregated).toHaveLength(3);

        const hook = aggregated.find(p => p.pirate_name === 'Captain Hook');
        expect(hook).toBeDefined();
        expect(hook!.total_items).toBe(8); // 5 + 1 + 2
        expect(hook!.total_cost).toBe(170); // 50 + 100 + 20
        expect(hook!.consumption_count).toBe(3);
        expect(hook!.items).toHaveLength(2); // Rum and Treasure Map
      });

      it('should track first and last consumption dates', () => {
        const aggregated = aggregateByPirate(mockConsumptions);
        const hook = aggregated.find(p => p.pirate_name === 'Captain Hook');

        expect(hook!.first_consumption).toBe('2025-01-15T10:00:00Z');
        expect(hook!.last_consumption).toBe('2025-01-17T10:00:00Z');
      });

      it('should aggregate product items correctly', () => {
        const aggregated = aggregateByPirate(mockConsumptions);
        const hook = aggregated.find(p => p.pirate_name === 'Captain Hook');

        const rumItem = hook!.items.find(i => i.product_name === 'Rum');
        expect(rumItem!.quantity).toBe(7); // 5 + 2
        expect(rumItem!.cost).toBe(70); // 50 + 20

        const mapItem = hook!.items.find(i => i.product_name === 'Treasure Map');
        expect(mapItem!.quantity).toBe(1);
        expect(mapItem!.cost).toBe(100);
      });

      it('should handle single consumption per pirate', () => {
        const singleConsumption = [mockConsumptions[4]]; // Anne Bonny
        const aggregated = aggregateByPirate(singleConsumption);

        expect(aggregated).toHaveLength(1);
        expect(aggregated[0].pirate_name).toBe('Anne Bonny');
        expect(aggregated[0].total_items).toBe(1);
        expect(aggregated[0].consumption_count).toBe(1);
      });

      it('should handle empty consumptions array', () => {
        const aggregated = aggregateByPirate([]);

        expect(aggregated).toEqual([]);
      });

      it('should handle consumptions without cost', () => {
        const noCostConsumptions: ItemConsumption[] = [
          {
            id: '1',
            expedition_id: 'exp1',
            pirate_name: 'Captain Hook',
            product_name: 'Rum',
            product_emoji: '🍾',
            quantity: 5,
            consumed_at: '2025-01-15T10:00:00Z',
          },
        ];

        const aggregated = aggregateByPirate(noCostConsumptions);

        expect(aggregated[0].total_cost).toBe(0);
      });
    });

    describe('aggregateByProduct', () => {
      it('should aggregate consumptions by product', () => {
        const aggregated = aggregateByProduct(mockConsumptions);

        expect(aggregated).toHaveLength(3); // Rum, Treasure Map, Sword

        const rum = aggregated.find(p => p.product_name === 'Rum');
        expect(rum).toBeDefined();
        expect(rum!.total_quantity).toBe(10); // 5 + 3 + 2
        expect(rum!.total_cost).toBe(100); // 50 + 30 + 20
        expect(rum!.unique_consumers).toBe(2); // Captain Hook and Blackbeard
      });

      it('should track consumers correctly', () => {
        const aggregated = aggregateByProduct(mockConsumptions);
        const rum = aggregated.find(p => p.product_name === 'Rum');

        expect(rum!.consumed_by).toHaveLength(2);

        const hookConsumption = rum!.consumed_by.find(c => c.pirate_name === 'Captain Hook');
        expect(hookConsumption!.quantity).toBe(7); // 5 + 2
        expect(hookConsumption!.cost).toBe(70); // 50 + 20

        const blackbeardConsumption = rum!.consumed_by.find(c => c.pirate_name === 'Blackbeard');
        expect(blackbeardConsumption!.quantity).toBe(3);
        expect(blackbeardConsumption!.cost).toBe(30);
      });

      it('should handle single product consumption', () => {
        const singleConsumption = [mockConsumptions[2]]; // Treasure Map
        const aggregated = aggregateByProduct(singleConsumption);

        expect(aggregated).toHaveLength(1);
        expect(aggregated[0].product_name).toBe('Treasure Map');
        expect(aggregated[0].unique_consumers).toBe(1);
      });

      it('should handle empty consumptions array', () => {
        const aggregated = aggregateByProduct([]);

        expect(aggregated).toEqual([]);
      });
    });
  });

  describe('Top Consumers', () => {
    describe('getTopConsumersByItems', () => {
      it('should return top consumers sorted by total items', () => {
        const summaries: PirateConsumptionSummary[] = [
          {
            pirate_name: 'Captain Hook',
            total_items: 10,
            total_cost: 100,
            items: [],
            first_consumption: '2025-01-15T10:00:00Z',
            last_consumption: '2025-01-17T10:00:00Z',
            consumption_count: 3,
          },
          {
            pirate_name: 'Blackbeard',
            total_items: 5,
            total_cost: 50,
            items: [],
            first_consumption: '2025-01-15T11:00:00Z',
            last_consumption: '2025-01-15T11:00:00Z',
            consumption_count: 1,
          },
          {
            pirate_name: 'Anne Bonny',
            total_items: 15,
            total_cost: 150,
            items: [],
            first_consumption: '2025-01-14T10:00:00Z',
            last_consumption: '2025-01-18T10:00:00Z',
            consumption_count: 5,
          },
        ];

        const top = getTopConsumersByItems(summaries, 2);

        expect(top).toHaveLength(2);
        expect(top[0].pirate_name).toBe('Anne Bonny'); // 15 items
        expect(top[1].pirate_name).toBe('Captain Hook'); // 10 items
      });

      it('should respect limit parameter', () => {
        const summaries = aggregateByPirate(mockConsumptions);
        const top = getTopConsumersByItems(summaries, 1);

        expect(top).toHaveLength(1);
      });

      it('should not mutate original array', () => {
        const summaries = aggregateByPirate(mockConsumptions);
        const original = [...summaries];

        getTopConsumersByItems(summaries, 2);

        expect(summaries).toEqual(original);
      });
    });

    describe('getTopConsumersByCost', () => {
      it('should return top consumers sorted by total cost', () => {
        const summaries: PirateConsumptionSummary[] = [
          {
            pirate_name: 'Captain Hook',
            total_items: 10,
            total_cost: 200,
            items: [],
            first_consumption: '2025-01-15T10:00:00Z',
            last_consumption: '2025-01-17T10:00:00Z',
            consumption_count: 3,
          },
          {
            pirate_name: 'Blackbeard',
            total_items: 15,
            total_cost: 100,
            items: [],
            first_consumption: '2025-01-15T11:00:00Z',
            last_consumption: '2025-01-15T11:00:00Z',
            consumption_count: 1,
          },
          {
            pirate_name: 'Anne Bonny',
            total_items: 5,
            total_cost: 300,
            items: [],
            first_consumption: '2025-01-14T10:00:00Z',
            last_consumption: '2025-01-18T10:00:00Z',
            consumption_count: 5,
          },
        ];

        const top = getTopConsumersByCost(summaries, 2);

        expect(top).toHaveLength(2);
        expect(top[0].pirate_name).toBe('Anne Bonny'); // 300 cost
        expect(top[1].pirate_name).toBe('Captain Hook'); // 200 cost
      });

      it('should use default limit of 5', () => {
        const summaries = aggregateByPirate(mockConsumptions);
        const top = getTopConsumersByCost(summaries);

        expect(top.length).toBeLessThanOrEqual(5);
      });
    });

    describe('getMostConsumedProducts', () => {
      it('should return most consumed products by quantity', () => {
        const summaries: ProductConsumptionSummary[] = [
          {
            product_name: 'Rum',
            product_emoji: '🍾',
            total_quantity: 20,
            total_cost: 200,
            consumed_by: [],
            unique_consumers: 3,
          },
          {
            product_name: 'Sword',
            product_emoji: '⚔️',
            total_quantity: 5,
            total_cost: 375,
            consumed_by: [],
            unique_consumers: 2,
          },
          {
            product_name: 'Treasure Map',
            product_emoji: '🗺️',
            total_quantity: 10,
            total_cost: 1000,
            consumed_by: [],
            unique_consumers: 5,
          },
        ];

        const mostConsumed = getMostConsumedProducts(summaries, 2);

        expect(mostConsumed).toHaveLength(2);
        expect(mostConsumed[0].product_name).toBe('Rum'); // 20 quantity
        expect(mostConsumed[1].product_name).toBe('Treasure Map'); // 10 quantity
      });

      it('should respect limit parameter', () => {
        const summaries = aggregateByProduct(mockConsumptions);
        const mostConsumed = getMostConsumedProducts(summaries, 1);

        expect(mostConsumed).toHaveLength(1);
      });
    });
  });

  describe('Filtering', () => {
    describe('filterByDateRange', () => {
      it('should filter consumptions within date range', () => {
        const startDate = '2025-01-15T00:00:00Z';
        const endDate = '2025-01-16T23:59:59Z';

        const filtered = filterByDateRange(mockConsumptions, startDate, endDate);

        expect(filtered).toHaveLength(3); // IDs 1, 2, 3
        expect(filtered.every(c => {
          const time = new Date(c.consumed_at).getTime();
          return time >= new Date(startDate).getTime() && time <= new Date(endDate).getTime();
        })).toBe(true);
      });

      it('should include consumptions on boundary dates', () => {
        const startDate = '2025-01-15T10:00:00Z';
        const endDate = '2025-01-15T11:00:00Z';

        const filtered = filterByDateRange(mockConsumptions, startDate, endDate);

        expect(filtered).toHaveLength(2); // IDs 1 and 2
      });

      it('should return empty array when no consumptions in range', () => {
        const startDate = '2025-01-01T00:00:00Z';
        const endDate = '2025-01-10T00:00:00Z';

        const filtered = filterByDateRange(mockConsumptions, startDate, endDate);

        expect(filtered).toEqual([]);
      });
    });

    describe('filterByPirate', () => {
      it('should filter consumptions by pirate name', () => {
        const filtered = filterByPirate(mockConsumptions, 'Captain Hook');

        expect(filtered).toHaveLength(3); // IDs 1, 3, 4
        expect(filtered.every(c => c.pirate_name === 'Captain Hook')).toBe(true);
      });

      it('should return empty array when pirate not found', () => {
        const filtered = filterByPirate(mockConsumptions, 'Unknown Pirate');

        expect(filtered).toEqual([]);
      });
    });

    describe('filterByProduct', () => {
      it('should filter consumptions by product name', () => {
        const filtered = filterByProduct(mockConsumptions, 'Rum');

        expect(filtered).toHaveLength(3); // IDs 1, 2, 4
        expect(filtered.every(c => c.product_name === 'Rum')).toBe(true);
      });

      it('should return empty array when product not found', () => {
        const filtered = filterByProduct(mockConsumptions, 'Unknown Product');

        expect(filtered).toEqual([]);
      });
    });
  });

  describe('Statistics', () => {
    describe('calculateConsumptionStats', () => {
      it('should calculate comprehensive statistics', () => {
        const stats = calculateConsumptionStats(mockConsumptions);

        expect(stats.total_consumptions).toBe(5);
        expect(stats.total_items).toBe(12); // 5 + 3 + 1 + 2 + 1
        expect(stats.total_cost).toBe(275); // 50 + 30 + 100 + 20 + 75
        expect(stats.unique_pirates).toBe(3); // Captain Hook, Blackbeard, Anne Bonny
        expect(stats.unique_products).toBe(3); // Rum, Treasure Map, Sword
        expect(stats.average_items_per_consumption).toBe(12 / 5);
        expect(stats.average_cost_per_consumption).toBe(275 / 5);
      });

      it('should handle empty consumptions array', () => {
        const stats = calculateConsumptionStats([]);

        expect(stats.total_consumptions).toBe(0);
        expect(stats.total_items).toBe(0);
        expect(stats.total_cost).toBe(0);
        expect(stats.unique_pirates).toBe(0);
        expect(stats.unique_products).toBe(0);
        expect(stats.average_items_per_consumption).toBe(0);
        expect(stats.average_cost_per_consumption).toBe(0);
      });

      it('should handle consumptions without cost', () => {
        const noCostConsumptions: ItemConsumption[] = mockConsumptions.map(c => ({
          ...c,
          cost: undefined,
        }));

        const stats = calculateConsumptionStats(noCostConsumptions);

        expect(stats.total_cost).toBe(0);
        expect(stats.average_cost_per_consumption).toBe(0);
      });
    });
  });

  describe('Sorting and Grouping', () => {
    describe('sortByDate', () => {
      it('should sort consumptions by date descending (default)', () => {
        const sorted = sortByDate(mockConsumptions);

        expect(sorted[0].id).toBe('5'); // 2025-01-17T12:00:00Z
        expect(sorted[sorted.length - 1].id).toBe('1'); // 2025-01-15T10:00:00Z
      });

      it('should sort consumptions by date ascending', () => {
        const sorted = sortByDate(mockConsumptions, true);

        expect(sorted[0].id).toBe('1'); // 2025-01-15T10:00:00Z
        expect(sorted[sorted.length - 1].id).toBe('5'); // 2025-01-17T12:00:00Z
      });

      it('should not mutate original array', () => {
        const original = [...mockConsumptions];
        sortByDate(mockConsumptions);

        expect(mockConsumptions).toEqual(original);
      });
    });

    describe('groupByDate', () => {
      it('should group consumptions by date (YYYY-MM-DD)', () => {
        const grouped = groupByDate(mockConsumptions);

        expect(grouped['2025-01-15']).toHaveLength(2); // IDs 1, 2
        expect(grouped['2025-01-16']).toHaveLength(1); // ID 3
        expect(grouped['2025-01-17']).toHaveLength(2); // IDs 4, 5
      });

      it('should handle empty consumptions array', () => {
        const grouped = groupByDate([]);

        expect(grouped).toEqual({});
      });

      it('should extract date correctly from ISO timestamp', () => {
        const grouped = groupByDate(mockConsumptions);
        const dates = Object.keys(grouped);

        expect(dates.every(date => /^\d{4}-\d{2}-\d{2}$/.test(date))).toBe(true);
      });
    });

    describe('getDailyTotals', () => {
      it('should calculate daily totals', () => {
        const dailyTotals = getDailyTotals(mockConsumptions);

        expect(dailyTotals).toHaveLength(3);

        const jan15 = dailyTotals.find(d => d.date === '2025-01-15');
        expect(jan15).toBeDefined();
        expect(jan15!.total_items).toBe(8); // 5 + 3
        expect(jan15!.total_cost).toBe(80); // 50 + 30
        expect(jan15!.consumption_count).toBe(2);
      });

      it('should sort daily totals by date ascending', () => {
        const dailyTotals = getDailyTotals(mockConsumptions);

        expect(dailyTotals[0].date).toBe('2025-01-15');
        expect(dailyTotals[dailyTotals.length - 1].date).toBe('2025-01-17');
      });

      it('should handle empty consumptions array', () => {
        const dailyTotals = getDailyTotals([]);

        expect(dailyTotals).toEqual([]);
      });

      it('should handle consumptions without cost', () => {
        const noCostConsumptions: ItemConsumption[] = mockConsumptions.map(c => ({
          ...c,
          cost: undefined,
        }));

        const dailyTotals = getDailyTotals(noCostConsumptions);

        expect(dailyTotals.every(d => d.total_cost === 0)).toBe(true);
      });
    });
  });

  describe('Advanced Analytics', () => {
    describe('getMostDiverseConsumer', () => {
      it('should find pirate with most different products', () => {
        const summaries: PirateConsumptionSummary[] = [
          {
            pirate_name: 'Captain Hook',
            total_items: 10,
            total_cost: 200,
            items: [
              { product_name: 'Rum', product_emoji: '🍾', quantity: 5, cost: 50 },
              { product_name: 'Sword', product_emoji: '⚔️', quantity: 3, cost: 75 },
              { product_name: 'Map', product_emoji: '🗺️', quantity: 2, cost: 75 },
            ],
            first_consumption: '2025-01-15T10:00:00Z',
            last_consumption: '2025-01-17T10:00:00Z',
            consumption_count: 3,
          },
          {
            pirate_name: 'Blackbeard',
            total_items: 15,
            total_cost: 300,
            items: [
              { product_name: 'Rum', product_emoji: '🍾', quantity: 15, cost: 300 },
            ],
            first_consumption: '2025-01-15T11:00:00Z',
            last_consumption: '2025-01-15T11:00:00Z',
            consumption_count: 1,
          },
        ];

        const mostDiverse = getMostDiverseConsumer(summaries);

        expect(mostDiverse).not.toBeNull();
        expect(mostDiverse!.pirate_name).toBe('Captain Hook'); // 3 different products
      });

      it('should return null for empty array', () => {
        const mostDiverse = getMostDiverseConsumer([]);

        expect(mostDiverse).toBeNull();
      });

      it('should handle single summary', () => {
        const summaries = aggregateByPirate([mockConsumptions[0]]);
        const mostDiverse = getMostDiverseConsumer(summaries);

        expect(mostDiverse).not.toBeNull();
        expect(mostDiverse!.pirate_name).toBe('Captain Hook');
      });
    });

    describe('calculateConsumptionVelocity', () => {
      it('should calculate items per day', () => {
        // Consumptions span from 2025-01-15 to 2025-01-17 (3 days)
        // Total items: 12
        // Velocity: 12 / 3 = 4 items/day
        const velocity = calculateConsumptionVelocity(mockConsumptions);

        // Days: Jan 15 to Jan 17 = 2 days difference, but Math.ceil makes it 2
        // Actually: 2025-01-15T10:00:00Z to 2025-01-17T12:00:00Z
        // = ~2.08 days, ceil = 3 days
        expect(velocity).toBeCloseTo(4, 1); // 12 items / 3 days
      });

      it('should return 0 for empty consumptions', () => {
        const velocity = calculateConsumptionVelocity([]);

        expect(velocity).toBe(0);
      });

      it('should handle single day consumption', () => {
        const singleDayConsumptions = mockConsumptions.slice(0, 2); // Both on Jan 15
        const velocity = calculateConsumptionVelocity(singleDayConsumptions);

        // Same day, daysDiff = 1 (min value), total items = 8
        expect(velocity).toBe(8);
      });

      it('should handle consumptions across many days', () => {
        const spreadConsumptions: ItemConsumption[] = [
          {
            id: '1',
            expedition_id: 'exp1',
            pirate_name: 'Captain Hook',
            product_name: 'Rum',
            product_emoji: '🍾',
            quantity: 10,
            consumed_at: '2025-01-01T10:00:00Z',
            cost: 100,
          },
          {
            id: '2',
            expedition_id: 'exp1',
            pirate_name: 'Blackbeard',
            product_name: 'Rum',
            product_emoji: '🍾',
            quantity: 10,
            consumed_at: '2025-01-11T10:00:00Z',
            cost: 100,
          },
        ];

        const velocity = calculateConsumptionVelocity(spreadConsumptions);

        // 10 days, 20 items = 2 items/day
        expect(velocity).toBe(2);
      });
    });
  });
});
