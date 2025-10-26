import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useExpeditionCRUD } from './useExpeditionCRUD';
import { expeditionService } from '@/services/api/expeditionService';

vi.mock('@/services/api/expeditionService');

describe('useExpeditionCRUD', () => {
  const mockExpedition = {
    id: 1,
    name: 'Test Expedition',
    description: 'Test Description',
    status: 'active',
    created_at: '2025-01-01',
    deadline: '2025-12-31',
    items: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createExpedition', () => {
    it('should create expedition successfully', async () => {
      vi.mocked(expeditionService.create).mockResolvedValue(mockExpedition);

      const { result } = renderHook(() => useExpeditionCRUD());

      const newExpedition = await result.current.createExpedition({
        name: 'Test Expedition',
        description: 'Test Description',
        deadline_days: 30,
      });

      expect(newExpedition).toEqual(mockExpedition);
      expect(result.current.error).toBeNull();
    });

    it('should handle create errors', async () => {
      const errorMessage = 'Failed to create';
      vi.mocked(expeditionService.create).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useExpeditionCRUD());

      const newExpedition = await result.current.createExpedition({
        name: 'Test Expedition',
        description: 'Test Description',
        deadline_days: 30,
      });

      await waitFor(() => {
        expect(newExpedition).toBeNull();
        expect(result.current.error).toBe(errorMessage);
      });
    });

    it('should call onSuccess callback on successful creation', async () => {
      const onSuccess = vi.fn();
      vi.mocked(expeditionService.create).mockResolvedValue(mockExpedition);

      const { result } = renderHook(() => useExpeditionCRUD({ onSuccess }));

      await result.current.createExpedition({
        name: 'Test Expedition',
        description: 'Test Description',
        deadline_days: 30,
      });

      expect(onSuccess).toHaveBeenCalledTimes(1);
    });

    it('should call onError callback on creation failure', async () => {
      const onError = vi.fn();
      const errorMessage = 'Failed to create';
      vi.mocked(expeditionService.create).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useExpeditionCRUD({ onError }));

      await result.current.createExpedition({
        name: 'Test Expedition',
        description: 'Test Description',
        deadline_days: 30,
      });

      expect(onError).toHaveBeenCalledWith(errorMessage);
    });
  });

  describe('updateExpeditionStatus', () => {
    it('should update expedition status successfully', async () => {
      const updatedExpedition = { ...mockExpedition, status: 'completed' };
      vi.mocked(expeditionService.updateStatus).mockResolvedValue(updatedExpedition);

      const { result } = renderHook(() => useExpeditionCRUD());

      const updated = await result.current.updateExpeditionStatus(1, 'completed');

      expect(updated).toEqual(updatedExpedition);
      expect(result.current.error).toBeNull();
    });

    it('should handle update errors', async () => {
      const errorMessage = 'Failed to update';
      vi.mocked(expeditionService.updateStatus).mockRejectedValue(
        new Error(errorMessage)
      );

      const { result } = renderHook(() => useExpeditionCRUD());

      const updated = await result.current.updateExpeditionStatus(1, 'completed');

      await waitFor(() => {
        expect(updated).toBeNull();
        expect(result.current.error).toBe(errorMessage);
      });
    });
  });

  describe('deleteExpedition', () => {
    it('should delete expedition successfully', async () => {
      vi.mocked(expeditionService.delete).mockResolvedValue(undefined);

      const { result } = renderHook(() => useExpeditionCRUD());

      const success = await result.current.deleteExpedition(1);

      expect(success).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should handle delete errors', async () => {
      const errorMessage = 'Failed to delete';
      vi.mocked(expeditionService.delete).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useExpeditionCRUD());

      const success = await result.current.deleteExpedition(1);

      await waitFor(() => {
        expect(success).toBe(false);
        expect(result.current.error).toBe(errorMessage);
      });
    });
  });

  describe('clearError', () => {
    it('should clear error state', async () => {
      vi.mocked(expeditionService.create).mockRejectedValue(
        new Error('Test error')
      );

      const { result } = renderHook(() => useExpeditionCRUD());

      // Create error
      await result.current.createExpedition({
        name: 'Test',
        description: 'Test',
        deadline_days: 30,
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Test error');
      });

      // Clear error
      result.current.clearError();

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });
  });
});
