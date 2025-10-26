/**
 * Utility Service
 *
 * Handles utility operations like health checks and file downloads.
 * Domain: System utilities.
 */

import { httpClient } from './httpClient';

/**
 * Utility Service
 *
 * Responsible for:
 * - Health checks
 * - File downloads
 * - URL generation
 */
class UtilityService {
  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<any> {
    const response = await httpClient.get('/health');
    return response.data;
  }

  /**
   * Download file from URL
   */
  async downloadFile(url: string): Promise<Blob> {
    const response = await httpClient.get(url, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Get full URL for a path
   */
  getFullUrl(path: string): string {
    return httpClient.getFullUrl(path);
  }
}

// Create and export singleton instance
export const utilityService = new UtilityService();

// Export class for testing
export { UtilityService };
