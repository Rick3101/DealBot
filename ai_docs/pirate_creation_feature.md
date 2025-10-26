# Pirate Creation Feature

## Overview
This document describes the new pirate creation functionality that allows admins and owners to manually create pirates with original names through the webapp Brambler maintenance page.

## Implementation Date
2025-10-16

## Feature Description
Previously, pirates were automatically created from `Vendas.comprador` data. Now, admins and owners can manually create new pirates with:
- A specified original name (required)
- An optional custom pirate name (auto-generated if not provided)
- Automatic encryption support (if expedition has an owner_key)
- Duplicate prevention (cannot create same original_name for same expedition)

## Backend Implementation

### 1. Service Layer: BramblerService.create_pirate()

**File:** `services/brambler_service.py`

**Method Signature:**
```python
def create_pirate(
    self,
    expedition_id: int,
    original_name: str,
    pirate_name: Optional[str] = None,
    owner_key: Optional[str] = None
) -> Optional[Dict]:
```

**Parameters:**
- `expedition_id`: The expedition ID to add the pirate to
- `original_name`: The real name/buyer name (required)
- `pirate_name`: Optional custom pirate name (if None, auto-generated)
- `owner_key`: Optional encryption key for identity protection

**Returns:**
Dictionary with pirate data:
```python
{
    'id': int,
    'pirate_name': str,
    'original_name': str,
    'expedition_id': int,
    'encrypted_identity': str,
    'created_at': str (ISO format)
}
```

**Features:**
- Input sanitization for both original_name and pirate_name
- Automatic pirate name generation using deterministic algorithm
- Duplicate prevention (checks if original_name already exists)
- Optional encryption support
- Comprehensive error logging
- Transaction safety

**Example Usage:**
```python
brambler_service = BramblerService()

# Auto-generated pirate name
result = brambler_service.create_pirate(
    expedition_id=11,
    original_name="John Doe"
)

# Custom pirate name
result = brambler_service.create_pirate(
    expedition_id=11,
    original_name="Jane Smith",
    pirate_name="Capitao Jane o Valente"
)
```

### 2. API Endpoint: POST /api/brambler/create

**File:** `app.py` (lines 1433-1500)

**Endpoint:** `POST /api/brambler/create`

**Authentication:** Required (Owner or Admin level)

**Request Headers:**
- `X-Chat-ID`: User's Telegram chat ID (required for authentication)

**Request Body:**
```json
{
    "expedition_id": 11,
    "original_name": "John Doe",
    "pirate_name": "Capitao John o Magnifico"  // Optional
}
```

**Success Response (201 Created):**
```json
{
    "success": true,
    "pirate": {
        "id": 35,
        "pirate_name": "Capitao John o Magnifico",
        "original_name": "John Doe",
        "expedition_id": 11,
        "encrypted_identity": "",
        "created_at": "2025-10-16T10:30:00"
    },
    "message": "Pirate created successfully"
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
    "error": "Authentication required"
}
```

**403 Forbidden:**
```json
{
    "error": "Owner/Admin permission required"
}
```

**400 Bad Request:**
```json
{
    "error": "expedition_id is required"
}
// OR
{
    "error": "original_name is required"
}
// OR
{
    "error": "Failed to create pirate (may already exist)"
}
```

**404 Not Found:**
```json
{
    "error": "Expedition not found"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Internal server error"
}
```

## Frontend Implementation

### 1. UI Components: Brambler Maintenance Page

**File:** `webapp/src/pages/BramblerMaintenance.tsx`

**New Features:**
- **Create Pirate Button:** Green "Create Pirate" button in the controls section
- **Create Modal:** Full-featured modal with form for pirate creation
- **Expedition Selector:** Dropdown to choose which expedition to add pirate to
- **Original Name Input:** Required field for real buyer/consumer name
- **Pirate Name Input:** Optional field (auto-generates if left blank)
- **Real-time Validation:** Error messages for missing fields
- **Success Feedback:** Automatically adds new pirate to the list upon creation

**Location in UI:**
- Navigate to: Brambler Maintenance page
- Click: "Create Pirate" button (green button with + icon)
- Fill form and submit

**User Flow:**
1. Click "Create Pirate" button
2. Select an expedition from dropdown (only shows active expeditions)
3. Enter original name (required)
4. Optionally enter custom pirate name (or leave blank for auto-generation)
5. Click "Create Pirate" to submit
6. New pirate appears in the table immediately

### 2. TypeScript Service: BramblerService.createPirate()

**File:** `webapp/src/services/api/bramblerService.ts`

**Method Signature:**
```typescript
async createPirate(data: BramblerCreateRequest): Promise<BramblerCreateResponse>
```

**Request Interface:**
```typescript
export interface BramblerCreateRequest {
  expedition_id: number;
  original_name: string;
  pirate_name?: string; // Optional - will be auto-generated if not provided
}
```

**Response Interface:**
```typescript
export interface BramblerCreateResponse {
  success: boolean;
  pirate: BramblerMaintenanceItem;
  message: string;
}
```

**Example Usage:**
```typescript
import { bramblerService } from '@/services/api/bramblerService';

// Auto-generated pirate name
const result = await bramblerService.createPirate({
  expedition_id: 11,
  original_name: "John Doe"
});

// Custom pirate name
const result = await bramblerService.createPirate({
  expedition_id: 11,
  original_name: "Jane Smith",
  pirate_name: "Capitao Jane o Valente"
});
```

## Database Schema

**Table:** `expedition_pirates`

**Relevant Columns:**
- `id` (SERIAL PRIMARY KEY)
- `expedition_id` (INTEGER REFERENCES Expeditions)
- `pirate_name` (VARCHAR(100) NOT NULL)
- `original_name` (VARCHAR(100) NOT NULL)
- `chat_id` (BIGINT)
- `user_id` (INTEGER REFERENCES Usuarios)
- `encrypted_identity` (TEXT)
- `role` (VARCHAR(20) DEFAULT 'participant')
- `joined_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
- `status` (VARCHAR(20) DEFAULT 'active')

**Constraints:**
- `UNIQUE(expedition_id, pirate_name)` - Prevents duplicate pirate names per expedition
- `UNIQUE(expedition_id, original_name)` - Prevents duplicate original names per expedition

## Security Features

1. **Authentication Required:** Only authenticated users can create pirates
2. **Permission Check:** Only Owner or Admin level users allowed
3. **Input Sanitization:** Both original_name and pirate_name are sanitized
4. **Expedition Validation:** Verifies expedition exists before creating pirate
5. **Duplicate Prevention:** Prevents creating duplicate original_name for same expedition
6. **Encryption Support:** Automatically encrypts identity if expedition has owner_key

## Use Cases

### 1. Manually Add New Buyer
When a new buyer joins an expedition but hasn't made a purchase yet:
```json
POST /api/brambler/create
{
    "expedition_id": 11,
    "original_name": "NewBuyer"
}
```

### 2. Create Pirate with Custom Name
When you want a specific pirate name for a buyer:
```json
POST /api/brambler/create
{
    "expedition_id": 11,
    "original_name": "VIPBuyer",
    "pirate_name": "Almirante VIP das Sete Mares"
}
```

### 3. Pre-populate Expedition Pirates
Before expedition starts, add expected participants:
```json
POST /api/brambler/create
{
    "expedition_id": 12,
    "original_name": "ExpectedParticipant1"
}
```

## Testing

**Test File:** `test_pirate_creation.py`

**Test Coverage:**
1. Create pirate with auto-generated name
2. Create pirate with custom name
3. Duplicate prevention validation
4. Retrieve all pirates for expedition
5. Cleanup test data

**Run Tests:**
```bash
python test_pirate_creation.py
```

**Expected Results:**
- Auto-generated pirate name should follow pattern: "Rank + Name + Suffix"
- Custom pirate name should be preserved exactly
- Duplicate attempts should return None
- All created pirates should appear in expedition pirate list

## Integration with Existing Features

### Brambler Maintenance Page
The webapp Brambler maintenance page can now:
1. View all pirates across all expeditions (existing)
2. Update pirate names (existing)
3. **Create new pirates manually (NEW)**

### Expedition System
Pirates created manually will:
- Appear in expedition pirate lists
- Be available for item consumption tracking
- Support encryption/decryption with owner key
- Follow same anonymization rules as auto-created pirates

## Future Enhancements

1. **Bulk Pirate Creation:** Create multiple pirates at once from CSV
2. **Pirate Deletion:** Soft delete pirates with status = 'inactive'
3. **Pirate Transfer:** Move pirates between expeditions
4. **Pirate History:** Track all changes to pirate names
5. **Pirate Roles:** Assign different roles (participant, officer, captain)

## Related Files

**Backend:**
- `services/brambler_service.py` (lines 1072-1152)
- `app.py` (lines 1433-1500)
- `database/schema.py` (expedition_pirates table)

**Frontend:**
- `webapp/src/services/api/bramblerService.ts` (lines 102-117, 134-150)

**Tests:**
- `test_pirate_creation.py`

**Documentation:**
- `ai_docs/brambler_maintenance_page_implementation.md`
- `ai_docs/pirate_anonymization_webapp_implementation.md`

## API Reference Summary

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/brambler/create` | POST | Create new pirate | Owner/Admin |
| `/api/brambler/all-names` | GET | Get all pirates | Owner/Admin |
| `/api/brambler/update/<pirate_id>` | PUT | Update pirate name | Owner/Admin |
| `/api/brambler/names/<expedition_id>` | GET | Get expedition pirates | Any |
| `/api/brambler/generate/<expedition_id>` | POST | Generate pirate names | Owner |
| `/api/brambler/decrypt/<expedition_id>` | POST | Decrypt pirate names | Owner |

## Changelog

### Version 1.0 (2025-10-16)
- Initial implementation of pirate creation feature
- Added `BramblerService.create_pirate()` method
- Added `POST /api/brambler/create` endpoint
- Added TypeScript types and service method
- Added comprehensive tests
- Added documentation

---

**Last Updated:** 2025-10-16
**Author:** Development Team
**Status:** Production Ready
