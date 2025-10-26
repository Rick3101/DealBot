import { useState, useEffect, useCallback, useMemo } from 'react';
import { bramblerService } from '@/services/api/bramblerService';
import { userService } from '@/services/api/userService';
import { hapticFeedback } from '@/utils/telegram';
import { PirateName, Buyer } from '@/types/expedition';

export const useExpeditionPirates = (expeditionId: number | null) => {
  const [pirateNames, setPirateNames] = useState<PirateName[]>([]);
  const [allBuyers, setAllBuyers] = useState<Buyer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load pirate names for this expedition
  const loadPirateNames = useCallback(async () => {
    if (!expeditionId) return;

    try {
      const names = await bramblerService.getNames(expeditionId);
      setPirateNames(names);
    } catch (error) {
      console.error('Error loading pirate names:', error);
      setError('Failed to load pirate names');
    }
  }, [expeditionId]);

  // Load all buyers once (called on mount)
  const loadAllBuyers = useCallback(async () => {
    setLoading(true);
    try {
      const buyers = await userService.getBuyers();
      setAllBuyers(buyers.map(b => ({ name: b.name })));
    } catch (error) {
      console.error('Error loading buyers:', error);
      setError('Failed to load buyers');
    } finally {
      setLoading(false);
    }
  }, []);

  // Compute available buyers from existing data (no API call)
  const availableBuyers = useMemo(() => {
    // Get set of existing original names from pirates
    const existingOriginalNames = new Set(
      pirateNames.map(p => p.original_name).filter(Boolean)
    );

    // Filter out buyers who are already pirates in this expedition
    return allBuyers.filter(b => !existingOriginalNames.has(b.name));
  }, [allBuyers, pirateNames]);

  // Add a new pirate to the expedition
  const addPirate = useCallback(async (originalName: string): Promise<void> => {
    if (!expeditionId || !originalName.trim()) {
      throw new Error('Invalid expedition ID or pirate name');
    }

    try {
      await bramblerService.generateNames(expeditionId, {
        original_names: [originalName.trim()],
      });

      hapticFeedback('success');

      // Only need to reload pirate names - availableBuyers will auto-update via useMemo
      await loadPirateNames();
    } catch (error) {
      hapticFeedback('error');
      throw error;
    }
  }, [expeditionId, loadPirateNames]);

  // Initial load - load both pirates and buyers
  useEffect(() => {
    loadPirateNames();
    loadAllBuyers();
  }, [loadPirateNames, loadAllBuyers]);

  return {
    pirateNames,
    availableBuyers,
    loading,
    error,
    loadAvailableBuyers: loadAllBuyers, // Keeping same API for backwards compatibility
    addPirate,
    refresh: loadPirateNames,
  };
};
