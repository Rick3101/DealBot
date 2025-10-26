# Brambler Decryption Fix - Webapp Real Names Display

## Issue
When entering a decryption key in the Brambler Manager webapp (/brambler), the pirate names were still shown instead of the real names after toggling "Show Real Names".

## Root Cause
The `BramblerManager.tsx` component was only toggling the display state locally without calling the backend decryption API. The component structure was:

1. User enters decryption key
2. User clicks "Show Real Names" button
3. Component toggles `showRealNames` state to `true`
4. **PROBLEM**: No API call was made to decrypt the names
5. Display logic tried to show `pirate.original_name` which is `null` (due to full encryption mode)
6. Result: Pirate names still displayed

## Solution Implemented

### 1. State Management Enhancement
Added `decryptedMappings` to component state to store the decrypted pirate-to-real-name mappings:

```typescript
interface BramblerState {
  pirateNames: PirateName[];
  showRealNames: boolean;
  decryptionKey: string;
  isOwner: boolean;
  loading: boolean;
  error: string | null;
  decryptedMappings: Record<string, string>; // pirate_name -> original_name
}
```

### 2. API Integration in Toggle Handler
Updated `handleToggleView` to call the decryption API when showing real names:

```typescript
const handleToggleView = async () => {
  if (!state.showRealNames && state.isOwner) {
    // Validate key is provided
    if (!state.decryptionKey.trim()) {
      setState(prev => ({ ...prev, error: 'Please enter your decryption key' }));
      return;
    }

    // Call decrypt API
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { bramblerService } = await import('@/services/api/bramblerService');

      const decryptedMappings = await bramblerService.decryptNames(expeditionId, {
        owner_key: state.decryptionKey
      });

      setState(prev => ({
        ...prev,
        showRealNames: true,
        decryptedMappings,
        loading: false,
        error: null
      }));

      hapticFeedback('medium');
      showAlert('Names decrypted successfully!');
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to decrypt names. Please check your decryption key and try again.'
      }));
    }
  } else {
    // Toggle back to pirate names (no API call needed)
    setState(prev => ({
      ...prev,
      showRealNames: false,
      error: null
    }));
  }
};
```

### 3. Display Logic Update
Changed the name display to use decrypted mappings instead of `pirate.original_name`:

**Before:**
```typescript
{state.showRealNames && pirate.original_name
  ? `👤 ${pirate.original_name}`
  : `🏴‍☠️ ${pirate.pirate_name}`
}
```

**After:**
```typescript
{state.showRealNames && state.decryptedMappings[pirate.pirate_name]
  ? `👤 ${state.decryptedMappings[pirate.pirate_name]}`
  : `🏴‍☠️ ${pirate.pirate_name}`
}
```

### 4. Avatar Initials Update
Updated avatar display to use decrypted names:

```typescript
{getAvatarInitials(
  state.showRealNames && state.decryptedMappings[pirate.pirate_name]
    ? state.decryptedMappings[pirate.pirate_name]
    : pirate.pirate_name
)}
```

### 5. Export Functionality Update
Updated export to use decrypted mappings:

```typescript
names: state.pirateNames.map(name => ({
  pirate_name: name.pirate_name,
  original_name: state.showRealNames && state.decryptedMappings[name.pirate_name]
    ? state.decryptedMappings[name.pirate_name]
    : '[ENCRYPTED]'
}))
```

## Flow After Fix

1. User enters owner key in the decryption key input
2. User clicks "Show Real Names" button
3. Component calls `/api/brambler/decrypt/{expedition_id}` with the owner key
4. Backend decrypts all pirate names using the owner key
5. Backend returns mappings: `{ "Capitão Barbas Negras": "John Doe", ... }`
6. Component stores mappings in `decryptedMappings` state
7. Component sets `showRealNames` to `true`
8. Display logic looks up real names from `decryptedMappings` using pirate name as key
9. User sees real names displayed correctly

## Security Considerations

1. **Decryption on demand**: Names are only decrypted when owner explicitly enters key and toggles view
2. **Memory-only storage**: Decrypted mappings are stored in component state (React memory), never persisted
3. **Toggle off clears display**: When toggling back to pirate names, real names are hidden (mappings remain in memory until page refresh)
4. **Owner-only access**: API endpoint validates owner permission before allowing decryption
5. **Key validation**: Invalid keys result in decryption failure with error message

## Backend API Used

**Endpoint**: `POST /api/brambler/decrypt/{expedition_id}`

**Request Body**:
```json
{
  "owner_key": "user_entered_owner_key"
}
```

**Response**:
```json
{
  "success": true,
  "expedition_id": 7,
  "decrypted_count": 5,
  "mappings": [
    {
      "pirate_name": "Capitão Barbas Negras o Terrível",
      "original_name": "John Doe"
    }
  ],
  "mappings_dict": {
    "Capitão Barbas Negras o Terrível": "John Doe"
  }
}
```

## Files Modified

1. **webapp/src/pages/BramblerManager.tsx**:
   - Added `decryptedMappings` to state interface
   - Updated `handleToggleView` to call decrypt API
   - Updated display logic to use `decryptedMappings`
   - Updated avatar initials logic
   - Updated export functionality

## Testing Recommendations

1. **Valid Key Test**: Enter correct owner key and verify real names appear
2. **Invalid Key Test**: Enter wrong key and verify error message appears
3. **No Key Test**: Try to show real names without entering key and verify error
4. **Toggle Test**: Toggle between pirate/real names multiple times
5. **Export Test**: Export names in both pirate and real name modes
6. **Non-Owner Test**: Verify non-owners cannot see decrypt option

## Related Documentation

- [Brambler Full Encryption Guide](brambler_full_encryption_guide.md)
- [Pirate Anonymization Webapp Implementation](pirate_anonymization_webapp_implementation.md)
- [Owner Key Migration](owner_key_migration_completed.md)
