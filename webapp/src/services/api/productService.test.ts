/**
 * Tests for Product Service
 *
 * Tests product fetching operations.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { productService, ProductService } from './productService';
import { httpClient } from './httpClient';

// Mock httpClient
vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
  },
}));

describe('ProductService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockProduct = {
    id: 1,
    name: 'Test Product',
    emoji: '🧪',
    media_type: null,
    media_file_id: null,
  };

  const mockProducts = [
    mockProduct,
    {
      id: 2,
      name: 'Another Product',
      emoji: '⚗️',
      media_type: 'photo',
      media_file_id: 'file_123',
    },
  ];

  describe('getAll', () => {
    it('should fetch all products', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { products: mockProducts },
      } as any);

      const result = await productService.getAll();

      expect(httpClient.get).toHaveBeenCalledWith('/api/products');
      expect(result).toEqual(mockProducts);
    });

    it('should handle empty product list', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { products: [] },
      } as any);

      const result = await productService.getAll();

      expect(result).toEqual([]);
    });

    it('should handle products with media', async () => {
      const productsWithMedia = [
        {
          id: 1,
          name: 'Product 1',
          emoji: '🧪',
          media_type: 'photo',
          media_file_id: 'photo_123',
        },
        {
          id: 2,
          name: 'Product 2',
          emoji: '⚗️',
          media_type: 'video',
          media_file_id: 'video_456',
        },
      ];

      vi.mocked(httpClient.get).mockResolvedValue({
        data: { products: productsWithMedia },
      } as any);

      const result = await productService.getAll();

      expect(result[0].media_type).toBe('photo');
      expect(result[1].media_type).toBe('video');
    });

    it('should propagate errors', async () => {
      const error = new Error('Failed to fetch products');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(productService.getAll()).rejects.toThrow('Failed to fetch products');
    });
  });

  describe('getById', () => {
    it('should fetch product by ID', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockProduct,
      } as any);

      const result = await productService.getById(1);

      expect(httpClient.get).toHaveBeenCalledWith('/api/products/1');
      expect(result).toEqual(mockProduct);
    });

    it('should handle different product IDs', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: { ...mockProduct, id: 42 },
      } as any);

      const result = await productService.getById(42);

      expect(httpClient.get).toHaveBeenCalledWith('/api/products/42');
      expect(result.id).toBe(42);
    });

    it('should handle product with all fields', async () => {
      const fullProduct = {
        id: 1,
        name: 'Complete Product',
        emoji: '🧪',
        media_type: 'photo',
        media_file_id: 'file_123',
        created_at: '2025-01-01',
        updated_at: '2025-01-02',
      };

      vi.mocked(httpClient.get).mockResolvedValue({
        data: fullProduct,
      } as any);

      const result = await productService.getById(1);

      expect(result.media_type).toBe('photo');
      expect(result.created_at).toBe('2025-01-01');
    });

    it('should propagate errors for invalid ID', async () => {
      const error = new Error('Product not found');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(productService.getById(999)).rejects.toThrow('Product not found');
    });
  });

  describe('Service Instance', () => {
    it('should export a singleton instance', () => {
      expect(productService).toBeInstanceOf(ProductService);
    });

    it('should export the class for testing', () => {
      expect(ProductService).toBeDefined();
      const newInstance = new ProductService();
      expect(newInstance).toBeInstanceOf(ProductService);
    });
  });
});
