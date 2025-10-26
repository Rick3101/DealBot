import { useState } from 'react';
import { masterKeyStorage } from '@/services/masterKeyStorage';
import { hapticFeedback, showAlert, showConfirm } from '@/utils/telegram';

export interface DecryptionState {
  decryptionKey: string;
  showRealNames: boolean;
  decryptedMappings: Record<string, string>; // pirate_name -> original_name
  decryptedItemMappings: Record<string, string>; // encrypted_item_name -> original_item_name
  individualToggles: Record<number, boolean>; // pirate_id -> show_real_name
}

export interface DecryptionActions {
  setDecryptionKey: (key: string) => void;
  toggleView: (isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void) => Promise<void>;
  getMasterKey: (isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void) => Promise<void>;
  saveMasterKey: (isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void) => Promise<void>;
  clearSavedKey: (isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void) => Promise<void>;
  toggleIndividualName: (pirateId: number, isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void, e?: React.MouseEvent) => Promise<void>;
}

/**
 * Custom hook for managing decryption and master key operations
 * Handles bulk decryption, individual toggles, and master key management
 */
export const useBramblerDecryption = (): [DecryptionState, DecryptionActions] => {
  const [state, setState] = useState<DecryptionState>({
    decryptionKey: '',
    showRealNames: false,
    decryptedMappings: {},
    decryptedItemMappings: {},
    individualToggles: {},
  });

  const actions: DecryptionActions = {
    setDecryptionKey: (key: string) => {
      setState(prev => ({ ...prev, decryptionKey: key }));
    },

    toggleView: async (isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void) => {
      console.log('[useBramblerDecryption] handleToggleView START', {
        showRealNames: state.showRealNames,
        isOwner,
        hasDecryptedData: Object.keys(state.decryptedMappings).length > 0
      });

      if (!state.showRealNames && isOwner) {
        // If trying to show real names, check if we already have decrypted data
        if (!state.decryptionKey.trim()) {
          console.log('[useBramblerDecryption] No decryption key, showing error');
          setError('Please enter your master key');
          return;
        }

        // Check if we already have decrypted mappings - if so, just toggle without API call
        if (Object.keys(state.decryptedMappings).length > 0) {
          console.log('[useBramblerDecryption] Already have decrypted data, toggling instantly');
          hapticFeedback('light');
          setState(prev => ({ ...prev, showRealNames: true }));
          setError(null);
          return;
        }

        console.log('[useBramblerDecryption] No cached data, calling API to decrypt...');
        // Call BULK decrypt API for ALL expeditions at once
        setLoading(true);
        setError(null);

        try {
          const { bramblerService } = await import('@/services/api/bramblerService');

          console.log('[useBramblerDecryption] Decrypting ALL data using bulk decrypt API');

          // Decrypt ALL pirates and items across ALL expeditions in one API call
          const { pirate_mappings, item_mappings } = await bramblerService.decryptAll(state.decryptionKey);

          const totalDecryptedPirates = Object.keys(pirate_mappings).length;
          const totalDecryptedItems = Object.keys(item_mappings).length;

          console.log(`[useBramblerDecryption] Total decrypted: ${totalDecryptedPirates} pirates, ${totalDecryptedItems} items`);

          setState(prev => ({
            ...prev,
            showRealNames: true,
            decryptedMappings: pirate_mappings,
            decryptedItemMappings: item_mappings,
          }));

          setLoading(false);
          setError(null);
          hapticFeedback('medium');
          console.log(`[useBramblerDecryption] Successfully decrypted and cached ${totalDecryptedPirates} pirates and ${totalDecryptedItems} items`);
        } catch (error: any) {
          console.error('[useBramblerDecryption] Decryption failed:', error);
          setLoading(false);
          setError(error?.message || 'Failed to decrypt names. Please check your master key and try again.');
        }
      } else {
        // Just toggle back to pirate names (no API call needed)
        console.log('[useBramblerDecryption] Hiding real names (instant toggle)');
        hapticFeedback('light');
        setState(prev => ({ ...prev, showRealNames: false }));
        setError(null);
      }
    },

    getMasterKey: async (isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void) => {
      if (!isOwner) return;

      hapticFeedback('light');
      setLoading(true);
      setError(null);

      try {
        const { bramblerService } = await import('@/services/api/bramblerService');

        console.log('[useBramblerDecryption] Fetching user master key from API');

        // Get the user's master key (works for ALL expeditions)
        const masterKey = await bramblerService.getUserMasterKey();

        console.log('[useBramblerDecryption] Master key retrieved, length:', masterKey.length);

        setState(prev => ({ ...prev, decryptionKey: masterKey }));
        setLoading(false);
        setError(null);

        // Show success message
        showAlert('Master key loaded! This key works for ALL your expeditions.');
      } catch (error: any) {
        console.error('[useBramblerDecryption] Failed to get master key:', error);
        setLoading(false);
        setError('Failed to retrieve master key. Make sure you are an owner.');
      }
    },

    saveMasterKey: async (isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void) => {
      if (!isOwner || !state.decryptionKey.trim()) {
        setError('Please enter a master key first');
        return;
      }

      hapticFeedback('medium');
      setLoading(true);
      setError(null);

      try {
        const result = await masterKeyStorage.saveMasterKey(state.decryptionKey);

        if (result.success) {
          setLoading(false);
          setError(null);

          const storageType = result.source === 'telegram_cloud' ? 'Telegram Cloud Storage' : 'Local Storage';
          hapticFeedback('success');

          showAlert(`Master key saved to ${storageType}! It will auto-load next time you visit.`);
        } else {
          throw new Error(result.error || 'Failed to save key');
        }
      } catch (error: any) {
        console.error('[useBramblerDecryption] Failed to save master key:', error);
        setLoading(false);
        setError(error?.message || 'Failed to save master key. Please try again.');
        hapticFeedback('error');
      }
    },

    clearSavedKey: async (isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void) => {
      if (!isOwner) return;

      // Confirm before clearing
      const confirmed = await showConfirm('Are you sure you want to remove your saved master key? You can always save it again later.');

      if (!confirmed) return;

      hapticFeedback('medium');
      setLoading(true);
      setError(null);

      try {
        const result = await masterKeyStorage.clearMasterKey();

        if (result.success) {
          setState(prev => ({
            ...prev,
            decryptionKey: '', // Clear from UI too
            showRealNames: false, // Hide real names
            decryptedMappings: {},
            decryptedItemMappings: {},
            individualToggles: {},
          }));

          setLoading(false);
          setError(null);
          hapticFeedback('success');

          showAlert(`Master key cleared from ${result.clearedFrom.join(' and ')}!`);
        } else {
          throw new Error('Failed to clear saved key');
        }
      } catch (error: any) {
        console.error('[useBramblerDecryption] Failed to clear saved key:', error);
        setLoading(false);
        setError(error?.message || 'Failed to clear saved key. Please try again.');
        hapticFeedback('error');
      }
    },

    toggleIndividualName: async (pirateId: number, isOwner: boolean, setLoading: (loading: boolean) => void, setError: (error: string | null) => void, e?: React.MouseEvent) => {
      // Prevent event propagation
      e?.preventDefault();
      e?.stopPropagation();

      console.log('[useBramblerDecryption] Toggle individual name for pirate ID:', pirateId);

      if (!isOwner) {
        console.warn('[useBramblerDecryption] Cannot toggle - not owner');
        return;
      }

      // If no decrypted mappings yet, we need to decrypt first
      if (Object.keys(state.decryptedMappings).length === 0) {
        console.log('[useBramblerDecryption] No decrypted mappings - need to decrypt first');

        if (!state.decryptionKey.trim()) {
          setError('Please enter your master key first to view individual names');
          return;
        }

        // Decrypt all names first
        setLoading(true);
        setError(null);

        try {
          const { bramblerService } = await import('@/services/api/bramblerService');

          console.log('[useBramblerDecryption] Decrypting ALL data for individual toggle');

          const { pirate_mappings, item_mappings } = await bramblerService.decryptAll(state.decryptionKey);

          console.log(`[useBramblerDecryption] Decrypted ${Object.keys(pirate_mappings).length} pirates, ${Object.keys(item_mappings).length} items`);

          setState(prev => ({
            ...prev,
            decryptedMappings: pirate_mappings,
            decryptedItemMappings: item_mappings,
            individualToggles: {
              ...prev.individualToggles,
              [pirateId]: true // Show this specific pirate
            },
          }));

          setLoading(false);
          setError(null);
          hapticFeedback('medium');
        } catch (error: any) {
          console.error('[useBramblerDecryption] Decryption failed:', error);
          setLoading(false);
          setError(error?.message || 'Failed to decrypt. Please check your master key.');
        }
      } else {
        // Already decrypted, just toggle the individual view
        hapticFeedback('light');
        setState(prev => ({
          ...prev,
          individualToggles: {
            ...prev.individualToggles,
            [pirateId]: !prev.individualToggles[pirateId]
          }
        }));

        console.log('[useBramblerDecryption] Toggle completed for pirate ID:', pirateId);
      }
    }
  };

  return [state, actions];
};
