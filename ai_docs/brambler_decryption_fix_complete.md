# Brambler Decryption Fix - Complete Solution

## Problem Summary

When attempting to decrypt pirate names in the Brambler Manager webapp, users were seeing:
- "Failed to decrypt names" error message
- Backend logs showing "Invalid owner key format" errors
- Pirate names remained encrypted even after entering a decryption key

## Root Causes Identified

### 1. Missing owner_key in Expedition Queries
**File**: `services/expedition_service.py:98`
- The `get_expedition_by_id()` method wasn't selecting the `owner_key` column
- This caused the expedition object to have `owner_key = None`
- Backend couldn't retrieve the stored encryption key

### 2. Expedition Model Incompatibility
**File**: `models/expedition.py:67-81`
- The `Expedition` dataclass didn't have an `owner_key` field
- The `from_db_row()` method only handled 7 fields, not 8
- When owner_key was added to queries, the model couldn't parse it

### 3. TypeScript Interface Mismatch
**File**: `webapp/src/types/expedition.ts:119-121`
- The `BramblerDecryptRequest` interface had an extra `encrypted_mapping` field
- Backend API expected only `owner_key`
- API calls were failing due to wrong request format

### 4. User Confusion About Which Key to Use
**Critical Issue**: Users were trying to use the **expedition's owner_key** instead of their **USER MASTER KEY**

The system uses:
- **Expedition owner_key**: Stored in database, used internally for encryption
- **User master key**: Deterministic key based on chat_id, what users need to decrypt

## Complete Solution Implemented

### Backend Fixes

#### 1. Updated Expedition Service Query
**File**: `services/expedition_service.py:98`
```python
query = """
    SELECT id, name, owner_chat_id, status, deadline, created_at, completed_at, owner_key
    FROM expeditions
    WHERE id = %s
"""
```

#### 2. Enhanced Expedition Model
**File**: `models/expedition.py:55-90`
```python
@dataclass
class Expedition:
    id: int
    name: str
    owner_chat_id: int
    status: ExpeditionStatus
    deadline: Optional[datetime] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner_key: Optional[str] = None  # NEW FIELD

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Expedition':
        if not row:
            return None

        # Handle both 7-field (old) and 8-field (new with owner_key) rows
        if len(row) == 8:
            id_, name, owner_chat_id, status, deadline, created_at, completed_at, owner_key = row
        else:
            # Backward compatibility
            id_, name, owner_chat_id, status, deadline, created_at, completed_at = row
            owner_key = None

        return cls(
            id=id_,
            name=name,
            owner_chat_id=owner_chat_id,
            status=ExpeditionStatus.from_string(status),
            deadline=deadline,
            created_at=created_at,
            completed_at=completed_at,
            owner_key=owner_key
        )
```

### Frontend Fixes

#### 1. Fixed TypeScript Interface
**File**: `webapp/src/types/expedition.ts:119-121`
```typescript
export interface BramblerDecryptRequest {
  owner_key: string;  // Removed encrypted_mapping field
}
```

#### 2. Added Master Key Fetch Functionality
**File**: `webapp/src/services/api/bramblerService.ts:75-88`
```typescript
/**
 * Get user's master key (works for all their expeditions)
 */
async getUserMasterKey(): Promise<string> {
  const response = await httpClient.get<{
    success: boolean;
    master_key: string;
    owner_chat_id: number;
    created_at: string;
    key_version: number;
    message: string;
  }>(`${this.basePath}/master-key`);
  return response.data.master_key;
}
```

#### 3. Enhanced UI with Auto-Load Button
**File**: `webapp/src/pages/BramblerManager.tsx:617-636`
```typescript
{state.isOwner && (
  <KeySection>
    <Key size={20} color={pirateColors.muted} />
    <KeyInput
      type="password"
      placeholder="Enter your master key..."
      value={state.decryptionKey}
      onChange={(e) => handleKeyChange(e.target.value)}
      title="Use your USER MASTER KEY (not the expedition key). Click 'Load My Key' to fetch it automatically."
    />
    <PirateButton
      variant="outline"
      size="sm"
      onClick={handleGetMasterKey}
      disabled={state.loading}
    >
      Load My Key
    </PirateButton>
  </KeySection>
)}
```

#### 4. Added handleGetMasterKey Function
**File**: `webapp/src/pages/BramblerManager.tsx:425-460`
```typescript
const handleGetMasterKey = async () => {
  if (!state.isOwner) return;

  hapticFeedback('light');
  setState(prev => ({ ...prev, loading: true, error: null }));

  try {
    const { bramblerService } = await import('@/services/api/bramblerService');

    console.log('[BramblerManager] Fetching user master key from API');

    // Call the master-key API endpoint (gets user's master key for ALL expeditions)
    const masterKey = await bramblerService.getUserMasterKey();

    console.log('[BramblerManager] Master key retrieved, length:', masterKey.length);

    setState(prev => ({
      ...prev,
      decryptionKey: masterKey,
      loading: false,
      error: null
    }));

    // Show success message
    await import('@/utils/telegram').then(({ showAlert }) => {
      showAlert('Master key loaded! Click "Show Real Names" to decrypt.');
    });
  } catch (error: any) {
    console.error('[BramblerManager] Failed to get master key:', error);
    setState(prev => ({
      ...prev,
      loading: false,
      error: 'Failed to retrieve master key. Make sure you are the expedition owner.'
    }));
  }
};
```

#### 5. Fixed Button Reload Issue
**File**: `webapp/src/components/ui/PirateButton.tsx:192`
```typescript
<ButtonBase
  type="button"  // Prevents form submission behavior
  ...
>
```

#### 6. Enhanced Error Logging
**File**: `webapp/src/pages/BramblerManager.tsx:396-408`
- Added detailed console logging for debugging
- Better error messages showing actual API errors

## How It Works Now

### User Flow

1. **Navigate to Brambler Manager** (`/brambler`)
2. **Click "Load My Key" button**
   - Calls `GET /api/brambler/master-key`
   - Backend generates/retrieves user's master key based on chat_id
   - Key is deterministic - same chat_id always generates same key
   - Key is automatically filled into the input field
3. **Click "Show Real Names"**
   - Calls `POST /api/brambler/decrypt/{expedition_id}` with master key
   - Backend decrypts all pirate names
   - Returns mappings: `{"Capitão Barbas Negras": "John Doe"}`
   - Frontend displays real names!

### API Flow

```
Frontend                          Backend
--------                          -------
1. Click "Load My Key"
   GET /api/brambler/master-key
   Headers: X-Chat-ID: 5094426438
                                  -> Validate owner permission
                                  -> Check user_master_keys table
                                  -> If exists: return stored key
                                  -> If not: generate_user_master_key(chat_id)
                                  -> Store in database
   <- { master_key: "mWb1d2SV..." }

2. Click "Show Real Names"
   POST /api/brambler/decrypt/7
   Headers: X-Chat-ID: 5094426438
   Body: { owner_key: "mWb1d2SV..." }
                                  -> Validate owner permission
                                  -> Get expedition with owner_key
                                  -> Decrypt all pirate names
                                  -> Return mappings
   <- { mappings_dict: { "pirate": "real" } }

3. Display real names
```

## Key Concepts

### User Master Key
- **What**: A single, deterministic encryption key for each user
- **Based On**: User's chat_id
- **Used For**: Decrypting pirate names in ALL expeditions owned by the user
- **Generation**: `generate_user_master_key(chat_id)` - always returns same key for same chat_id
- **Storage**: `user_master_keys` table
- **Format**: 88-character base64-encoded string

### Expedition Owner Key
- **What**: Per-expedition encryption key stored in database
- **Used For**: Backend encryption/decryption operations
- **Not For**: User input - users should never enter this directly
- **Storage**: `expeditions.owner_key` column

## Testing

### Get Your Master Key

**For chat_id 5094426438 (Morty - dev user)**:
```
Master Key: mWb1d2SV0p40ug4skGTPiAOy9rk-RpLBbpWyVgcqFEAL6c5gRIaE2t061K7n3K724s-cN5BwkvTnjUrxt6TcHQ==
```

**Via API**:
```bash
curl -X GET http://localhost:5000/api/brambler/master-key \
  -H "X-Chat-ID: 5094426438"
```

**Via Python**:
```python
from utils.encryption import get_encryption_service

encryption = get_encryption_service()
master_key = encryption.generate_user_master_key(5094426438)
print(f"Master Key: {master_key}")
```

### Test Decryption

1. Start Flask app
2. Open webapp in browser
3. Navigate to `/brambler`
4. Click "Load My Key" button
5. Verify key is loaded in input field
6. Click "Show Real Names"
7. Verify pirate names change to real names

## Files Modified

### Backend
1. `services/expedition_service.py` - Added owner_key to SQL query
2. `models/expedition.py` - Added owner_key field and backward compatibility
3. `utils/encryption.py` - Already had all needed functionality

### Frontend
1. `webapp/src/types/expedition.ts` - Fixed BramblerDecryptRequest interface
2. `webapp/src/services/api/bramblerService.ts` - Added getUserMasterKey method
3. `webapp/src/pages/BramblerManager.tsx` - Added auto-load functionality and better UX
4. `webapp/src/components/ui/PirateButton.tsx` - Fixed form submission issue

### Documentation
1. `ai_docs/brambler_decryption_fix.md` - Initial fix documentation
2. `ai_docs/brambler_decryption_fix_complete.md` - This comprehensive guide
3. `GET_YOUR_MASTER_KEY.md` - Already existed with instructions

## Security Considerations

1. **Master Key Generation**: Deterministic but secure (PBKDF2 with 100k iterations)
2. **API Access**: Owner-only permission required
3. **Frontend Storage**: Keys only in React state (memory), never persisted
4. **Transmission**: HTTPS required in production
5. **Database Storage**: Master keys stored in `user_master_keys` table with timestamps

## Troubleshooting

### "Failed to decrypt names"
- **Solution**: Click "Load My Key" first to get your master key
- **Or**: Check browser console for detailed error messages

### "Invalid owner key format"
- **Cause**: User entered expedition owner_key instead of master key
- **Solution**: Use "Load My Key" button or get key from `/api/brambler/master-key`

### "Owner permission required"
- **Cause**: User is not marked as owner in database
- **Solution**: Check `Usuarios` table - ensure user has `nivel = 'owner'`

### "Failed to retrieve master key"
- **Cause**: Authentication headers not sent
- **Solution**: Verify `X-Chat-ID` header is being sent by httpClient

## Related Documentation

- [Brambler Full Encryption Guide](brambler_full_encryption_guide.md)
- [User Master Key Guide](user_master_key_guide.md)
- [Get Your Master Key](../GET_YOUR_MASTER_KEY.md)
- [Owner Key Migration](owner_key_migration_completed.md)

## Status

✅ **COMPLETE** - All fixes implemented and tested
✅ Backend queries include owner_key
✅ Frontend can auto-load master key
✅ Decryption works with correct key
✅ UX improved with helpful buttons and tooltips
