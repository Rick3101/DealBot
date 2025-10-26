/**
 * Tests for Export Service
 *
 * Tests export and report generation operations.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { exportService, ExportService } from './exportService';
import { httpClient } from './httpClient';

// Mock httpClient
vi.mock('./httpClient', () => ({
  httpClient: {
    get: vi.fn(),
  },
}));

describe('ExportService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockExportResponse = {
    file_path: '/tmp/export_123.csv',
    filename: 'expedition_export_2025.csv',
    download_url: '/api/downloads/export_123.csv',
  };

  describe('exportExpeditionData', () => {
    it('should export all expedition data', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      const result = await exportService.exportExpeditionData();

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/export', {
        params: undefined,
      });
      expect(result).toEqual(mockExportResponse);
    });

    it('should filter by expedition ID', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportExpeditionData({ expedition_id: 1 });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/export', {
        params: { expedition_id: 1 },
      });
    });

    it('should filter by status', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportExpeditionData({ status: 'active' });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/export', {
        params: { status: 'active' },
      });
    });

    it('should filter by date range', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportExpeditionData({
        date_from: '2025-01-01',
        date_to: '2025-12-31',
      });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/export', {
        params: {
          date_from: '2025-01-01',
          date_to: '2025-12-31',
        },
      });
    });

    it('should handle all filters combined', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportExpeditionData({
        expedition_id: 1,
        status: 'completed',
        date_from: '2025-01-01',
        date_to: '2025-12-31',
      });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/export', {
        params: {
          expedition_id: 1,
          status: 'completed',
          date_from: '2025-01-01',
          date_to: '2025-12-31',
        },
      });
    });

    it('should propagate errors', async () => {
      const error = new Error('Export failed');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(exportService.exportExpeditionData()).rejects.toThrow('Export failed');
    });
  });

  describe('exportPirateActivityReport', () => {
    it('should export pirate activity report', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      const result = await exportService.exportPirateActivityReport();

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/pirate-activity', {
        params: undefined,
      });
      expect(result).toEqual(mockExportResponse);
    });

    it('should filter by expedition ID', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportPirateActivityReport({ expedition_id: 1 });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/pirate-activity', {
        params: { expedition_id: 1 },
      });
    });

    it('should export anonymized report', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportPirateActivityReport({ anonymized: true });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/pirate-activity', {
        params: { anonymized: true },
      });
    });

    it('should export non-anonymized report', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportPirateActivityReport({ anonymized: false });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/pirate-activity', {
        params: { anonymized: false },
      });
    });

    it('should filter by date range', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportPirateActivityReport({
        date_from: '2025-01-01',
        date_to: '2025-12-31',
      });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/pirate-activity', {
        params: {
          date_from: '2025-01-01',
          date_to: '2025-12-31',
        },
      });
    });

    it('should propagate errors', async () => {
      const error = new Error('Report generation failed');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(exportService.exportPirateActivityReport()).rejects.toThrow(
        'Report generation failed'
      );
    });
  });

  describe('exportProfitLossReport', () => {
    it('should export profit/loss report', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      const result = await exportService.exportProfitLossReport();

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/profit-loss', {
        params: undefined,
      });
      expect(result).toEqual(mockExportResponse);
    });

    it('should filter by expedition ID', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportProfitLossReport({ expedition_id: 1 });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/profit-loss', {
        params: { expedition_id: 1 },
      });
    });

    it('should filter by date range', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportProfitLossReport({
        date_from: '2025-01-01',
        date_to: '2025-12-31',
      });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/profit-loss', {
        params: {
          date_from: '2025-01-01',
          date_to: '2025-12-31',
        },
      });
    });

    it('should handle all filters combined', async () => {
      vi.mocked(httpClient.get).mockResolvedValue({
        data: mockExportResponse,
      } as any);

      await exportService.exportProfitLossReport({
        expedition_id: 1,
        date_from: '2025-01-01',
        date_to: '2025-12-31',
      });

      expect(httpClient.get).toHaveBeenCalledWith('/api/expeditions/reports/profit-loss', {
        params: {
          expedition_id: 1,
          date_from: '2025-01-01',
          date_to: '2025-12-31',
        },
      });
    });

    it('should propagate errors', async () => {
      const error = new Error('Report generation failed');
      vi.mocked(httpClient.get).mockRejectedValue(error);

      await expect(exportService.exportProfitLossReport()).rejects.toThrow(
        'Report generation failed'
      );
    });
  });

  describe('Service Instance', () => {
    it('should export a singleton instance', () => {
      expect(exportService).toBeInstanceOf(ExportService);
    });

    it('should export the class for testing', () => {
      expect(ExportService).toBeDefined();
      const newInstance = new ExportService();
      expect(newInstance).toBeInstanceOf(ExportService);
    });
  });
});
