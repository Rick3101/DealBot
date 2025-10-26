/**
 * Tests for Expedition Items Service
 *
 * Tests expedition items and consumption operations.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { expeditionItemsService, ExpeditionItemsService } from './expeditionItemsService';
import { httpClient } from './httpClient';

// Mock httpClient
vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('ExpeditionItemsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockItems = [
    {
      id: 1,
      product_id: 100,
      product_name: 'Test Product',
      target_price: 50,
      quantity: 10,
      consumed: 5,
    },
  ];

  const mockConsumption = {
    id: 1,
    expedition_id: 1,
    item_id: 1,
    consumer_name: 'Test Pirate',
    quantity: 2,
    price: 100,
    consumed_at: '2025-01-01T00:00:00Z',
  };

  describe('getItems', () => {
    it('should fetch expedition items', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { items: mockItems },
      } as any);

      const result = await expeditionItemsService.getItems(1);

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/1/items');
      expect(result).toEqual(mockItems);
    });

    it('should handle empty items list', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { items: [] },
      } as any);

      const result = await expeditionItemsService.getItems(1);

      expect(result).toEqual([]);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch items');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(expeditionItemsService.getItems(1)).rejects.toThrow('Failed to fetch items');
    });
  });

  describe('addItems', () => {
    const addItemsRequest = {
      items: [
        {
          product_id: 100,
          target_price: 50,
          quantity: 10,
        },
      ],
    };

    it('should add items to expedition', async () => {
      vi.mocked(httpClient.post).mockResolvedValue({
        data: { items: mockItems },
      } as any);

      const result = await expeditionItemsService.addItems(1, addItemsRequest);

      expect(httpClient.post).toHaveBeenCalledWith('/api/expeditions/1/items', addItemsRequest);
      expect(result).toEqual(mockItems);
    });

    it('should handle multiple items', async () => {
      const multipleItems = {
        items: [
          { product_id: 100, target_price: 50, quantity: 10 },
          { product_id: 101, target_price: 30, quantity: 5 },
        ],
      };

      vi.mocked(httpClient.post).mockResolvedValue({
        data: { items: mockItems },
      } as any);

      await expeditionItemsService.addItems(1, multipleItems);

      expect(httpClient.post).toHaveBeenCalledWith('/api/expeditions/1/items', multipleItems);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to add items');
      vi.mocked(httpClient.post).mockRejectedValue(error);

      await expect(expeditionItemsService.addItems(1, addItemsRequest)).rejects.toThrow(
        'Failed to add items'
      );
    });
  });

  describe('consumeItem', () => {
    const consumeRequest = {
      item_id: 1,
      consumer_name: 'Test Pirate',
      quantity: 2,
      price: 100,
    };

    it('should consume item from expedition', async () => {
      vi.mocked(httpClient.post).mockResolvedValue({
        data: mockConsumption,
      } as any);

      const result = await expeditionItemsService.consumeItem(1, consumeRequest);

      expect(httpClient.post).toHaveBeenCalledWith('/api/expeditions/1/consume', consumeRequest);
      expect(result).toEqual(mockConsumption);
    });

    it('should handle different quantities', async () => {
      const differentQuantity = { ...consumeRequest, quantity: 5 };

      vi.mocked(httpClient.post).mockResolvedValue({
        data: { ...mockConsumption, quantity: 5 },
      } as any);

      const result = await expeditionItemsService.consumeItem(1, differentQuantity);

      expect(result.quantity).toBe(5);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to consume item');
      vi.mocked(httpClient.post).mockRejectedValue(error);

      await expect(expeditionItemsService.consumeItem(1, consumeRequest)).rejects.toThrow(
        'Failed to consume item'
      );
    });
  });

  describe('getConsumptions', () => {
    const mockConsumptions = [mockConsumption];

    it('should fetch all consumptions', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { consumptions: mockConsumptions },
      } as any);

      const result = await expeditionItemsService.getConsumptions();

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/consumptions', {
        params: undefined,
      });
      expect(result).toEqual(mockConsumptions);
    });

    it('should filter by consumer name', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { consumptions: mockConsumptions },
      } as any);

      await expeditionItemsService.getConsumptions({ consumer_name: 'Test Pirate' });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/consumptions', {
        params: { consumer_name: 'Test Pirate' },
      });
    });

    it('should filter by payment status', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { consumptions: mockConsumptions },
      } as any);

      await expeditionItemsService.getConsumptions({ payment_status: 'paid' });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/consumptions', {
        params: { payment_status: 'paid' },
      });
    });

    it('should handle empty consumptions', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { consumptions: [] },
      } as any);

      const result = await expeditionItemsService.getConsumptions();

      expect(result).toEqual([]);
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch consumptions');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(expeditionItemsService.getConsumptions()).rejects.toThrow(
        'Failed to fetch consumptions'
      );
    });
  });

  describe('Service Instance', () => {
    it('should export a singleton instance', () => {
      expect(expeditionItemsService).toBeInstanceOf(ExpeditionItemsService);
    });

    it('should export the class for testing', () => {
      expect(ExpeditionItemsService).toBeDefined();
      const newInstance = new ExpeditionItemsService();
      expect(newInstance).toBeInstanceOf(ExpeditionItemsService);
    });
  });
});
