import { useState, useCallback } from 'react';
import { expeditionItemsService } from '@/services/api/expeditionItemsService';
import { hapticFeedback } from '@/utils/telegram';

interface ConsumeItemParams {
  product_id: number;
  pirate_name: string;
  quantity: number;
  price: number;
}

export const useItemConsumption = (expeditionId: number) => {
  const [consuming, setConsuming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const consumeItem = useCallback(async (
    params: ConsumeItemParams,
    onSuccess?: () => void | Promise<void>
  ): Promise<void> => {
    setConsuming(true);
    setError(null);

    try {
      await expeditionItemsService.consumeItem(expeditionId, {
        product_id: params.product_id,
        pirate_name: params.pirate_name,
        quantity: params.quantity,
        price: params.price,
      });

      hapticFeedback('success');

      // Wait for the refresh to complete before resolving
      if (onSuccess) {
        await onSuccess();
      }
    } catch (err) {
      console.error('Error consuming item:', err);
      setError(err instanceof Error ? err.message : 'Failed to consume item');
      hapticFeedback('error');
      throw err;
    } finally {
      setConsuming(false);
    }
  }, [expeditionId]);

  return {
    consuming,
    error,
    consumeItem,
  };
};
