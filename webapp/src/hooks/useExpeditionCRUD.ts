import { useState, useCallback } from 'react';
import { Expedition, CreateExpeditionRequest } from '@/types/expedition';
import { expeditionService } from '@/services/api/expeditionService';

interface UseExpeditionCRUDOptions {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

interface UseExpeditionCRUDReturn {
  error: string | null;
  createExpedition: (data: CreateExpeditionRequest) => Promise<Expedition | null>;
  updateExpeditionStatus: (id: number, status: string) => Promise<Expedition | null>;
  deleteExpedition: (id: number) => Promise<boolean>;
  clearError: () => void;
}

/**
 * Hook for managing expedition CRUD operations
 * Single Responsibility: Create, Update, Delete operations
 */
export const useExpeditionCRUD = (
  options: UseExpeditionCRUDOptions = {}
): UseExpeditionCRUDReturn => {
  const { onSuccess, onError } = options;
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const createExpedition = useCallback(
    async (data: CreateExpeditionRequest): Promise<Expedition | null> => {
      try {
        setError(null);
        const newExpedition = await expeditionService.create(data);

        if (onSuccess) {
          onSuccess();
        }

        return newExpedition;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to create expedition';
        console.error('Failed to create expedition:', err);
        setError(errorMessage);

        if (onError) {
          onError(errorMessage);
        }

        return null;
      }
    },
    [onSuccess, onError]
  );

  const updateExpeditionStatus = useCallback(
    async (id: number, status: string): Promise<Expedition | null> => {
      try {
        setError(null);
        const updatedExpedition = await expeditionService.updateStatus(id, status as 'active' | 'completed' | 'cancelled');

        if (onSuccess) {
          onSuccess();
        }

        return updatedExpedition;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update expedition';
        console.error('Failed to update expedition status:', err);
        setError(errorMessage);

        if (onError) {
          onError(errorMessage);
        }

        return null;
      }
    },
    [onSuccess, onError]
  );

  const deleteExpedition = useCallback(
    async (id: number): Promise<boolean> => {
      try {
        setError(null);
        await expeditionService.delete(id);

        if (onSuccess) {
          onSuccess();
        }

        return true;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete expedition';
        console.error('Failed to delete expedition:', err);
        setError(errorMessage);

        if (onError) {
          onError(errorMessage);
        }

        return false;
      }
    },
    [onSuccess, onError]
  );

  return {
    error,
    createExpedition,
    updateExpeditionStatus,
    deleteExpedition,
    clearError,
  };
};
