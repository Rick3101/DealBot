/**
 * Product Service
 *
 * Handles product-related operations.
 * Domain: Product management only.
 */

import { httpClient } from './httpClient';
import { Product } from '@/types/expedition';

/**
 * Product Service
 *
 * Responsible for:
 * - Getting product list
 * - Product CRUD operations (future expansion)
 */
class ProductService {
  private readonly basePath = '/api/products';

  /**
   * Get all products
   */
  async getAll(): Promise<Product[]> {
    const response = await httpClient.get<{ products: Product[] }>(this.basePath);
    return response.data.products;
  }

  /**
   * Get product by ID (future expansion)
   */
  async getById(id: number): Promise<Product> {
    const response = await httpClient.get<Product>(`${this.basePath}/${id}`);
    return response.data;
  }
}

// Create and export singleton instance
export const productService = new ProductService();

// Export class for testing
export { ProductService };
