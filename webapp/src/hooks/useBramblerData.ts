import { useState, useEffect } from 'react';
import type { BramblerMaintenanceItem, EncryptedItem } from '@/services/api/bramblerService';
import { masterKeyStorage } from '@/services/masterKeyStorage';
import { showAlert } from '@/utils/telegram';

export interface BramblerDataState {
  // Pirates
  pirateNames: BramblerMaintenanceItem[];

  // Items
  encryptedItems: EncryptedItem[];

  // Expeditions
  expeditions: Array<{ id: number; name: string }>;

  // Loading & Error
  loading: boolean;
  error: string | null;

  // Owner Status
  isOwner: boolean;

  // Auto-loaded key metadata
  autoLoadedKey: string;
  keySource: string;
}

export interface BramblerDataActions {
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addPirate: (pirate: BramblerMaintenanceItem) => void;
  updatePirate: (updatedPirate: BramblerMaintenanceItem) => void;
  removePirate: (pirateId: number) => void;
  addItem: (item: EncryptedItem) => void;
  removeItem: (itemId: number) => void;
  refreshData: () => Promise<void>;
}

/**
 * Custom hook for managing Brambler data loading and state
 * Handles fetching pirates, items, and expeditions on mount
 * Auto-loads saved master key from storage
 */
export const useBramblerData = (): [BramblerDataState, BramblerDataActions] => {
  const [state, setState] = useState<BramblerDataState>({
    pirateNames: [],
    encryptedItems: [],
    expeditions: [],
    loading: true,
    error: null,
    isOwner: false,
    autoLoadedKey: '',
    keySource: '',
  });

  const loadAllData = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { bramblerService } = await import('@/services/api/bramblerService');
      const { expeditionService } = await import('@/services/api/expeditionService');

      // Load pirates, items, and expeditions in parallel
      const [allPirates, allItems, allExpeditions] = await Promise.all([
        bramblerService.getAllNames(),
        bramblerService.getAllEncryptedItems().catch(() => []), // Graceful fallback
        expeditionService.getAll().catch(() => []) // Graceful fallback
      ]);

      // User is owner if they have owner permission (checked by API)
      const isOwner = true; // API already validated permission

      console.log(`[useBramblerData] Loaded ${allPirates.length} pirates and ${allItems.length} items`);

      // Extract unique expeditions from items and pirates, merge with expedition list
      const expeditionMap = new Map<number, { id: number; name: string }>();

      // Add from pirates
      allPirates.forEach((pirate: BramblerMaintenanceItem) => {
        if (!expeditionMap.has(pirate.expedition_id)) {
          expeditionMap.set(pirate.expedition_id, {
            id: pirate.expedition_id,
            name: pirate.expedition_name
          });
        }
      });

      // Add from items
      allItems.forEach((item: EncryptedItem) => {
        if (!expeditionMap.has(item.expedition_id)) {
          expeditionMap.set(item.expedition_id, {
            id: item.expedition_id,
            name: item.expedition_name
          });
        }
      });

      // Add from full expedition list
      allExpeditions.forEach((exp: any) => {
        if (!expeditionMap.has(exp.id)) {
          expeditionMap.set(exp.id, {
            id: exp.id,
            name: exp.name
          });
        }
      });

      const expeditions = Array.from(expeditionMap.values());

      // AUTO-LOAD SAVED MASTER KEY
      let savedKey = '';
      let keySource = '';
      try {
        const keyMetadata = await masterKeyStorage.loadMasterKey();
        if (keyMetadata && keyMetadata.key) {
          savedKey = keyMetadata.key;
          keySource = keyMetadata.source === 'telegram_cloud' ? 'Telegram Cloud' : 'Local Storage';
          console.log(`[useBramblerData] Auto-loaded saved master key from ${keySource}`);
        }
      } catch (error) {
        console.warn('[useBramblerData] Failed to auto-load saved key:', error);
      }

      setState(prev => ({
        ...prev,
        pirateNames: allPirates,
        encryptedItems: allItems,
        expeditions,
        isOwner,
        autoLoadedKey: savedKey,
        keySource,
        loading: false
      }));

      // Show notification if key was auto-loaded
      if (savedKey && keySource) {
        showAlert(`Master key auto-loaded from ${keySource}! Click "Show Real Names" to decrypt.`);
      }
    } catch (error) {
      console.error('[useBramblerData] Failed to load data:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load data. Please try again.'
      }));
    }
  };

  // Load data on mount
  useEffect(() => {
    loadAllData();
  }, []); // No dependencies - load once on mount

  const actions: BramblerDataActions = {
    setLoading: (loading: boolean) => {
      setState(prev => ({ ...prev, loading }));
    },

    setError: (error: string | null) => {
      setState(prev => ({ ...prev, error }));
    },

    addPirate: (pirate: BramblerMaintenanceItem) => {
      setState(prev => ({
        ...prev,
        pirateNames: [...prev.pirateNames, pirate]
      }));
    },

    updatePirate: (updatedPirate: BramblerMaintenanceItem) => {
      setState(prev => ({
        ...prev,
        pirateNames: prev.pirateNames.map(p =>
          p.id === updatedPirate.id ? updatedPirate : p
        )
      }));
    },

    removePirate: (pirateId: number) => {
      setState(prev => ({
        ...prev,
        pirateNames: prev.pirateNames.filter(p => p.id !== pirateId)
      }));
    },

    addItem: (item: EncryptedItem) => {
      setState(prev => ({
        ...prev,
        encryptedItems: [...prev.encryptedItems, item]
      }));
    },

    removeItem: (itemId: number) => {
      setState(prev => ({
        ...prev,
        encryptedItems: prev.encryptedItems.filter(i => i.id !== itemId)
      }));
    },

    refreshData: loadAllData
  };

  return [state, actions];
};
