/**
 * Expedition Service
 *
 * Handles core Expedition CRUD operations.
 * Domain: Expedition entity management only.
 *
 * For items/consumption operations: use expeditionItemsService
 * For export/reports operations: use exportService
 */

import { httpClient } from './httpClient';
import {
  Expedition,
  ExpeditionDetails,
  CreateExpeditionRequest,
} from '@/types/expedition';

/**
 * Expedition Service
 *
 * Responsible for:
 * - Listing expeditions
 * - Getting expedition details
 * - Creating expeditions
 * - Updating expedition status
 * - Deleting expeditions
 * - Searching expeditions
 */
class ExpeditionService {
  private readonly basePath = '/api/expeditions';

  /**
   * Get all expeditions
   */
  async getAll(): Promise<Expedition[]> {
    const response = await httpClient.get<{ expeditions: Expedition[] }>(this.basePath);
    return response.data.expeditions;
  }

  /**
   * Get expedition by ID with full details
   */
  async getById(id: number): Promise<ExpeditionDetails> {
    const response = await httpClient.get<ExpeditionDetails>(`${this.basePath}/${id}`);
    return response.data;
  }

  /**
   * Create a new expedition
   */
  async create(data: CreateExpeditionRequest): Promise<Expedition> {
    const response = await httpClient.post<Expedition>(this.basePath, data);
    return response.data;
  }

  /**
   * Update expedition status
   */
  async updateStatus(id: number, status: 'active' | 'completed' | 'cancelled'): Promise<Expedition> {
    const response = await httpClient.put<Expedition>(`${this.basePath}/${id}`, { status });
    return response.data;
  }

  /**
   * Delete expedition
   */
  async delete(id: number): Promise<void> {
    await httpClient.delete(`${this.basePath}/${id}`);
  }

  /**
   * Search expeditions with advanced filters
   */
  async search(params: {
    q?: string;
    status?: string;
    owner_chat_id?: number;
    date_from?: string;
    date_to?: string;
    sort_by?: string;
    sort_order?: string;
    limit?: number;
    offset?: number;
  }): Promise<{
    results: any[];
    total_count: number;
    limit: number;
    offset: number;
    has_more: boolean;
  }> {
    const response = await httpClient.get(`${this.basePath}/search`, { params });
    return response.data;
  }
}

// Create and export singleton instance
export const expeditionService = new ExpeditionService();

// Export class for testing
export { ExpeditionService };
