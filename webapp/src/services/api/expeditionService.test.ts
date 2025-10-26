/**
 * Tests for Expedition Service
 *
 * Tests all expedition CRUD operations and search functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { expeditionService, ExpeditionService } from './expeditionService';
import { httpClient } from './httpClient';
import type { Expedition, ExpeditionDetails, CreateExpeditionRequest } from '@/types/expedition';

// Mock httpClient
vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('ExpeditionService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockExpedition: Expedition = {
    id: 1,
    name: 'Test Expedition',
    description: 'Test Description',
    status: 'active',
    created_at: '2025-01-01',
    deadline: '2025-12-31',
    items: [],
  };

  const mockExpeditionDetails: ExpeditionDetails = {
    ...mockExpedition,
    items: [
      {
        id: 1,
        product_id: 100,
        product_name: 'Test Product',
        target_price: 50,
        quantity: 10,
        consumed: 5,
      },
    ],
    pirate_names: [],
    consumptions: [],
    progress: {
      total_items: 1,
      consumed_items: 1,
      total_quantity: 10,
      consumed_quantity: 5,
      completion_percentage: 50,
    },
  };

  const mockExpeditions: Expedition[] = [mockExpedition];

  describe('getAll', () => {
    it('should fetch all expeditions', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { expeditions: mockExpeditions },
      } as any);

      const result = await expeditionService.getAll();

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions');
      expect(result).toEqual(mockExpeditions);
    });

    it('should handle empty expedition list', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { expeditions: [] },
      } as any);

      const result = await expeditionService.getAll();

      expect(result).toEqual([]);
    });

    it('should propagate errors', async () => {
      const error = new Error('Network error');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(expeditionService.getAll()).rejects.toThrow('Network error');
    });
  });

  describe('getById', () => {
    it('should fetch expedition by ID', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExpeditionDetails,
      } as any);

      const result = await expeditionService.getById(1);

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/1');
      expect(result).toEqual(mockExpeditionDetails);
    });

    it('should handle different expedition IDs', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { ...mockExpeditionDetails, id: 42 },
      } as any);

      const result = await expeditionService.getById(42);

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/42');
      expect(result.id).toBe(42);
    });

    it('should propagate errors for invalid ID', async () => {
      const error = new Error('Expedition not found');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(expeditionService.getById(999)).rejects.toThrow('Expedition not found');
    });
  });

  describe('create', () => {
    const createRequest: CreateExpeditionRequest = {
      name: 'New Expedition',
      description: 'New Description',
      deadline_days: 30,
    };

    it('should create new expedition', async () => {
      vi.mocked(httpClient.post).mockResolvedValue({
        data: mockExpedition,
      } as any);

      const result = await expeditionService.create(createRequest);

      expect(httpClient.post).toHaveBeenCalledWith('/api/expeditions', createRequest);
      expect(result).toEqual(mockExpedition);
    });

    it('should handle creation with all fields', async () => {
      const fullRequest = {
        ...createRequest,
        owner_chat_id: 12345,
      };

      vi.mocked(httpClient.post).mockResolvedValue({
        data: mockExpedition,
      } as any);

      await expeditionService.create(fullRequest);

      expect(httpClient.post).toHaveBeenCalledWith('/api/expeditions', fullRequest);
    });

    it('should propagate creation errors', async () => {
      const error = new Error('Failed to create');
      vi.mocked(httpClient.post).mockRejectedValue(error);

      await expect(expeditionService.create(createRequest)).rejects.toThrow('Failed to create');
    });
  });

  describe('updateStatus', () => {
    it('should update expedition status to completed', async () => {
      const updated = { ...mockExpedition, status: 'completed' };
      vi.mocked(httpClient.put).mockResolvedValue({
        data: updated,
      } as any);

      const result = await expeditionService.updateStatus(1, 'completed');

      expect(httpClient.put).toHaveBeenCalledWith('/api/expeditions/1', { status: 'completed' });
      expect(result.status).toBe('completed');
    });

    it('should update expedition status to cancelled', async () => {
      const updated = { ...mockExpedition, status: 'cancelled' };
      vi.mocked(httpClient.put).mockResolvedValue({
        data: updated,
      } as any);

      const result = await expeditionService.updateStatus(1, 'cancelled');

      expect(httpClient.put).toHaveBeenCalledWith('/api/expeditions/1', { status: 'cancelled' });
      expect(result.status).toBe('cancelled');
    });

    it('should propagate update errors', async () => {
      const error = new Error('Failed to update');
      vi.mocked(httpClient.put).mockRejectedValue(error);

      await expect(expeditionService.updateStatus(1, 'active')).rejects.toThrow('Failed to update');
    });
  });

  describe('delete', () => {
    it('should delete expedition', async () => {
      vi.mocked(httpClient.delete).mockResolvedValue({} as any);

      await expeditionService.delete(1);

      expect(httpClient.delete).toHaveBeenCalledWith('/api/expeditions/1');
    });

    it('should handle delete for different IDs', async () => {
      vi.mocked(httpClient.delete).mockResolvedValue({} as any);

      await expeditionService.delete(42);

      expect(httpClient.delete).toHaveBeenCalledWith('/api/expeditions/42');
    });

    it('should propagate delete errors', async () => {
      const error = new Error('Failed to delete');
      vi.mocked(httpClient.delete).mockRejectedValue(error);

      await expect(expeditionService.delete(1)).rejects.toThrow('Failed to delete');
    });
  });

  describe('search', () => {
    const mockSearchResults = {
      results: [mockExpedition],
      total_count: 1,
      limit: 10,
      offset: 0,
      has_more: false,
    };

    it('should search expeditions with query', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockSearchResults,
      } as any);

      const result = await expeditionService.search({ q: 'test' });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/search', {
        params: { q: 'test' },
      });
      expect(result).toEqual(mockSearchResults);
    });

    it('should search with status filter', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockSearchResults,
      } as any);

      await expeditionService.search({ status: 'active' });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/search', {
        params: { status: 'active' },
      });
    });

    it('should search with pagination', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockSearchResults,
      } as any);

      await expeditionService.search({ limit: 20, offset: 10 });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/search', {
        params: { limit: 20, offset: 10 },
      });
    });

    it('should search with date range', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockSearchResults,
      } as any);

      await expeditionService.search({
        date_from: '2025-01-01',
        date_to: '2025-12-31',
      });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/search', {
        params: {
          date_from: '2025-01-01',
          date_to: '2025-12-31',
        },
      });
    });

    it('should search with sorting', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockSearchResults,
      } as any);

      await expeditionService.search({
        sort_by: 'created_at',
        sort_order: 'desc',
      });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/search', {
        params: {
          sort_by: 'created_at',
          sort_order: 'desc',
        },
      });
    });

    it('should handle empty search results', async () => {
      const emptyResults = {
        results: [],
        total_count: 0,
        limit: 10,
        offset: 0,
        has_more: false,
      };

      vi.mocked(httpClient.get).mockResolvedValue({
        data: emptyResults,
      } as any);

      const result = await expeditionService.search({ q: 'nonexistent' });

      expect(result.results).toEqual([]);
      expect(result.total_count).toBe(0);
    });

    it('should propagate search errors', async () => {
      const error = new Error('Search failed');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(expeditionService.search({ q: 'test' })).rejects.toThrow('Search failed');
    });
  });

  describe('Service Instance', () => {
    it('should export a singleton instance', () => {
      expect(expeditionService).toBeInstanceOf(ExpeditionService);
    });

    it('should export the class for testing', () => {
      expect(ExpeditionService).toBeDefined();
      const newInstance = new ExpeditionService();
      expect(newInstance).toBeInstanceOf(ExpeditionService);
    });
  });
});
