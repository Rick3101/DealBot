/**
 * Expedition Items Service
 *
 * Handles expedition items and consumption operations.
 * Domain: Expedition items management and consumption tracking.
 */

import { httpClient } from './httpClient';
import {
  CreateExpeditionItemRequest,
  ConsumeItemRequest,
  ItemConsumption,
  PayConsumptionRequest,
} from '@/types/expedition';

/**
 * Expedition Items Service
 *
 * Responsible for:
 * - Getting expedition items
 * - Adding items to expeditions
 * - Consuming items from expeditions
 * - Querying item consumptions
 */
class ExpeditionItemsService {
  private readonly basePath = '/api/expeditions';

  /**
   * Get expedition items
   */
  async getItems(expeditionId: number): Promise<any[]> {
    const response = await httpClient.get<{ items: any[] }>(`${this.basePath}/${expeditionId}/items`);
    return response.data.items;
  }

  /**
   * Add items to expedition
   */
  async addItems(expeditionId: number, data: CreateExpeditionItemRequest): Promise<any[]> {
    const response = await httpClient.post<{ items: any[] }>(`${this.basePath}/${expeditionId}/items`, data);
    return response.data.items;
  }

  /**
   * Consume item from expedition
   */
  async consumeItem(expeditionId: number, data: ConsumeItemRequest): Promise<ItemConsumption> {
    const response = await httpClient.post<ItemConsumption>(`${this.basePath}/${expeditionId}/consume`, data);
    return response.data;
  }

  /**
   * Get consumptions with optional filters
   */
  async getConsumptions(params?: {
    consumer_name?: string;
    payment_status?: string;
  }): Promise<ItemConsumption[]> {
    const response = await httpClient.get<{ consumptions: ItemConsumption[] }>(`${this.basePath}/consumptions`, {
      params,
    });
    return response.data.consumptions;
  }

  /**
   * Pay for a consumption (full or partial payment)
   */
  async payConsumption(data: PayConsumptionRequest): Promise<ItemConsumption> {
    const response = await httpClient.post<ItemConsumption>(`${this.basePath}/consumptions/${data.consumption_id}/pay`, {
      amount: data.amount,
    });
    return response.data;
  }
}

// Create and export singleton instance
export const expeditionItemsService = new ExpeditionItemsService();

// Export class for testing
export { ExpeditionItemsService };
