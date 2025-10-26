# How to Get Your Master Decryption Key

Your decryption key is now **always the same** across ALL your expeditions!

## Quick Start - Get Your Key Now

### Option 1: API Call (Easiest)

Start your Flask app and call:

```bash
curl -X GET http://localhost:5000/api/brambler/master-key \
  -H "X-Chat-ID: YOUR_CHAT_ID"
```

**Replace `YOUR_CHAT_ID` with your actual Telegram chat ID.**

Example response:
```json
{
  "success": true,
  "master_key": "YOUR_MASTER_KEY_HERE",
  "owner_chat_id": 123456789,
  "created_at": "2025-10-23T12:00:00",
  "key_version": 1,
  "message": "This is your master key - it works for ALL your expeditions"
}
```

### Option 2: Python Script

Create a file `get_my_key.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

from database import initialize_database
from utils.encryption import get_encryption_service

# Initialize database
initialize_database()

# Your Telegram chat ID
YOUR_CHAT_ID = 123456789  # CHANGE THIS

# Get encryption service
encryption_service = get_encryption_service()

# Generate your master key (deterministic - always the same)
master_key = encryption_service.generate_user_master_key(YOUR_CHAT_ID)

print(f"Your Master Key: {master_key}")
print(f"\nThis key works for ALL your expeditions!")
print("Save it somewhere safe - you'll need it to decrypt pirate names.")
```

Run it:
```bash
python get_my_key.py
```

### Option 3: Database Query

If you have database access:

```sql
-- Check if you already have a stored key
SELECT master_key, created_at
FROM user_master_keys
WHERE owner_chat_id = YOUR_CHAT_ID;

-- If no result, the key will be generated when you first request it via API
```

## Important Facts About Your Master Key

1. **Always the Same**: Your master key is generated deterministically from your chat_id
2. **Works Everywhere**: Use it to decrypt pirate names in ANY of your expeditions
3. **Secure**: Only YOU (as owner) can retrieve your master key
4. **Regeneratable**: Lost it? Just generate it again - it will be the same!

## Using Your Master Key

Once you have your master key, use it to decrypt pirate names:

```bash
curl -X POST http://localhost:5000/api/brambler/decrypt/EXPEDITION_ID \
  -H "X-Chat-ID: YOUR_CHAT_ID" \
  -H "Content-Type: application/json" \
  -d '{"owner_key": "YOUR_MASTER_KEY"}'
```

This works for **ALL your expeditions** - just change the `EXPEDITION_ID`.

## Migrating Existing Expeditions

If you have existing expeditions with old keys, migrate them to use your master key:

```bash
# Preview what will change
python migrations/migrate_to_master_keys.py --dry-run --owner-chat-id YOUR_CHAT_ID

# Actually migrate
python migrations/migrate_to_master_keys.py --owner-chat-id YOUR_CHAT_ID
```

## Troubleshooting

### "Authentication required"
- Make sure you're passing your chat_id in the `X-Chat-ID` header

### "Owner permission required"
- Only users with owner-level permissions can get their master key
- Check your user level in the database

### "Different key than expected"
- The key is deterministic based on your chat_id
- Same chat_id = same key, always
- Double-check you're using the correct chat_id

## Next Steps

1. Get your master key using one of the methods above
2. Save it in a secure location (password manager recommended)
3. Use it to decrypt pirate names in any of your expeditions
4. Optional: Run the migration to update existing expeditions

---

**Need Help?**
- Check the full guide: `ai_docs/user_master_key_guide.md`
- API documentation in the guide
- Test the implementation: `python test_master_key_implementation.py`
