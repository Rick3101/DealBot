/**
 * API Client Facade (Backward Compatible)
 *
 * This facade maintains backward compatibility with the old expeditionApi
 * while delegating to the new domain-specific services.
 *
 * @deprecated Individual domain services should be used instead:
 * - expeditionService for expedition CRUD operations
 * - expeditionItemsService for items and consumption operations
 * - exportService for export and report operations
 * - dashboardService for dashboard/analytics
 * - bramblerService for pirate name operations
 * - productService for product operations
 * - userService for user/buyer operations
 * - utilityService for health checks and downloads
 */

import { expeditionService } from './expeditionService';
import { expeditionItemsService } from './expeditionItemsService';
import { exportService } from './exportService';
import { dashboardService } from './dashboardService';
import { bramblerService } from './bramblerService';
import { productService } from './productService';
import { userService } from './userService';
import { utilityService } from './utilityService';
import { httpClient } from './httpClient';

import {
  Expedition,
  ExpeditionDetails,
  CreateExpeditionRequest,
  CreateExpeditionItemRequest,
  ConsumeItemRequest,
  PirateName,
  BramblerGenerateRequest,
  BramblerDecryptRequest,
  TimelineData,
  AnalyticsData,
  ItemConsumption,
  Product,
} from '@/types/expedition';

/**
 * API Client Facade
 *
 * Maintains backward compatibility while using new service architecture
 */
class ApiClient {
  // Expedition CRUD operations
  async getExpeditions(): Promise<Expedition[]> {
    console.warn('[DEPRECATED] Use expeditionService.getAll() instead');
    return expeditionService.getAll();
  }

  async getExpeditionById(id: number): Promise<ExpeditionDetails> {
    console.warn('[DEPRECATED] Use expeditionService.getById() instead');
    return expeditionService.getById(id);
  }

  async createExpedition(data: CreateExpeditionRequest): Promise<Expedition> {
    console.warn('[DEPRECATED] Use expeditionService.create() instead');
    return expeditionService.create(data);
  }

  async updateExpeditionStatus(id: number, status: string): Promise<Expedition> {
    console.warn('[DEPRECATED] Use expeditionService.updateStatus() instead');
    return expeditionService.updateStatus(id, status as any);
  }

  async deleteExpedition(id: number): Promise<void> {
    console.warn('[DEPRECATED] Use expeditionService.delete() instead');
    return expeditionService.delete(id);
  }

  // Expedition items management
  async getExpeditionItems(expeditionId: number): Promise<any[]> {
    console.warn('[DEPRECATED] Use expeditionItemsService.getItems() instead');
    return expeditionItemsService.getItems(expeditionId);
  }

  async addItemsToExpedition(expeditionId: number, data: CreateExpeditionItemRequest): Promise<any[]> {
    console.warn('[DEPRECATED] Use expeditionItemsService.addItems() instead');
    return expeditionItemsService.addItems(expeditionId, data);
  }

  // Item consumption
  async consumeItem(expeditionId: number, data: ConsumeItemRequest): Promise<ItemConsumption> {
    console.warn('[DEPRECATED] Use expeditionItemsService.consumeItem() instead');
    return expeditionItemsService.consumeItem(expeditionId, data);
  }

  async getConsumptions(params?: {
    consumer_name?: string;
    payment_status?: string;
  }): Promise<ItemConsumption[]> {
    console.warn('[DEPRECATED] Use expeditionItemsService.getConsumptions() instead');
    return expeditionItemsService.getConsumptions(params);
  }

  // Brambler (name anonymization) operations
  async generatePirateNames(expeditionId: number, data: BramblerGenerateRequest): Promise<PirateName[]> {
    console.warn('[DEPRECATED] Use bramblerService.generateNames() instead');
    return bramblerService.generateNames(expeditionId, data);
  }

  async decryptPirateNames(expeditionId: number, data: BramblerDecryptRequest): Promise<Record<string, string>> {
    console.warn('[DEPRECATED] Use bramblerService.decryptNames() instead');
    return bramblerService.decryptNames(expeditionId, data);
  }

  async getPirateNames(expeditionId: number): Promise<PirateName[]> {
    console.warn('[DEPRECATED] Use bramblerService.getNames() instead');
    return bramblerService.getNames(expeditionId);
  }

  // Dashboard and analytics
  async getDashboardTimeline(): Promise<TimelineData> {
    console.warn('[DEPRECATED] Use dashboardService.getTimeline() instead');
    return dashboardService.getTimeline();
  }

  async getOverdueExpeditions(): Promise<any> {
    console.warn('[DEPRECATED] Use dashboardService.getOverdueExpeditions() instead');
    return dashboardService.getOverdueExpeditions();
  }

  async getAnalytics(): Promise<AnalyticsData> {
    console.warn('[DEPRECATED] Use dashboardService.getAnalytics() instead');
    return dashboardService.getAnalytics();
  }

  // Products
  async getProducts(): Promise<Product[]> {
    console.warn('[DEPRECATED] Use productService.getAll() instead');
    return productService.getAll();
  }

  // Users
  async getUsers(): Promise<{ username: string; level: string; total_purchases: string; last_access: string; status: string }[]> {
    console.warn('[DEPRECATED] Use userService.getUsers() instead');
    return userService.getUsers();
  }

  // Buyers (from sales)
  async getBuyers(): Promise<{ name: string }[]> {
    console.warn('[DEPRECATED] Use userService.getBuyers() instead');
    return userService.getBuyers();
  }

  // Export functionality
  async exportExpeditionData(params?: {
    expedition_id?: number;
    status?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<{ file_path: string; filename: string; download_url: string }> {
    console.warn('[DEPRECATED] Use exportService.exportExpeditionData() instead');
    return exportService.exportExpeditionData(params);
  }

  async exportPirateActivityReport(params?: {
    expedition_id?: number;
    anonymized?: boolean;
    date_from?: string;
    date_to?: string;
  }): Promise<{ file_path: string; filename: string; download_url: string }> {
    console.warn('[DEPRECATED] Use exportService.exportPirateActivityReport() instead');
    return exportService.exportPirateActivityReport(params);
  }

  async exportProfitLossReport(params?: {
    expedition_id?: number;
    date_from?: string;
    date_to?: string;
  }): Promise<{ file_path: string; filename: string; download_url: string }> {
    console.warn('[DEPRECATED] Use exportService.exportProfitLossReport() instead');
    return exportService.exportProfitLossReport(params);
  }

  // Search
  async searchExpeditions(params: {
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
    console.warn('[DEPRECATED] Use expeditionService.search() instead');
    return expeditionService.search(params);
  }

  // Health check
  async healthCheck(): Promise<any> {
    console.warn('[DEPRECATED] Use utilityService.healthCheck() instead');
    return utilityService.healthCheck();
  }

  // Download file helper
  async downloadFile(url: string): Promise<Blob> {
    console.warn('[DEPRECATED] Use utilityService.downloadFile() instead');
    return utilityService.downloadFile(url);
  }

  // Utility method to get full URL
  getFullUrl(path: string): string {
    console.warn('[DEPRECATED] Use utilityService.getFullUrl() instead');
    return utilityService.getFullUrl(path);
  }
}

// Create and export singleton instance for backward compatibility
export const apiClient = new ApiClient();

// Alias as expeditionApi for backward compatibility
export const expeditionApi = apiClient;

// Export class
export { ApiClient };

// Re-export all domain services for migration
export {
  expeditionService,
  expeditionItemsService,
  exportService,
  dashboardService,
  bramblerService,
  productService,
  userService,
  utilityService,
  httpClient,
};
