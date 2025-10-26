# User Master Key System - Complete Guide

## Overview

The **User Master Key** system provides a single, consistent decryption key for each user across ALL their expeditions. Instead of having a different key for each expedition, you now have ONE master key that works everywhere.

## Key Features

### Before (Per-Expedition Keys)
- Each expedition had its own unique encryption key
- You needed different keys to decrypt different expeditions
- Lost keys meant lost access to specific expedition data
- Managing multiple keys was cumbersome

### After (User Master Key)
- **ONE key per user** - works for ALL your expeditions
- Same key across past, present, and future expeditions
- Easy to remember and store
- Consistent decryption experience

## How It Works

### 1. Key Generation

Your master key is generated **deterministically** based on your `owner_chat_id`:

```python
# The key is ALWAYS the same for your chat_id
master_key = generate_user_master_key(your_chat_id)
# Result: "base64_encoded_key_here..."
```

**Technical Details:**
- Algorithm: PBKDF2-HMAC-SHA256
- Iterations: 100,000
- Key Size: 256 bits (32 bytes)
- Salt: Deterministic based on your chat_id
- Format: Base64-encoded (64 bytes: 32 salt + 32 key)

### 2. Key Storage

Your master key is stored in the `user_master_keys` table:

```sql
CREATE TABLE user_master_keys (
    id SERIAL PRIMARY KEY,
    owner_chat_id BIGINT UNIQUE NOT NULL,
    master_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    key_version INTEGER DEFAULT 1
);
```

### 3. Automatic Application

When you create a new expedition, it automatically uses your master key:

```python
# Old behavior (random per-expedition key)
owner_key = generate_owner_key(expedition_id, owner_chat_id, use_master_key=False)

# New behavior (uses master key)
owner_key = generate_owner_key(expedition_id, owner_chat_id, use_master_key=True)
# Returns the SAME key for all your expeditions!
```

## Getting Your Master Key

### Option 1: API Endpoint (Recommended)

```http
GET /api/brambler/master-key
Headers:
  X-Chat-ID: <your_chat_id>
```

**Response:**
```json
{
  "success": true,
  "master_key": "your_consistent_master_key_here",
  "owner_chat_id": 123456789,
  "created_at": "2025-10-23T12:00:00",
  "key_version": 1,
  "message": "This is your master key - it works for ALL your expeditions"
}
```

### Option 2: Database Query

If you have direct database access:

```sql
SELECT master_key
FROM user_master_keys
WHERE owner_chat_id = <your_chat_id>;
```

### Option 3: Python Script

```python
from utils.encryption import get_encryption_service

encryption_service = get_encryption_service()
your_chat_id = 123456789  # Replace with your actual chat_id

# This will ALWAYS return the same key for your chat_id
master_key = encryption_service.generate_user_master_key(your_chat_id)
print(f"Your master key: {master_key}")
```

## Using Your Master Key

### Decrypt Pirate Names

```http
POST /api/brambler/decrypt/<expedition_id>
Headers:
  X-Chat-ID: <your_chat_id>
Body:
{
  "owner_key": "your_master_key_here"
}
```

**Response:**
```json
{
  "success": true,
  "expedition_id": 123,
  "decrypted_count": 5,
  "mappings": [
    {
      "pirate_name": "Capitão Barbas Negras o Terrível",
      "original_name": "JohnDoe"
    }
  ],
  "mappings_dict": {
    "Capitão Barbas Negras o Terrível": "JohnDoe"
  }
}
```

### Works Across ALL Expeditions

The same master key works for:
- Expedition 1
- Expedition 2
- Expedition 3
- ...all future expeditions!

## Migration Guide

### Migrating Existing Expeditions

If you have existing expeditions with old per-expedition keys, run the migration:

```bash
# Dry run (see what would change)
python migrations/migrate_to_master_keys.py --dry-run

# Migrate your expeditions (by your chat_id)
python migrations/migrate_to_master_keys.py --owner-chat-id YOUR_CHAT_ID

# Migrate ALL owners (admin only)
python migrations/migrate_to_master_keys.py
```

### What the Migration Does

1. **Generates your master key** (if you don't have one)
2. **Stores it** in `user_master_keys` table
3. **Updates all your expeditions** to use this master key
4. **Re-encrypts pirate names** with the new key (future enhancement)

### Migration Example

```
Starting master key migration...

Owner 123456789 has 5 expeditions

============================================================
Processing owner: 123456789
============================================================
Generated and stored master key for owner 123456789
Updated 5 expeditions for owner 123456789
Processed 15 pirate names for owner 123456789
Successfully migrated owner 123456789

============================================================
MIGRATION SUMMARY
============================================================
Owners found: 1
Master keys generated: 1
Expeditions updated: 5
Pirate names processed: 15
Errors: 0
============================================================
Migration completed successfully!
```

## Security Considerations

### Advantages

1. **Consistency**: Same key everywhere - easier to manage
2. **Deterministic**: Lost your key? Regenerate it from your chat_id
3. **Backward Compatible**: Old expeditions can still work with old keys
4. **Secure**: 256-bit AES-GCM encryption with 100k PBKDF2 iterations

### Security Model

| User Type | Can Get Master Key | Can Decrypt Names |
|-----------|-------------------|-------------------|
| Owner     | ✅ Yes            | ✅ Yes            |
| Admin     | ❌ No             | ❌ No             |
| User      | ❌ No             | ❌ No             |

### Best Practices

1. **Store Your Key Securely**
   - Save it in a password manager
   - Don't share it publicly
   - Treat it like a password

2. **Access Control**
   - Only you (owner) can retrieve your master key
   - API requires owner-level permissions
   - Each user has their own unique master key

3. **Key Regeneration**
   - Your master key is deterministic
   - It can be regenerated from your chat_id
   - No need to back up manually (but recommended)

## Troubleshooting

### "Master key not found"

**Solution:**
```bash
# Call the API endpoint to generate it
curl -X GET http://localhost:5000/api/brambler/master-key \
  -H "X-Chat-ID: your_chat_id"
```

### "Permission denied"

**Cause:** You need owner-level access

**Solution:**
- Verify you're authenticated as an owner
- Check your chat_id in the X-Chat-ID header

### Different key than expected

**Cause:** The key is deterministic based on chat_id

**Solution:**
- Verify you're using the correct chat_id
- The same chat_id ALWAYS produces the same key

## API Reference

### Get User Master Key

**Endpoint:** `GET /api/brambler/master-key`

**Headers:**
- `X-Chat-ID`: Your Telegram chat ID (required)

**Response:**
```json
{
  "success": true,
  "master_key": "base64_encoded_key",
  "owner_chat_id": 123456789,
  "created_at": "2025-10-23T12:00:00",
  "key_version": 1,
  "message": "This is your master key - it works for ALL your expeditions"
}
```

**Permissions:** Owner only

**Behavior:**
- If key exists: Returns existing key and updates `last_accessed`
- If key doesn't exist: Generates new key and stores it

## Database Schema

### user_master_keys Table

```sql
CREATE TABLE user_master_keys (
    id SERIAL PRIMARY KEY,
    owner_chat_id BIGINT UNIQUE NOT NULL,  -- Your Telegram chat ID
    master_key TEXT NOT NULL,               -- Your master encryption key
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    key_version INTEGER DEFAULT 1          -- For future key rotation
);
```

### Indexes

```sql
CREATE INDEX idx_usermasterkeys_owner_chat_id ON user_master_keys(owner_chat_id);
CREATE INDEX idx_usermasterkeys_last_accessed ON user_master_keys(last_accessed);
```

## Code Examples

### Check if You Have a Master Key

```python
from database import get_db_manager

db_manager = get_db_manager()
your_chat_id = 123456789

with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT master_key, created_at
            FROM user_master_keys
            WHERE owner_chat_id = %s
        """, (your_chat_id,))
        result = cur.fetchone()

        if result:
            print(f"You have a master key created at {result[1]}")
        else:
            print("No master key found - call the API to generate one")
```

### Manually Generate Master Key

```python
from utils.encryption import get_encryption_service
from database import get_db_manager

encryption_service = get_encryption_service()
db_manager = get_db_manager()

your_chat_id = 123456789

# Generate the key (deterministic)
master_key = encryption_service.generate_user_master_key(your_chat_id)

# Store it
with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO user_master_keys (owner_chat_id, master_key, key_version)
            VALUES (%s, %s, 1)
            ON CONFLICT (owner_chat_id) DO NOTHING
        """, (your_chat_id, master_key))
        conn.commit()

print(f"Your master key: {master_key}")
```

## Summary

✅ **User Master Key Benefits:**
- ONE key for ALL your expeditions
- Easy to retrieve via API
- Deterministic - can be regenerated
- Secure 256-bit AES-GCM encryption
- Backward compatible with old expeditions

🔐 **Security:**
- Owner-only access
- Stored securely in database
- Deterministic generation from chat_id
- Same security as per-expedition keys

📊 **Use Cases:**
- Decrypt any of your expedition pirate names
- Works across all past and future expeditions
- Single key to manage instead of many
- Consistent decryption experience

## Next Steps

1. **Get your master key**: Call `GET /api/brambler/master-key`
2. **Save it securely**: Store in a password manager
3. **Test it**: Try decrypting pirate names from different expeditions
4. **Migrate old expeditions**: Run the migration script if needed

---

**Need Help?**
- Check the API endpoint: `/api/brambler/master-key`
- Run migration: `python migrations/migrate_to_master_keys.py --help`
- Review code: `utils/encryption.py` (generate_user_master_key function)
