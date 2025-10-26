/**
 * Export Service
 *
 * Handles all export and report generation operations.
 * Domain: Data export and reporting.
 */

import { httpClient } from './httpClient';

/**
 * Export file response interface
 */
export interface ExportFileResponse {
  file_path: string;
  filename: string;
  download_url: string;
}

/**
 * Export Service
 *
 * Responsible for:
 * - Exporting expedition data
 * - Generating pirate activity reports
 * - Generating profit/loss reports
 */
class ExportService {
  private readonly basePath = '/api/expeditions';

  /**
   * Export expedition data
   */
  async exportExpeditionData(params?: {
    expedition_id?: number;
    status?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<ExportFileResponse> {
    const response = await httpClient.get<ExportFileResponse>(`${this.basePath}/export`, { params });
    return response.data;
  }

  /**
   * Export pirate activity report
   */
  async exportPirateActivityReport(params?: {
    expedition_id?: number;
    anonymized?: boolean;
    date_from?: string;
    date_to?: string;
  }): Promise<ExportFileResponse> {
    const response = await httpClient.get<ExportFileResponse>(`${this.basePath}/reports/pirate-activity`, { params });
    return response.data;
  }

  /**
   * Export profit/loss report
   */
  async exportProfitLossReport(params?: {
    expedition_id?: number;
    date_from?: string;
    date_to?: string;
  }): Promise<ExportFileResponse> {
    const response = await httpClient.get<ExportFileResponse>(`${this.basePath}/reports/profit-loss`, { params });
    return response.data;
  }
}

// Create and export singleton instance
export const exportService = new ExportService();

// Export class for testing
export { ExportService };
