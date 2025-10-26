import { useState, useEffect, useCallback } from 'react';
import { ExpeditionDetails } from '@/types/expedition';
import { expeditionService } from '@/services/api/expeditionService';
import { useRealTimeUpdates } from './useRealTimeUpdates';

interface UseExpeditionDetailsOptions {
  enableRealTime?: boolean;
  enableHaptic?: boolean;
  enablePopups?: boolean;
}

export const useExpeditionDetails = (
  expeditionId: number,
  options: UseExpeditionDetailsOptions = {}
) => {
  const { enableRealTime = true, enableHaptic = true, enablePopups = true } = options;

  const [expedition, setExpedition] = useState<ExpeditionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load expedition data from API
  const loadExpedition = useCallback(async (showLoader = true) => {
    console.log('[useExpeditionDetails] loadExpedition called, showLoader:', showLoader);
    if (showLoader) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError(null);

    try {
      console.log('[useExpeditionDetails] Fetching expedition', expeditionId);
      const data = await expeditionService.getById(expeditionId);
      console.log('[useExpeditionDetails] Received expedition data:', {
        id: data.id,
        name: data.name,
        status: data.status,
        items: data.items?.length,
        consumptions: data.consumptions?.length
      });
      console.log('[useExpeditionDetails] Consumption details:');
      data.consumptions?.forEach(c => {
        console.log(`  ID ${c.id}: ${c.pirate_name} - Status: ${c.payment_status}, Paid: ${c.amount_paid}/${c.total_price}`);
      });

      const oldExpeditionId = expedition?.id;
      setExpedition(data);
      console.log('[useExpeditionDetails] State updated successfully', {
        previousExpeditionId: oldExpeditionId,
        newExpeditionId: data.id,
        sameReference: expedition === data
      });
    } catch (err) {
      console.error('[useExpeditionDetails] Error loading expedition:', err);
      setError('Failed to load expedition details. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
      console.log('[useExpeditionDetails] Loading/refreshing state cleared');
    }
  }, [expeditionId]);

  // Subscribe to real-time updates for this expedition
  const { updates } = useRealTimeUpdates(
    enableRealTime ? expeditionId : undefined,
    {
      enableHaptic,
      enablePopups,
      autoJoinExpeditions: true,
    }
  );

  // Handle real-time updates
  useEffect(() => {
    if (updates.length > 0) {
      const latestUpdate = updates[0];
      // Refresh expedition data when new update arrives
      if (latestUpdate.expedition_id === expeditionId) {
        console.log('Received update for expedition:', latestUpdate);
        loadExpedition(false);
      }
    }
  }, [updates, expeditionId, loadExpedition]);

  // Initial load
  useEffect(() => {
    loadExpedition(true);
  }, [loadExpedition]);

  const refresh = useCallback(async () => {
    await loadExpedition(false);
  }, [loadExpedition]);

  return {
    expedition,
    loading,
    refreshing,
    error,
    refresh,
  };
};
