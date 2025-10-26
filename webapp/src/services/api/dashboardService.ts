/**
 * Dashboard Service
 *
 * Handles dashboard-specific data: timeline, analytics, and overdue expeditions.
 * Domain: Dashboard and analytics only.
 */

import { httpClient } from './httpClient';
import { TimelineData, AnalyticsData } from '@/types/expedition';

/**
 * Dashboard Service
 *
 * Responsible for:
 * - Timeline data (expeditions with progress)
 * - Analytics and statistics
 * - Overdue expedition tracking
 */
class DashboardService {
  private readonly basePath = '/api/dashboard';

  /**
   * Get dashboard timeline with expedition progress and stats
   */
  async getTimeline(): Promise<TimelineData> {
    const response = await httpClient.get<TimelineData>(`${this.basePath}/timeline`);
    return response.data;
  }

  /**
   * Get analytics data with comprehensive statistics
   */
  async getAnalytics(): Promise<AnalyticsData> {
    const response = await httpClient.get<AnalyticsData>(`${this.basePath}/analytics`);
    return response.data;
  }

  /**
   * Get overdue expeditions
   */
  async getOverdueExpeditions(): Promise<any> {
    const response = await httpClient.get(`${this.basePath}/overdue`);
    return response.data;
  }
}

// Create and export singleton instance
export const dashboardService = new DashboardService();

// Export class for testing
export { DashboardService };
