/**
 * Brambler Service
 *
 * Handles pirate name generation and encryption/decryption.
 * Domain: Name anonymization (Brambler) only.
 */

import { httpClient } from './httpClient';
import {
  PirateName,
  BramblerGenerateRequest,
  BramblerDecryptRequest,
} from '@/types/expedition';

/**
 * Brambler Service
 *
 * Responsible for:
 * - Generating pirate names (anonymization)
 * - Decrypting pirate names (owner only)
 * - Retrieving pirate names for an expedition
 */
class BramblerService {
  private readonly basePath = '/api/brambler';

  /**
   * Generate pirate names for an expedition
   */
  async generateNames(expeditionId: number, data: BramblerGenerateRequest): Promise<PirateName[]> {
    const response = await httpClient.post<{ pirate_names: PirateName[] }>(
      `${this.basePath}/generate/${expeditionId}`,
      data
    );
    return response.data.pirate_names;
  }

  /**
   * Decrypt pirate names (owner only)
   */
  async decryptNames(expeditionId: number, data: BramblerDecryptRequest): Promise<Record<string, string>> {
    const response = await httpClient.post<{
      success: boolean;
      expedition_id: number;
      decrypted_count: number;
      mappings_dict: Record<string, string>;
    }>(
      `${this.basePath}/decrypt/${expeditionId}`,
      data
    );
    return response.data.mappings_dict;
  }

  /**
   * Get pirate names for an expedition
   */
  async getNames(expeditionId: number): Promise<PirateName[]> {
    const response = await httpClient.get<{ pirate_names: PirateName[] }>(
      `${this.basePath}/names/${expeditionId}`
    );
    return response.data.pirate_names;
  }

  /**
   * Get owner key for an expedition (owner only)
   */
  async getOwnerKey(expeditionId: number): Promise<string> {
    const response = await httpClient.get<{
      success: boolean;
      expedition_id: number;
      owner_key: string;
    }>(`${this.basePath}/owner-key/${expeditionId}`);
    return response.data.owner_key;
  }

  /**
   * Get user's master key (works for all their expeditions)
   */
  async getUserMasterKey(): Promise<string> {
    const response = await httpClient.get<{
      success: boolean;
      master_key: string;
      owner_chat_id: number;
      created_at: string;
      key_version: number;
      message: string;
    }>(`${this.basePath}/master-key`);
    return response.data.master_key;
  }

  /**
   * Get ALL pirate names across all expeditions (for maintenance page)
   */
  async getAllNames(): Promise<BramblerMaintenanceItem[]> {
    const response = await httpClient.get<{
      success: boolean;
      pirates: BramblerMaintenanceItem[];
      total_count: number;
    }>(`${this.basePath}/all-names`);
    return response.data.pirates;
  }

  /**
   * Update a pirate name by ID
   */
  async updatePirateName(pirateId: number, newPirateName: string): Promise<boolean> {
    const response = await httpClient.put<{
      success: boolean;
      pirate_id: number;
      new_pirate_name: string;
      message: string;
    }>(`${this.basePath}/update/${pirateId}`, {
      pirate_name: newPirateName
    });
    return response.data.success;
  }

  /**
   * Create a new pirate with optional custom name
   * If pirate_name is not provided, it will be auto-generated
   */
  async createPirate(data: BramblerCreateRequest): Promise<BramblerCreateResponse> {
    const response = await httpClient.post<{
      success: boolean;
      pirate: BramblerMaintenanceItem;
      message: string;
    }>(`${this.basePath}/create`, data);
    return {
      success: response.data.success,
      pirate: response.data.pirate,
      message: response.data.message
    };
  }

  /**
   * Create a new encrypted item with optional custom encrypted name
   * If encrypted_name is not provided, it will be auto-generated
   */
  async createEncryptedItem(data: BramblerCreateItemRequest): Promise<BramblerCreateItemResponse> {
    const response = await httpClient.post<{
      success: boolean;
      item: EncryptedItem;
      message: string;
    }>(`${this.basePath}/items/create`, data);
    return {
      success: response.data.success,
      item: response.data.item,
      message: response.data.message
    };
  }

  /**
   * Get ALL encrypted items across all owner's expeditions
   */
  async getAllEncryptedItems(): Promise<EncryptedItem[]> {
    const response = await httpClient.get<{
      success: boolean;
      items: EncryptedItem[];
      total_count: number;
    }>(`${this.basePath}/items/all`);
    return response.data.items;
  }

  /**
   * Decrypt item names for a specific expedition
   */
  async decryptItemNames(expeditionId: number, ownerKey: string): Promise<Record<string, string>> {
    const response = await httpClient.post<Record<string, string>>(
      `${this.basePath}/items/decrypt/${expeditionId}`,
      { owner_key: ownerKey }
    );
    return response.data;
  }

  /**
   * Delete a pirate by ID (owner only)
   */
  async deletePirate(pirateId: number): Promise<boolean> {
    const response = await httpClient.delete<{
      success: boolean;
      message: string;
    }>(`${this.basePath}/pirate/${pirateId}`);
    return response.data.success;
  }

  /**
   * Delete an encrypted item by ID (owner only)
   */
  async deleteEncryptedItem(itemId: number): Promise<boolean> {
    const response = await httpClient.delete<{
      success: boolean;
      message: string;
    }>(`${this.basePath}/items/${itemId}`);
    return response.data.success;
  }

  /**
   * Decrypt ALL pirates and items across ALL owner's expeditions using master key
   */
  async decryptAll(ownerKey: string): Promise<{
    pirate_mappings: Record<string, string>;
    item_mappings: Record<string, string>;
  }> {
    const response = await httpClient.post<{
      success: boolean;
      owner_chat_id: number;
      pirate_mappings: Record<string, string>;
      item_mappings: Record<string, string>;
      total_pirates_decrypted: number;
      total_items_decrypted: number;
    }>(`${this.basePath}/decrypt-all`, {
      owner_key: ownerKey
    });
    return {
      pirate_mappings: response.data.pirate_mappings,
      item_mappings: response.data.item_mappings
    };
  }
}

/**
 * Brambler Maintenance Item type (for maintenance page)
 */
export interface BramblerMaintenanceItem {
  id: number;
  pirate_name: string;
  original_name: string | null;
  expedition_id: number;
  expedition_name: string;
  encrypted_identity: string;
  owner_chat_id: number;
  created_at: string | null;
}

/**
 * Create Pirate Request
 */
export interface BramblerCreateRequest {
  expedition_id: number;
  original_name: string;
  pirate_name?: string; // Optional - will be auto-generated if not provided
}

/**
 * Create Pirate Response
 */
export interface BramblerCreateResponse {
  success: boolean;
  pirate: BramblerMaintenanceItem;
  message: string;
}

/**
 * Encrypted Item type (for Brambler item management)
 */
export interface EncryptedItem {
  id: number;
  expedition_id: number;
  expedition_name: string;
  original_item_name: string | null; // Always null for security
  encrypted_item_name: string;
  encrypted_mapping: string;
  anonymized_item_code: string;
  item_type: string; // 'product', 'custom', 'resource'
  quantity_required: number;
  quantity_consumed: number;
  item_status: string;
  created_at: string;
  is_encrypted: boolean;
}

/**
 * Create Encrypted Item Request
 */
export interface BramblerCreateItemRequest {
  expedition_id: number;
  original_item_name: string;
  encrypted_name?: string; // Optional - will be auto-generated if not provided
  owner_key: string;
  item_type?: string; // Optional - defaults to 'product'
}

/**
 * Create Encrypted Item Response
 */
export interface BramblerCreateItemResponse {
  success: boolean;
  item: EncryptedItem;
  message: string;
}

// Create and export singleton instance
export const bramblerService = new BramblerService();

// Export class for testing
export { BramblerService };
