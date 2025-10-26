/**
 * Master Key Context
 *
 * Provides app-wide access to the user's master key for decryption operations.
 * This context allows components throughout the app to access and manage the master key
 * without prop drilling.
 *
 * Features:
 * - Auto-loads saved master key on app initialization
 * - Provides methods to save, load, and clear the master key
 * - Tracks key source (Telegram Cloud Storage vs localStorage)
 * - Provides loading states and error handling
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { masterKeyStorage, type MasterKeyMetadata } from '@/services/masterKeyStorage';

interface MasterKeyContextValue {
  // State
  masterKey: string | null;
  isLoading: boolean;
  error: string | null;
  metadata: Omit<MasterKeyMetadata, 'key'> | null;
  hasSavedKey: boolean;

  // Actions
  setMasterKey: (key: string) => void;
  saveMasterKey: (key: string) => Promise<{ success: boolean; source: 'telegram_cloud' | 'local_storage'; error?: string }>;
  loadMasterKey: () => Promise<void>;
  clearMasterKey: () => Promise<void>;
  fetchFromAPI: () => Promise<string>;
}

const MasterKeyContext = createContext<MasterKeyContextValue | undefined>(undefined);

export const useMasterKey = () => {
  const context = useContext(MasterKeyContext);
  if (!context) {
    throw new Error('useMasterKey must be used within MasterKeyProvider');
  }
  return context;
};

interface MasterKeyProviderProps {
  children: React.ReactNode;
  autoLoad?: boolean; // Auto-load saved key on mount
}

export const MasterKeyProvider: React.FC<MasterKeyProviderProps> = ({ children, autoLoad = true }) => {
  const [masterKey, setMasterKeyState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<Omit<MasterKeyMetadata, 'key'> | null>(null);
  const [hasSavedKey, setHasSavedKey] = useState(false);

  // Auto-load saved master key on mount
  useEffect(() => {
    if (autoLoad) {
      loadMasterKey();
    }
  }, [autoLoad]);

  const setMasterKey = useCallback((key: string) => {
    setMasterKeyState(key);
    setError(null);
  }, []);

  const saveMasterKey = useCallback(async (key: string) => {
    if (!key || key.trim().length === 0) {
      setError('Master key cannot be empty');
      return {
        success: false,
        source: 'local_storage' as const,
        error: 'Master key cannot be empty'
      };
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await masterKeyStorage.saveMasterKey(key);

      if (result.success) {
        setMasterKeyState(key);
        setHasSavedKey(true);

        // Update metadata
        const newMetadata = await masterKeyStorage.getMetadata();
        setMetadata(newMetadata);

        console.log('[MasterKeyContext] Successfully saved master key');
      } else {
        setError(result.error || 'Failed to save master key');
      }

      return result;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      console.error('[MasterKeyContext] Error saving master key:', err);
      return {
        success: false,
        source: 'local_storage' as const,
        error: errorMsg
      };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadMasterKey = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const keyData = await masterKeyStorage.loadMasterKey();

      if (keyData && keyData.key) {
        setMasterKeyState(keyData.key);
        setHasSavedKey(true);
        setMetadata({
          savedAt: keyData.savedAt,
          version: keyData.version,
          source: keyData.source
        });

        console.log(`[MasterKeyContext] Loaded master key from ${keyData.source}`);
      } else {
        setMasterKeyState(null);
        setHasSavedKey(false);
        setMetadata(null);
        console.log('[MasterKeyContext] No saved master key found');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load master key';
      setError(errorMsg);
      console.error('[MasterKeyContext] Error loading master key:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMasterKey = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await masterKeyStorage.clearMasterKey();

      if (result.success) {
        setMasterKeyState(null);
        setHasSavedKey(false);
        setMetadata(null);
        console.log('[MasterKeyContext] Cleared master key');
      } else {
        throw new Error('Failed to clear master key');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to clear master key';
      setError(errorMsg);
      console.error('[MasterKeyContext] Error clearing master key:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchFromAPI = useCallback(async (): Promise<string> => {
    setIsLoading(true);
    setError(null);

    try {
      const { bramblerService } = await import('@/services/api/bramblerService');

      console.log('[MasterKeyContext] Fetching master key from API');

      const apiKey = await bramblerService.getUserMasterKey();

      if (!apiKey || apiKey.trim().length === 0) {
        throw new Error('Received empty master key from API');
      }

      setMasterKeyState(apiKey);
      console.log('[MasterKeyContext] Successfully fetched master key from API');

      return apiKey;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch master key from API';
      setError(errorMsg);
      console.error('[MasterKeyContext] Error fetching master key:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const value: MasterKeyContextValue = {
    masterKey,
    isLoading,
    error,
    metadata,
    hasSavedKey,
    setMasterKey,
    saveMasterKey,
    loadMasterKey,
    clearMasterKey,
    fetchFromAPI
  };

  return <MasterKeyContext.Provider value={value}>{children}</MasterKeyContext.Provider>;
};

export { MasterKeyContext };
