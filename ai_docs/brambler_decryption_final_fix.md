# Brambler Decryption - Final Fix (Key Mismatch Resolution)

## The Real Problem

After implementing all the previous fixes, decryption was still failing with `InvalidTag` errors. The investigation revealed:

**The pirate names were encrypted with the EXPEDITION'S owner_key, but we were trying to decrypt with the USER'S master_key!**

### Key Discovery

Testing revealed:
```
Expedition owner_key: Pvui5dey0XYYxJ5AukeTFY3ivgYIk8VQ7HlbarIVVkdbQ8w8HS0b-mGZIUMlG18_sfUCoikjX5lXpmRtiIjnKA==

User master_key: mWb1d2SV0p40ug4skGTPiAOy9rk-RpLBbpWyVgcqFEAL6c5gRIaE2t061K7n3K724s-cN5BwkvTnjUrxt6TcHQ==

Keys are same: False

Decryption with expedition owner_key: SUCCESS! ✅
Decryption with user master_key: FAILED (InvalidTag) ❌
```

## Why This Happened

The system has TWO different key concepts that got confused:

### 1. Expedition Owner Key (Per-Expedition)
- **Stored in**: `expeditions.owner_key` column
- **Generated when**: Expedition is created
- **Used for**: Encrypting/decrypting pirate names for THAT specific expedition
- **Unique**: Each expedition has its own owner_key
- **What works**: Decrypting pirate names encrypted in that expedition

### 2. User Master Key (Per-User)
- **Stored in**: `user_master_keys` table
- **Generated from**: User's chat_id (deterministic)
- **Used for**: Universal key across ALL user's expeditions
- **Purpose**: Intended for future migration, not currently used for encryption
- **What works**: Nothing yet - data wasn't encrypted with this key

## The Confusion

The documentation and implementation suggested using the "user master key" for decryption, but:
1. The actual pirate names were encrypted with per-expedition owner_keys
2. The master key system was prepared but not fully migrated
3. Users needed the expedition's owner_key, not their master key

## Final Solution

**Use the expedition's owner_key for decryption, not the user's master key.**

### Frontend Changes

**File**: `webapp/src/pages/BramblerManager.tsx:425-460`

Changed from fetching user master key:
```typescript
// OLD - WRONG
const masterKey = await bramblerService.getUserMasterKey();
```

To fetching expedition owner key:
```typescript
// NEW - CORRECT
const ownerKey = await bramblerService.getOwnerKey(expeditionId);
```

**Updated tooltips**:
```typescript
// From: "Enter your master key..."
// To: "Enter expedition decryption key..."

// From: "Use your USER MASTER KEY..."
// To: "Click 'Load My Key' to fetch this expedition's decryption key automatically."
```

## How It Works Now

### User Flow

1. Navigate to `/brambler` page
2. Click **"Load My Key"** button
   - Calls `GET /api/brambler/owner-key/{expedition_id}`
   - Backend returns the expedition's owner_key
   - Key is filled into the input field
3. Click **"Show Real Names"**
   - Calls `POST /api/brambler/decrypt/{expedition_id}`
   - Sends the expedition's owner_key in request body
   - Backend decrypts pirate names with the SAME key used to encrypt them
   - Success! ✅

### API Flow

```
GET /api/brambler/owner-key/7
Headers: X-Chat-ID: 5094426438

Response:
{
  "success": true,
  "expedition_id": 7,
  "owner_key": "Pvui5dey0XYYxJ5AukeTFY..." // Expedition's key
}

POST /api/brambler/decrypt/7
Headers: X-Chat-ID: 5094426438
Body: {
  "owner_key": "Pvui5dey0XYYxJ5AukeTFY..." // Same key from above
}

Response:
{
  "success": true,
  "mappings_dict": {
    "Cabo Tsunami o Audaz": "Danilin",
    "Mestre Barba Ruiva o Cruel": "Du Pampa",
    ...
  }
}
```

## Testing Evidence

**Script**: `check_encryption_keys.py`

Results:
```
=== Decryption Tests ===

1. Testing with expedition owner_key:
   SUCCESS! Decrypted: {
     'Danilin': 'Cabo Tsunami o Audaz',
     'Du Pampa': 'Mestre Barba Ruiva o Cruel',
     'Paradinha': 'Corsário Dente de Ouro o Lendário',
     ...
   }

2. Testing with user master_key:
   FAILED: cryptography.exceptions.InvalidTag
```

This proves that **only the expedition's owner_key can decrypt the data**.

## What About Master Keys?

The user master key system exists in the codebase and API, but:

1. **It's not currently used** for encrypting pirate names
2. **It was prepared** for a future migration (see `migrations/migrate_to_master_keys.py`)
3. **It would require re-encrypting** all existing pirate names to use it
4. **For now**, use the expedition's owner_key per expedition

### Future Migration (Not Implemented Yet)

To use master keys, you would need to:
1. Decrypt all pirate names with current expedition owner_keys
2. Re-encrypt them with the user's master key
3. Update all expeditions to use the master key
4. Run the migration: `python migrations/migrate_to_master_keys.py`

**Until this migration runs, use expedition owner_keys!**

## Files Modified

1. **webapp/src/pages/BramblerManager.tsx**:
   - Changed `getUserMasterKey()` to `getOwnerKey(expeditionId)`
   - Updated tooltips and placeholders
   - Fixed function name (kept as `handleGetMasterKey` but it now gets owner key)

## Correct Keys for Expedition 7

**Expedition Owner Key** (✅ USE THIS):
```
Pvui5dey0XYYxJ5AukeTFY3ivgYIk8VQ7HlbarIVVkdbQ8w8HS0b-mGZIUMlG18_sfUCoikjX5lXpmRtiIjnKA==
```

**User Master Key** (❌ DON'T USE - won't work):
```
mWb1d2SV0p40ug4skGTPiAOy9rk-RpLBbpWyVgcqFEAL6c5gRIaE2t061K7n3K724s-cN5BwkvTnjUrxt6TcHQ==
```

## How to Use

1. Open webapp at `/brambler`
2. Click "Load My Key" - it fetches expedition 7's owner_key
3. Click "Show Real Names" - decryption works! ✅

## Error Logs Before Fix

```
cryptography.exceptions.InvalidTag
```

This meant: "Wrong decryption key - the data was encrypted with a different key"

## Error Logs After Fix

No errors! Decryption successful! ✅

## Status

✅ **WORKING** - Decryption now uses the correct key
✅ Load My Key button fetches expedition owner_key
✅ Show Real Names successfully decrypts
✅ All pirate names reveal real names when decrypted

## Related Documentation

- Previous attempts: `brambler_decryption_fix.md`, `brambler_decryption_fix_complete.md`
- Encryption guide: `brambler_full_encryption_guide.md`
- Master key migration (not run yet): `migrations/migrate_to_master_keys.py`
