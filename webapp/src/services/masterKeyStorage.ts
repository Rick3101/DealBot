/**
 * Master Key Storage Service
 *
 * Provides secure storage for the user's Master Key using:
 * 1. Telegram Cloud Storage (preferred) - encrypted and synced across devices
 * 2. localStorage (fallback) - browser-based storage
 *
 * Security considerations:
 * - Master key is stored encrypted in transit via Telegram Cloud Storage
 * - Key is only stored after explicit user consent
 * - Provides clear/logout functionality
 * - Auto-loads on app initialization (if previously saved)
 */

import { telegramWebApp } from '@/utils/telegram';

const MASTER_KEY_STORAGE_KEY = 'user_master_key';
const MASTER_KEY_TIMESTAMP_KEY = 'user_master_key_timestamp';
const MASTER_KEY_VERSION_KEY = 'user_master_key_version';

export interface MasterKeyMetadata {
  key: string;
  savedAt: string;
  version: number;
  source: 'telegram_cloud' | 'local_storage';
}

class MasterKeyStorageService {
  /**
   * Save master key to storage
   * Prioritizes Telegram Cloud Storage, falls back to localStorage
   */
  async saveMasterKey(masterKey: string): Promise<{ success: boolean; source: 'telegram_cloud' | 'local_storage'; error?: string }> {
    if (!masterKey || masterKey.trim().length === 0) {
      return {
        success: false,
        source: 'local_storage',
        error: 'Master key cannot be empty'
      };
    }

    const timestamp = new Date().toISOString();
    const version = 1; // For future key rotation support

    try {
      // Determine if Cloud Storage is supported
      const cloudStorageSupported = telegramWebApp.isCloudStorageSupported();
      console.log('[MasterKeyStorage] Cloud Storage supported:', cloudStorageSupported);

      // Try Telegram Cloud Storage first (preferred) - but it will auto-fallback to localStorage
      if (telegramWebApp.isAvailable()) {
        console.log('[MasterKeyStorage] Saving to storage (Cloud Storage will be tried first)');

        const saveSuccess = await telegramWebApp.setCloudStorage(MASTER_KEY_STORAGE_KEY, masterKey);

        if (saveSuccess) {
          // Save metadata
          await telegramWebApp.setCloudStorage(MASTER_KEY_TIMESTAMP_KEY, timestamp);
          await telegramWebApp.setCloudStorage(MASTER_KEY_VERSION_KEY, version.toString());

          // Determine which storage was actually used based on support
          const actualSource = cloudStorageSupported ? 'telegram_cloud' : 'local_storage';
          console.log(`[MasterKeyStorage] Successfully saved to ${actualSource}`);

          return {
            success: true,
            source: actualSource
          };
        }
      }

      // Manual fallback to localStorage if Telegram not available
      localStorage.setItem(MASTER_KEY_STORAGE_KEY, masterKey);
      localStorage.setItem(MASTER_KEY_TIMESTAMP_KEY, timestamp);
      localStorage.setItem(MASTER_KEY_VERSION_KEY, version.toString());

      console.log('[MasterKeyStorage] Successfully saved to localStorage');
      return {
        success: true,
        source: 'local_storage'
      };
    } catch (error) {
      console.error('[MasterKeyStorage] Error saving master key:', error);
      return {
        success: false,
        source: 'local_storage',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Load master key from storage
   * Checks Telegram Cloud Storage first, then falls back to localStorage
   */
  async loadMasterKey(): Promise<MasterKeyMetadata | null> {
    try {
      // Try Telegram Cloud Storage first
      if (telegramWebApp.isAvailable()) {
        console.log('[MasterKeyStorage] Attempting to load from Telegram Cloud Storage');

        const cloudKey = await telegramWebApp.getCloudStorage(MASTER_KEY_STORAGE_KEY);

        if (cloudKey && cloudKey.trim().length > 0) {
          const timestamp = await telegramWebApp.getCloudStorage(MASTER_KEY_TIMESTAMP_KEY);
          const version = await telegramWebApp.getCloudStorage(MASTER_KEY_VERSION_KEY);

          console.log('[MasterKeyStorage] Successfully loaded from Telegram Cloud Storage');
          return {
            key: cloudKey,
            savedAt: timestamp || new Date().toISOString(),
            version: version ? parseInt(version, 10) : 1,
            source: 'telegram_cloud'
          };
        }

        console.log('[MasterKeyStorage] No key found in Telegram Cloud Storage, checking localStorage');
      }

      // Fallback to localStorage
      const localKey = localStorage.getItem(MASTER_KEY_STORAGE_KEY);

      if (localKey && localKey.trim().length > 0) {
        const timestamp = localStorage.getItem(MASTER_KEY_TIMESTAMP_KEY);
        const version = localStorage.getItem(MASTER_KEY_VERSION_KEY);

        console.log('[MasterKeyStorage] Successfully loaded from localStorage');
        return {
          key: localKey,
          savedAt: timestamp || new Date().toISOString(),
          version: version ? parseInt(version, 10) : 1,
          source: 'local_storage'
        };
      }

      console.log('[MasterKeyStorage] No master key found in any storage');
      return null;
    } catch (error) {
      console.error('[MasterKeyStorage] Error loading master key:', error);
      return null;
    }
  }

  /**
   * Check if master key exists in storage
   */
  async hasMasterKey(): Promise<boolean> {
    const metadata = await this.loadMasterKey();
    return metadata !== null && metadata.key.trim().length > 0;
  }

  /**
   * Clear master key from all storage locations
   * Useful for logout or security purposes
   */
  async clearMasterKey(): Promise<{ success: boolean; clearedFrom: string[] }> {
    const clearedFrom: string[] = [];

    try {
      // Clear from Telegram Cloud Storage
      if (telegramWebApp.isAvailable()) {
        await telegramWebApp.setCloudStorage(MASTER_KEY_STORAGE_KEY, '');
        await telegramWebApp.setCloudStorage(MASTER_KEY_TIMESTAMP_KEY, '');
        await telegramWebApp.setCloudStorage(MASTER_KEY_VERSION_KEY, '');
        clearedFrom.push('telegram_cloud');
        console.log('[MasterKeyStorage] Cleared from Telegram Cloud Storage');
      }

      // Clear from localStorage
      localStorage.removeItem(MASTER_KEY_STORAGE_KEY);
      localStorage.removeItem(MASTER_KEY_TIMESTAMP_KEY);
      localStorage.removeItem(MASTER_KEY_VERSION_KEY);
      clearedFrom.push('local_storage');
      console.log('[MasterKeyStorage] Cleared from localStorage');

      return {
        success: true,
        clearedFrom
      };
    } catch (error) {
      console.error('[MasterKeyStorage] Error clearing master key:', error);
      return {
        success: false,
        clearedFrom
      };
    }
  }

  /**
   * Migrate key from localStorage to Telegram Cloud Storage
   * Useful when Telegram Cloud Storage becomes available
   */
  async migrateToCloudStorage(): Promise<{ success: boolean; migrated: boolean }> {
    if (!telegramWebApp.isAvailable()) {
      return {
        success: false,
        migrated: false
      };
    }

    try {
      // Check if key exists in localStorage
      const localKey = localStorage.getItem(MASTER_KEY_STORAGE_KEY);

      if (!localKey || localKey.trim().length === 0) {
        console.log('[MasterKeyStorage] No key in localStorage to migrate');
        return {
          success: true,
          migrated: false
        };
      }

      // Check if already in cloud storage
      const cloudKey = await telegramWebApp.getCloudStorage(MASTER_KEY_STORAGE_KEY);

      if (cloudKey && cloudKey.trim().length > 0) {
        console.log('[MasterKeyStorage] Key already exists in Telegram Cloud Storage');
        return {
          success: true,
          migrated: false
        };
      }

      // Migrate to cloud storage
      const timestamp = localStorage.getItem(MASTER_KEY_TIMESTAMP_KEY) || new Date().toISOString();
      const version = localStorage.getItem(MASTER_KEY_VERSION_KEY) || '1';

      await telegramWebApp.setCloudStorage(MASTER_KEY_STORAGE_KEY, localKey);
      await telegramWebApp.setCloudStorage(MASTER_KEY_TIMESTAMP_KEY, timestamp);
      await telegramWebApp.setCloudStorage(MASTER_KEY_VERSION_KEY, version);

      console.log('[MasterKeyStorage] Successfully migrated key to Telegram Cloud Storage');
      return {
        success: true,
        migrated: true
      };
    } catch (error) {
      console.error('[MasterKeyStorage] Error migrating to cloud storage:', error);
      return {
        success: false,
        migrated: false
      };
    }
  }

  /**
   * Get metadata about stored key (without returning the key itself)
   */
  async getMetadata(): Promise<Omit<MasterKeyMetadata, 'key'> | null> {
    const fullMetadata = await this.loadMasterKey();

    if (!fullMetadata) {
      return null;
    }

    return {
      savedAt: fullMetadata.savedAt,
      version: fullMetadata.version,
      source: fullMetadata.source
    };
  }
}

// Export singleton instance
export const masterKeyStorage = new MasterKeyStorageService();

// Export class for testing
export { MasterKeyStorageService };
