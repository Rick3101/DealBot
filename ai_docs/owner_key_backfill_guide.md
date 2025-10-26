# Owner Key Backfill Guide

## Issue

You discovered that existing expeditions have `owner_key = NULL` in the database. This prevents the pirate name decryption feature from working for those expeditions.

## Root Cause

The owner key generation feature was added to the `create_expedition()` method in [services/expedition_service.py:63-86](../services/expedition_service.py:63-86), but this only affects **new** expeditions created after the feature was implemented.

**Existing expeditions** created before this feature don't have owner keys, which causes the decryption API to fail with:
```
Failed to retrieve owner key
```

## Solution

Run the migration script to backfill owner keys for existing expeditions.

### Migration Script

**Location:** [migrations/backfill_expedition_owner_keys.py](../migrations/backfill_expedition_owner_keys.py)

### Usage

#### 1. Dry Run (Check What Will Be Updated)

```bash
python migrations/backfill_expedition_owner_keys.py --dry-run
```

**Output:**
```
============================================================
Expedition Owner Key Backfill Migration
============================================================
Found 5 expeditions without owner keys
  - Expedition 1: 'Summer Campaign' (owner: 123456789)
  - Expedition 2: 'Winter Sales' (owner: 123456789)
  - Expedition 3: 'Q4 Push' (owner: 987654321)
  - Expedition 4: 'Black Friday' (owner: 123456789)
  - Expedition 5: 'New Year' (owner: 555555555)

DRY RUN MODE - No changes made
Run with dry_run=False to actually update the database
============================================================
```

#### 2. Run the Migration

```bash
python migrations/backfill_expedition_owner_keys.py
```

**Output:**
```
============================================================
Expedition Owner Key Backfill Migration
============================================================
Found 5 expeditions without owner keys
✓ Updated expedition 1: 'Summer Campaign'
✓ Updated expedition 2: 'Winter Sales'
✓ Updated expedition 3: 'Q4 Push'
✓ Updated expedition 4: 'Black Friday'
✓ Updated expedition 5: 'New Year'

Successfully updated 5 expeditions

Verifying changes...

Verification Results:
  Total expeditions: 5
  With owner keys: 5
  Without owner keys: 0

✓ All expeditions have owner keys!
============================================================
Migration complete
============================================================
```

#### 3. Verify Owner Keys

```bash
python migrations/backfill_expedition_owner_keys.py --verify
```

**Output:**
```
Verification Results:
  Total expeditions: 5
  With owner keys: 5
  Without owner keys: 0

✓ All expeditions have owner keys!
```

## What the Migration Does

1. **Finds expeditions without owner keys:**
   ```sql
   SELECT id, owner_chat_id, name
   FROM expeditions
   WHERE owner_key IS NULL OR owner_key = ''
   ```

2. **Generates owner keys:**
   - Uses the same `generate_owner_key()` function from `utils/encryption`
   - Creates a secure 256-bit key using PBKDF2-HMAC-SHA256
   - Key is deterministic based on `expedition_id` and `owner_chat_id`

3. **Updates expeditions:**
   ```sql
   UPDATE expeditions
   SET owner_key = %s, owner_user_id = %s
   WHERE id = %s
   ```

4. **Verifies the migration:**
   - Counts expeditions with/without owner keys
   - Confirms all expeditions now have keys

## Safety Features

### Dry Run Mode
- Default mode shows what would be updated
- No database changes made
- Safe to run multiple times

### Transaction Safety
- All updates done in a single transaction
- Automatic rollback on error
- Preserves data integrity

### Error Handling
- Individual expedition failures logged
- Migration continues for other expeditions
- Detailed error messages for debugging

## After Migration

Once the migration is complete:

1. **Test Decryption in WebApp:**
   - Open an expedition as the owner
   - Click "Show Original Names" button
   - Verify decryption works

2. **Check Backend Logs:**
   ```bash
   grep "owner_key" bot.log | tail -20
   ```

3. **Verify Database:**
   ```sql
   SELECT id, name, owner_chat_id,
          CASE WHEN owner_key IS NULL THEN 'NULL' ELSE 'SET' END as owner_key_status
   FROM expeditions;
   ```

## Rollback Plan

If something goes wrong:

1. **Database Backup:**
   ```bash
   pg_dump your_database > backup_before_owner_keys.sql
   ```

2. **Restore if Needed:**
   ```bash
   psql your_database < backup_before_owner_keys.sql
   ```

3. **Clear Owner Keys:**
   ```sql
   UPDATE expeditions
   SET owner_key = NULL, owner_user_id = NULL
   WHERE id IN (1, 2, 3, ...);  -- Specify expedition IDs
   ```

## Future Expeditions

**New expeditions automatically get owner keys** during creation via [services/expedition_service.py:63-86](../services/expedition_service.py:63-86):

```python
# Generate owner key for this expedition
try:
    owner_key = generate_owner_key(expedition.id, request.owner_chat_id)

    # Update expedition with owner key and user ID
    update_query = """
        UPDATE expeditions
        SET owner_key = %s, owner_user_id = %s
        WHERE id = %s
    """

    update_params = (owner_key, request.owner_chat_id, expedition.id)
    updated_result = self._execute_query(update_query, update_params, fetch_one=True)
```

## Troubleshooting

### Issue: "No module named 'utils.encryption'"

**Solution:**
```bash
cd C:\Users\rikrd\source\repos\NEWBOT
python migrations/backfill_expedition_owner_keys.py
```

### Issue: "Failed to generate owner key"

**Check:**
1. `utils/encryption.py` exists
2. `generate_owner_key()` function is defined
3. All dependencies installed (`pip install -r requirements.txt`)

### Issue: "Database connection failed"

**Check:**
1. `DATABASE_URL` environment variable set
2. PostgreSQL server running
3. Database credentials correct

## Summary

✅ **Migration Created**: [migrations/backfill_expedition_owner_keys.py](../migrations/backfill_expedition_owner_keys.py)

✅ **Safe to Run**: Dry run mode by default, transaction-based

✅ **Verifiable**: Built-in verification command

✅ **Future-Proof**: New expeditions automatically get keys

**Run the migration to enable pirate name decryption for all existing expeditions!**

```bash
# 1. Check what will be updated
python migrations/backfill_expedition_owner_keys.py --dry-run

# 2. Run the migration
python migrations/backfill_expedition_owner_keys.py

# 3. Verify success
python migrations/backfill_expedition_owner_keys.py --verify
```
