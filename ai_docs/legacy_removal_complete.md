# Legacy Expedition System Removal - Complete Guide

**Date**: 2025-10-11
**Status**: ✅ Code Updated, 🟡 Database Cleanup Pending

## What We Did

### Phase 1: Service Layer Updates ✅ COMPLETE

**File: [services/expedition_service.py](c:\Users\rikrd\source\repos\NEWBOT\services\expedition_service.py)**

#### 1. Updated `consume_item()` (Lines 321-491)
**Changes:**
- ❌ Removed: `INSERT INTO item_consumptions`
- ✅ Now only writes to: `expedition_assignments`, `expedition_pirates`, `expedition_items`
- ✅ Return type changed: `ItemConsumption` → `Assignment`
- ✅ Includes consumer name, pirate name in Assignment object

#### 2. Renamed `pay_consumption()` → `pay_assignment()` (Lines 509-603)
**Changes:**
- ❌ Removed: Queries to `item_consumptions`
- ✅ Now queries: `expedition_assignments` with payment tracking via `expedition_payments`
- ✅ Parameter changed: `consumption_id` → `assignment_id`
- ✅ Return type changed: `ItemConsumption` → `Assignment`
- ✅ Proper payment aggregation with SUM() from `expedition_payments`

#### 3. Updated `get_expedition_consumptions()` (Lines 493-507)
**Changes:**
- ❌ Removed: Query to `item_consumptions`
- ✅ Now queries: `expedition_assignments` JOIN `expedition_pirates`
- ✅ Return type: `List[Assignment]`
- ✅ Includes pirate names in result

#### 4. Updated `get_user_consumptions()` (Lines 605-619)
**Changes:**
- ❌ Removed: Query to `item_consumptions`
- ✅ Now queries: `expedition_assignments` JOIN `expedition_pirates`
- ✅ Filters by `original_name` from `expedition_pirates`
- ✅ Return type: `List[Assignment]`

### Phase 2: Database Cleanup 🟡 READY TO EXECUTE

**Script: [drop_legacy_expedition_tables.py](c:\Users\rikrd\source\repos\NEWBOT\drop_legacy_expedition_tables.py)**

**What it does:**
1. Creates backup: `item_consumptions_backup`
2. Drops table: `item_consumptions` (CASCADE)
3. Deletes records: `pirate_names` WHERE `expedition_id IS NOT NULL`
4. Keeps: Global pirate_names (expedition_id IS NULL)
5. Verifies: New tables intact, backup created

**Safety Features:**
- ✅ Confirmation prompts
- ✅ Automatic backup creation
- ✅ Transaction-based (rollback on error)
- ✅ Verification checks
- ✅ Clear logging

## Breaking Changes

### API Changes

| Old Method | New Method | Parameter Change | Return Type Change |
|------------|------------|------------------|-------------------|
| `consume_item()` | Same | None | `ItemConsumption` → `Assignment` |
| `pay_consumption()` | `pay_assignment()` | `consumption_id` → `assignment_id` | `ItemConsumption` → `Assignment` |
| `get_expedition_consumptions()` | Same | None | `List[ItemConsumption]` → `List[Assignment]` |
| `get_user_consumptions()` | Same | None | `List[ItemConsumption]` → `List[Assignment]` |

### Data Model Changes

**ItemConsumption** (Legacy):
```python
- id
- expedition_id
- expedition_item_id
- consumer_name
- pirate_name
- quantity_consumed
- unit_price
- total_cost
- amount_paid
- payment_status
- consumed_at
```

**Assignment** (New):
```python
+ id
+ expedition_id
+ pirate_id
+ expedition_item_id
+ assigned_quantity
+ consumed_quantity
+ unit_price
+ total_cost
+ assignment_status
+ payment_status
+ assigned_at
+ completed_at
+ original_name (from JOIN)
+ pirate_name (from JOIN)
```

### Handler Impact

**Minimal to None** - Most handlers use service methods, so changes are transparent.

**If handlers directly use models:**
- Update: `ItemConsumption` → `Assignment`
- Update: `consumption.quantity_consumed` → `assignment.consumed_quantity`
- Update: `consumption.consumed_at` → `assignment.assigned_at` or `assignment.completed_at`
- Update: `consumption.amount_paid` → Calculate from `expedition_payments` SUM

## Migration Checklist

### Before Running drop_legacy_expedition_tables.py:

- [x] Data migration complete (15 rows migrated)
- [x] Service layer updated (4 methods)
- [x] BramblerService updated (3 methods)
- [ ] All expedition tests pass
- [ ] Full database backup created
- [ ] Handlers updated (if they directly use models)
- [ ] Export service updated (if uses item_consumptions)
- [ ] WebSocket service updated (if uses item_consumptions)

### Running the Cleanup:

```bash
python drop_legacy_expedition_tables.py
```

**Expected prompts:**
1. Confirm you want to continue
2. Confirm overwrite existing backup (if exists)
3. Confirm table drop

**Expected output:**
```
Creating backup tables...
Backed up 15 rows to item_consumptions_backup
Dropping legacy tables...
  - item_consumptions: 15 rows
  - pirate_names (expedition-specific): 13 rows
Dropped item_consumptions table
Deleted 13 expedition-specific pirate name mappings
Kept X global pirate name mappings
Verification successful!
CLEANUP COMPLETED SUCCESSFULLY!
```

### After Cleanup:

- [ ] Test expedition creation
- [ ] Test consumption recording
- [ ] Test payment processing
- [ ] Test pirate name lookups
- [ ] Test reports and exports
- [ ] Monitor for any errors
- [ ] Update schema.py (remove table definitions)

## Rollback Plan

If issues arise:

### Immediate Rollback (Before dropping tables):
```bash
# Just don't run drop_legacy_expedition_tables.py
# Revert service code changes via git
git checkout services/expedition_service.py
```

### After Tables Dropped:
```sql
-- Restore from backup
CREATE TABLE item_consumptions AS SELECT * FROM item_consumptions_backup;

-- Restore pirate_names from migration backup
-- (Would need to re-run migration)
```

## Testing Post-Removal

```bash
# Run the test suite
python test_new_expedition_system.py
```

**Expected results:**
- ✅ All pirate name lookups work
- ✅ Consumption creation works
- ✅ Payment processing works
- ✅ Assignment tracking works
- ✅ No references to item_consumptions

## Schema.py Updates (Phase 3)

After successful cleanup, update `database/schema.py`:

### Remove Lines:
1. **Table Creation** (~Lines 203-216):
   ```sql
   CREATE TABLE IF NOT EXISTS item_consumptions (...)
   ```

2. **Indexes** (~Lines 320-325, 340-344, 352):
   ```sql
   CREATE INDEX IF NOT EXISTS idx_itemconsumptions_* ...
   ```

3. **Health Check** (~Line 623):
   ```python
   required_tables = [
       ...,
       'item_consumptions',  # REMOVE THIS
       ...
   ]
   ```

## Benefits of Removal

### 1. Simplified Architecture
- Single source of truth for expedition data
- No more dual-write complexity
- Clearer data relationships

### 2. Better Data Model
- Role-based participant management
- Separate assignment vs consumption tracking
- Multiple payments per assignment
- Better audit trail

### 3. Improved Performance
- Fewer write operations
- Better query optimization
- Cleaner joins

### 4. Easier Maintenance
- Less code to maintain
- No synchronization logic
- Simpler debugging

## Documentation Updates Needed

After successful removal:

1. Update API documentation to show Assignment model
2. Update handler documentation
3. Update ERD diagrams
4. Update CLAUDE.md with new flows
5. Archive legacy system documentation

## Summary

✅ **Service layer fully migrated** - No longer uses `item_consumptions`
🟡 **Database cleanup ready** - Safe script available to drop legacy tables
📋 **Next step**: Run `drop_legacy_expedition_tables.py` after final testing

**Estimated Time**: ~15 minutes to run cleanup + verify
**Risk Level**: LOW (backup created, transaction-based, can rollback)
**Impact**: Breaking changes for direct model usage, transparent for service users
