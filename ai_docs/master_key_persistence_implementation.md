# Master Key Persistence Implementation

## Overview
This document describes the implementation of Master Key persistence for the Brambler system in the Telegram Mini App. The solution allows users to save their Master Key securely and have it auto-loaded on subsequent visits, eliminating the need to manually fetch it each time.

## Implementation Date
2025-10-25

## Architecture

### 1. Storage Service Layer
**File**: `webapp/src/services/masterKeyStorage.ts`

A dedicated service that handles all Master Key storage operations with dual-storage strategy:

#### Primary Storage: Telegram Cloud Storage
- **Advantages**:
  - Encrypted in transit by Telegram
  - Synced across all user's devices
  - Persistent even if browser cache is cleared
  - Telegram-native security

- **API Methods Used**:
  - `CloudStorage.setItem(key, value, callback)`
  - `CloudStorage.getItem(key, callback)`

#### Fallback Storage: localStorage
- **When Used**:
  - Telegram Cloud Storage unavailable
  - Development environment
  - Cloud Storage API call fails

- **Security Note**:
  - Browser-based storage
  - Cleared when browser cache is cleared
  - Not synced across devices

#### Service API

```typescript
class MasterKeyStorageService {
  // Save master key with automatic fallback
  async saveMasterKey(masterKey: string): Promise<{
    success: boolean;
    source: 'telegram_cloud' | 'local_storage';
    error?: string;
  }>

  // Load master key from any available storage
  async loadMasterKey(): Promise<MasterKeyMetadata | null>

  // Check if master key exists
  async hasMasterKey(): Promise<boolean>

  // Clear master key from all storage
  async clearMasterKey(): Promise<{
    success: boolean;
    clearedFrom: string[];
  }>

  // Migrate from localStorage to Telegram Cloud
  async migrateToCloudStorage(): Promise<{
    success: boolean;
    migrated: boolean;
  }>

  // Get metadata without exposing the key
  async getMetadata(): Promise<Omit<MasterKeyMetadata, 'key'> | null>
}
```

#### Storage Keys
- `user_master_key` - The encrypted master key
- `user_master_key_timestamp` - When the key was saved
- `user_master_key_version` - Key version for future rotation support

### 2. React Context Layer
**File**: `webapp/src/contexts/MasterKeyContext.tsx`

Provides app-wide access to Master Key management:

```typescript
interface MasterKeyContextValue {
  // State
  masterKey: string | null;
  isLoading: boolean;
  error: string | null;
  metadata: Omit<MasterKeyMetadata, 'key'> | null;
  hasSavedKey: boolean;

  // Actions
  setMasterKey: (key: string) => void;
  saveMasterKey: (key: string) => Promise<SaveResult>;
  loadMasterKey: () => Promise<void>;
  clearMasterKey: () => Promise<void>;
  fetchFromAPI: () => Promise<string>;
}
```

**Usage in Components**:
```typescript
import { useMasterKey } from '@/contexts/MasterKeyContext';

function MyComponent() {
  const { masterKey, saveMasterKey, loadMasterKey } = useMasterKey();

  // Use master key for decryption
  // Save/load as needed
}
```

### 3. UI Integration
**File**: `webapp/src/pages/BramblerManager.tsx`

#### Auto-Load on Page Load
```typescript
useEffect(() => {
  // ... load expeditions, pirates, items ...

  // AUTO-LOAD SAVED MASTER KEY
  const keyMetadata = await masterKeyStorage.loadMasterKey();
  if (keyMetadata && keyMetadata.key) {
    setState(prev => ({
      ...prev,
      decryptionKey: keyMetadata.key
    }));

    showAlert(`Master key auto-loaded from ${keySource}!`);
  }
}, []);
```

#### New UI Actions

1. **Load My Key Button**
   - Fetches master key from API (`/api/brambler/master-key`)
   - Populates the key input field
   - Does NOT automatically save to storage

2. **Save Key Button** (NEW)
   - Saves current key to Telegram Cloud Storage (or localStorage)
   - Shows confirmation with storage location
   - Disabled if no key is entered
   - Icon: Save icon

3. **Clear Saved Button** (NEW)
   - Clears saved key from all storage locations
   - Shows confirmation dialog before clearing
   - Clears decryption state and hides real names
   - Icon: Trash icon

#### User Flow

```
┌─────────────────────────────────────────────────────────────┐
│ User Opens Brambler Page                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Check for Saved Master Key     │
         └────────────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         │                                  │
         ▼                                  ▼
┌─────────────────┐              ┌─────────────────┐
│ Key Found       │              │ No Key Found    │
│ Auto-populate   │              │ Show empty      │
│ Show alert      │              │ input field     │
└─────────────────┘              └─────────────────┘
         │                                  │
         └────────────────┬─────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ User Options:                  │
         │ 1. Load My Key (from API)      │
         │ 2. Enter manually              │
         │ 3. Use auto-loaded key         │
         └────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ User Clicks "Save Key"         │
         │ → Saves to Telegram Cloud      │
         │ → Falls back to localStorage   │
         │ → Shows confirmation           │
         └────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Next Visit:                    │
         │ Key auto-loads automatically   │
         │ No need to fetch from API      │
         └────────────────────────────────┘
```

## Security Considerations

### 1. Storage Security
- **Telegram Cloud Storage**: Encrypted in transit, Telegram-managed
- **localStorage**: Browser-based, vulnerable to XSS if site is compromised
- **No server-side persistence**: Keys are never sent to or stored on our backend

### 2. Key Exposure
- Master Key is only displayed in password-protected input field
- Real names only shown when user explicitly clicks "Show Real Names"
- User can clear saved key at any time
- Auto-load shows notification to user (transparency)

### 3. Access Control
- Only users with "owner" permission can access master key features
- API endpoint `/api/brambler/master-key` validates ownership
- Frontend disables all key management UI for non-owners

### 4. Data Lifecycle
```
API Fetch → User Storage → Auto-Load → Decryption → Clear (optional)
    ↓            ↓             ↓            ↓              ↓
Secure     Encrypted      Transparent   Temporary    Complete
```

## Future Enhancements

### 1. Key Rotation Support
- Version tracking already implemented (`master_key_version`)
- Future: Support multiple key versions
- Automatic migration to new keys

### 2. Biometric Protection
- Telegram Web App may support biometric authentication in future
- Add biometric confirmation before auto-loading key
- Require biometric for "Show Real Names"

### 3. Key Expiration
- Optional: Set expiration time for saved keys
- Auto-clear after N days of inactivity
- User notification before expiration

### 4. Cross-Device Sync Status
- Show which devices have the key saved
- Allow remote key revocation
- Sync status indicators

### 5. Backup & Recovery
- Encrypted key backup to user's Telegram "Saved Messages"
- QR code export for offline backup
- Recovery flow with security questions

## Testing Checklist

- [x] Save key to Telegram Cloud Storage
- [x] Save key to localStorage (fallback)
- [x] Auto-load saved key on page refresh
- [x] Clear saved key (all storage locations)
- [x] Fetch key from API
- [x] Manual key entry
- [x] Decryption with saved key
- [ ] Migration from localStorage to Cloud Storage
- [ ] Error handling for storage failures
- [ ] Multi-device sync testing

## Migration Notes

### For Existing Users
1. No breaking changes - existing functionality remains
2. Users with no saved key will see empty input field (as before)
3. Users can opt-in to save their key by clicking "Save Key"
4. First-time save will prompt confirmation

### For New Users
1. Click "Load My Key" to fetch from API
2. Click "Save Key" to persist for future visits
3. On next visit, key auto-loads automatically
4. Can clear saved key at any time

## Troubleshooting

### Key Not Auto-Loading
**Check**:
1. Browser console for errors
2. Telegram Cloud Storage availability
3. localStorage quota not exceeded
4. Correct permission level (owner)

**Solution**:
- Click "Load My Key" to re-fetch
- Click "Save Key" again
- Check browser storage settings

### Storage Fallback
**When Telegram Cloud Storage fails**:
- Automatically falls back to localStorage
- User is notified of storage location
- No data loss

### Clear Not Working
**If saved key persists**:
1. Check browser console for errors
2. Manually clear localStorage: `localStorage.clear()`
3. Clear Telegram Cloud Storage from Telegram settings
4. Re-login to Mini App

## Related Files
- `webapp/src/services/masterKeyStorage.ts` - Storage service
- `webapp/src/contexts/MasterKeyContext.tsx` - React context
- `webapp/src/pages/BramblerManager.tsx` - UI integration
- `webapp/src/utils/telegram.ts` - Telegram Web App utilities
- `ai_docs/master_key_system_complete.md` - Master Key system overview
- `ai_docs/brambler_full_encryption_guide.md` - Brambler encryption guide

## Conclusion

The Master Key Persistence implementation provides a seamless user experience while maintaining security best practices. By leveraging Telegram Cloud Storage with localStorage fallback, users can securely save their master keys and have them automatically available on subsequent visits, eliminating repetitive API calls and improving the overall UX.

The dual-storage strategy ensures reliability across different environments while the React Context provides clean, app-wide access to master key functionality.
