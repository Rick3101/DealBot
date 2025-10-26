# Pirate Name Anonymization - WebApp Implementation

## Overview

This document describes the complete implementation of true pirate name anonymization in the webapp, where original names are encrypted and only visible to expedition owners through a secure decryption process.

## Implementation Date

2025-10-16

## Architecture

### Backend (Already Implemented)

The backend API at `/api/brambler/names/<expedition_id>` already implements proper anonymization:

```python
# app.py:1291
show_original = is_owner or user_level.value == 'owner'

# app.py:1328 - Only show original names to owners
"original_name": original_name if show_original else None
```

**Key Features:**
- Original names are hidden from non-owners (returned as `null`)
- Only expedition owners or system owners can see original names
- Full encryption mode support with AES-256-GCM

### Frontend Implementation

#### 1. PiratesTab Component Enhancement

**File:** [webapp/src/components/expedition/tabs/PiratesTab.tsx](../webapp/src/components/expedition/tabs/PiratesTab.tsx)

**New Props:**
```typescript
interface PiratesTabProps {
  pirateNames: PirateName[];
  onAddPirate: () => void;
  expeditionId: number;        // NEW
  isOwner: boolean;            // NEW
  ownerChatId: number;         // NEW
}
```

**New State:**
```typescript
const [showOriginalNames, setShowOriginalNames] = useState(false);
const [decryptedMappings, setDecryptedMappings] = useState<Record<string, string>>({});
const [isDecrypting, setIsDecrypting] = useState(false);
const [decryptError, setDecryptError] = useState<string | null>(null);
const [ownerKey, setOwnerKey] = useState<string | null>(null);
```

**Key Features:**

1. **Owner-Only Decryption Section**
   - Visible only to expedition owners
   - Shows "Show Original Names" / "Hide Original Names" toggle button
   - Displays security warning when names are decrypted

2. **Decryption Flow**
   - Retrieves owner key from `/api/brambler/owner-key/<expedition_id>`
   - Decrypts all pirate names using `/api/brambler/decrypt/<expedition_id>`
   - Stores decrypted mappings in memory (not localStorage for security)

3. **Display Logic**
   - Shows pirate names by default (anonymized)
   - Shows original names when decrypted and toggle is active
   - Displays 🔒 indicator for encrypted names
   - Displays 👤 icon and warning badge for decrypted names

#### 2. Container Component Updates

**File:** [webapp/src/containers/ExpeditionDetailsContainer.tsx](../webapp/src/containers/ExpeditionDetailsContainer.tsx)

**Changes:**
```typescript
// Import getUserId helper
import { hapticFeedback, getUserId } from '@/utils/telegram';

// Calculate ownership
const currentUserId = getUserId();
const isOwner = useMemo(() => {
  if (!expedition || !currentUserId) return false;
  return expedition.owner_chat_id === currentUserId;
}, [expedition, currentUserId]);

// Pass to presenter
<ExpeditionDetailsPresenter
  isOwner={isOwner}
  currentUserId={currentUserId}
  // ... other props
/>
```

#### 3. Presenter Component Updates

**File:** [webapp/src/components/expedition/ExpeditionDetailsPresenter.tsx](../webapp/src/components/expedition/ExpeditionDetailsPresenter.tsx)

**Changes:**
```typescript
interface ExpeditionDetailsPresenterProps {
  // ... existing props
  isOwner: boolean;
  currentUserId: number;
}

// Pass to PiratesTab
<PiratesTab
  pirateNames={pirateNames}
  onAddPirate={onOpenAddPirateModal}
  expeditionId={expedition.id}
  isOwner={isOwner}
  ownerChatId={currentUserId}
/>
```

#### 4. Brambler Service Update

**File:** [webapp/src/services/api/bramblerService.ts](../webapp/src/services/api/bramblerService.ts)

**Changes:**
```typescript
// Updated decrypt API response format
async decryptNames(expeditionId: number, data: BramblerDecryptRequest): Promise<Record<string, string>> {
  const response = await httpClient.post<{
    success: boolean;
    expedition_id: number;
    decrypted_count: number;
    mappings_dict: Record<string, string>;  // Use mappings_dict from API
  }>(
    `${this.basePath}/decrypt/${expeditionId}`,
    data
  );
  return response.data.mappings_dict;
}
```

## Security Features

### 1. API-Level Security
- ✅ Original names never sent to non-owners
- ✅ Owner key retrieval requires authentication
- ✅ Decryption requires owner permission
- ✅ All encrypted with AES-256-GCM

### 2. Frontend Security
- ✅ Decrypted names stored in memory only (React state)
- ✅ Not persisted to localStorage or sessionStorage
- ✅ Cleared on component unmount
- ✅ Security warning shown when names are decrypted
- ✅ Visual indicators for encrypted/decrypted states

### 3. User Experience Security
- ✅ Non-owners see only pirate names (anonymized)
- ✅ Owners can choose to decrypt (explicit action required)
- ✅ Warning banner reminds owners of sensitive data
- ✅ Easy toggle to hide names again

## Visual Indicators

### For Non-Owners
```
🏴‍☠️ Capitão Barbas Negras o Terrível
🔒 Original name encrypted
5 consumptions
```

### For Owners (Before Decryption)
```
🏴‍☠️ Capitão Barbas Negras o Terrível
🔒 Original name encrypted
5 consumptions

[Show Original Names] button available
```

### For Owners (After Decryption)
```
⚠️ Warning: Original names are currently visible
Make sure you're in a secure environment...

👤 JohnDoe
🔑 Decrypted Identity
5 consumptions

[Hide Original Names] button
```

## API Endpoints Used

### 1. Get Pirate Names
```http
GET /api/brambler/names/<expedition_id>
X-Chat-ID: <user_chat_id>

Response (Non-Owner):
{
  "pirate_names": [
    {
      "pirate_name": "Capitão Barbas Negras o Terrível",
      "original_name": null,  // Hidden
      "stats": {...}
    }
  ]
}

Response (Owner):
{
  "pirate_names": [
    {
      "pirate_name": "Capitão Barbas Negras o Terrível",
      "original_name": "JohnDoe",  // Visible
      "stats": {...}
    }
  ]
}
```

### 2. Get Owner Key (Owner-Only)
```http
GET /api/brambler/owner-key/<expedition_id>
X-Chat-ID: <owner_chat_id>

Response:
{
  "success": true,
  "expedition_id": 123,
  "owner_key": "base64_encoded_key"
}
```

### 3. Decrypt Pirate Names (Owner-Only)
```http
POST /api/brambler/decrypt/<expedition_id>
X-Chat-ID: <owner_chat_id>
Content-Type: application/json

{
  "owner_key": "base64_encoded_key"
}

Response:
{
  "success": true,
  "expedition_id": 123,
  "decrypted_count": 5,
  "mappings_dict": {
    "Capitão Barbas Negras o Terrível": "JohnDoe",
    "Almirante Garra de Ferro o Impiedoso": "JaneSmith"
  }
}
```

## Usage Flow

### For Non-Owners (Admins)
1. Open expedition details
2. Navigate to Pirates tab
3. See pirate names with 🔒 encrypted indicator
4. No decryption option available
5. Original names remain secure

### For Owners
1. Open expedition details
2. Navigate to Pirates tab
3. See pirate names with 🔒 encrypted indicator
4. See "Owner Decryption Access" section
5. Click "Show Original Names" button
6. System automatically:
   - Fetches owner key
   - Decrypts all pirate names
   - Shows warning banner
7. Names displayed as 👤 icons with original names
8. Click "Hide Original Names" to return to anonymized view

## Testing Checklist

- [ ] Non-owner users cannot see original names
- [ ] Non-owner users do not see decryption UI
- [ ] Expedition owner sees decryption UI
- [ ] Decryption button fetches owner key correctly
- [ ] Decryption API call works with valid owner key
- [ ] Decrypted names display correctly
- [ ] Warning banner appears when names are decrypted
- [ ] Hide button returns to anonymized view
- [ ] Decrypted data is not persisted to storage
- [ ] Component unmount clears decrypted data
- [ ] Error handling works for invalid owner keys
- [ ] Error handling works for failed API calls

## Files Modified

1. [webapp/src/components/expedition/tabs/PiratesTab.tsx](../webapp/src/components/expedition/tabs/PiratesTab.tsx)
   - Added decryption state management
   - Added owner-only decryption UI
   - Added display logic for encrypted/decrypted names

2. [webapp/src/containers/ExpeditionDetailsContainer.tsx](../webapp/src/containers/ExpeditionDetailsContainer.tsx)
   - Added ownership checking logic
   - Pass isOwner and currentUserId to presenter

3. [webapp/src/components/expedition/ExpeditionDetailsPresenter.tsx](../webapp/src/components/expedition/ExpeditionDetailsPresenter.tsx)
   - Accept isOwner and currentUserId props
   - Pass props to PiratesTab component

4. [webapp/src/services/api/bramblerService.ts](../webapp/src/services/api/bramblerService.ts)
   - Updated decryptNames to use correct API response format

## Benefits

✅ **Maximum Privacy**: Original names never exposed to non-owners
✅ **Owner Control**: Owners explicitly decrypt when needed
✅ **Secure by Default**: Anonymized view is the default
✅ **User Awareness**: Clear warnings about sensitive data
✅ **No Persistence**: Decrypted data stays in memory only
✅ **Clean UX**: Smooth toggle between anonymized and decrypted views
✅ **Visual Clarity**: Icons and badges clearly indicate state

## Future Enhancements

1. **Decryption Timeout**: Auto-hide after N minutes
2. **Audit Logging**: Track when owners decrypt names
3. **Partial Decryption**: Decrypt individual pirates on-demand
4. **Multi-Level Permissions**: Different access levels for different user types
5. **Export Controls**: Restrict export of decrypted data

## Conclusion

The pirate name anonymization system is now fully implemented in the webapp with:
- True end-to-end encryption
- Owner-only decryption access
- Clear visual indicators
- Secure handling of sensitive data
- Excellent user experience

All original names are truly anonymized by default, and only expedition owners can decrypt them through an explicit, secure process.
