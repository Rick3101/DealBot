# Pirate Name Anonymization Security Audit

## Executive Summary

**CRITICAL SECURITY ISSUE**: The pirate name anonymization system is **NOT truly anonymizing** buyer identities. Original names are stored in **plain text** in the database, defeating the purpose of the anonymization system.

## Current Implementation Problems

### 1. Database Schema - `expedition_pirates` Table

**Location**: [database/schema.py:233-247](database/schema.py#L233-L247)

```sql
CREATE TABLE IF NOT EXISTS expedition_pirates (
    id SERIAL PRIMARY KEY,
    expedition_id INTEGER REFERENCES Expeditions(id) ON DELETE CASCADE,
    pirate_name VARCHAR(100) NOT NULL,
    original_name VARCHAR(100) NOT NULL,  -- PROBLEM: Stored in plain text
    chat_id BIGINT,
    user_id INTEGER REFERENCES Usuarios(id),
    encrypted_identity TEXT,  -- Present but not used properly
    role VARCHAR(20) DEFAULT 'participant',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE(expedition_id, pirate_name),
    UNIQUE(expedition_id, original_name)
);
```

**Issues**:
- `original_name` is stored in **plain text**
- Anyone with database access can see the real buyer names
- The `encrypted_identity` field exists but is not being used as the primary storage
- Anonymization is cosmetic only

### 2. Brambler Service - Storage Logic

**Location**: [services/brambler_service.py:314-327](services/brambler_service.py#L314-L327)

```python
if use_full_encryption:
    # OPTION A: Store ONLY encrypted identity, original_name is NULL
    cur.execute("""
        INSERT INTO expedition_pirates (original_name, pirate_name, expedition_id, encrypted_identity)
        VALUES (NULL, %s, %s, %s) RETURNING id
    """, (pirate_name, expedition_id, encrypted_identity))
else:
    # OPTION B (LEGACY): Store plain text with optional encrypted backup
    cur.execute("""
        INSERT INTO expedition_pirates (original_name, pirate_name, expedition_id, encrypted_identity)
        VALUES (%s, %s, %s, %s) RETURNING id
    """, (original_name, pirate_name, expedition_id, encrypted_identity))
```

**Issues**:
- Code has **two modes** but the secure mode (full encryption) is not being used by default
- The `use_full_encryption` flag is **not being enforced**
- Most code paths use legacy mode with plain text storage

### 3. Expedition Service - Pirate Creation

**Location**: [services/expedition_service.py:386-398](services/expedition_service.py#L386-L398)

```python
# Create new pirate record
create_pirate_query = """
    INSERT INTO expedition_pirates
    (expedition_id, pirate_name, original_name, role, status, joined_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
"""
pirate_result = self._execute_query(
    create_pirate_query,
    (expedition_id, request.pirate_name.strip(), request.consumer_name.strip(),
     'participant', 'active', now),
    fetch_one=True
)
```

**Issues**:
- **No encryption** when creating pirate records during consumption
- `original_name` is inserted directly in plain text
- This is the main code path for creating pirates and it completely bypasses encryption

### 4. Item Consumptions Tracking

**Location**: Multiple references in [services/expedition_service.py](services/expedition_service.py)

```python
# Line 688 in optimized query
COALESCE(ep.original_name, 'Unknown') as consumer_name,
```

**Issues**:
- Queries directly access `original_name` column
- API responses include plain text names
- No decryption logic because encryption isn't being used

## Security Impact

### HIGH SEVERITY Issues:

1. **Privacy Violation**: Any admin with database access can see real buyer names
2. **False Security**: System claims to anonymize but doesn't
3. **Compliance Risk**: If this is meant for privacy compliance, it fails completely
4. **Data Breach Risk**: Original names are exposed in:
   - Database tables
   - Database backups
   - Query logs
   - API responses
   - Error logs

## Required Changes for True Anonymization

### Phase 1: Database Schema Updates

1. **Make `original_name` nullable**:
```sql
ALTER TABLE expedition_pirates
ALTER COLUMN original_name DROP NOT NULL;
```

2. **Add CHECK constraint** to ensure either encrypted or plain text (transition period):
```sql
ALTER TABLE expedition_pirates
ADD CONSTRAINT original_name_xor_encrypted CHECK (
    (original_name IS NULL AND encrypted_identity IS NOT NULL AND encrypted_identity != '') OR
    (original_name IS NOT NULL)
);
```

3. **Target state** (after migration):
```sql
-- original_name should always be NULL
-- encrypted_identity should always have data
ALTER TABLE expedition_pirates
ADD CONSTRAINT enforce_encryption CHECK (
    original_name IS NULL AND
    encrypted_identity IS NOT NULL AND
    encrypted_identity != ''
);
```

### Phase 2: Code Updates

#### 1. Update Brambler Service

**File**: [services/brambler_service.py](services/brambler_service.py)

- **Remove legacy mode** (`use_full_encryption=False` path)
- **Always encrypt** original names before storage
- **Never store** `original_name` in plain text
- **Store only** `encrypted_identity`

#### 2. Update Expedition Service

**File**: [services/expedition_service.py](services/expedition_service.py)

- **Update pirate creation** (lines 386-402) to use encryption
- **Add encryption logic** before any INSERT INTO expedition_pirates
- **Get owner_key** from expedition before creating pirates
- **Never pass** `original_name` to database

#### 3. Update All Queries

**Files**: All services that query expedition_pirates

- **Remove** direct SELECT of `original_name`
- **Add decryption logic** where owner access is required
- **Return null** for `original_name` in API responses (except for owners)
- **Use pirate_name** for all display purposes

#### 4. Update API Endpoints

**Files**: [app.py](app.py) and all Flask routes

- **Add owner verification** before returning decrypted names
- **Filter out** `original_name` from non-owner responses
- **Add decrypt endpoint** for owners only

### Phase 3: Migration Strategy

1. **Create migration script**:
   - Encrypt all existing `original_name` values
   - Store in `encrypted_identity`
   - Set `original_name` to NULL
   - Verify all records migrated

2. **Backup strategy**:
   - Export current data before migration
   - Test migration on copy first
   - Verify decryption works

3. **Rollback plan**:
   - Keep original data in backup
   - Have script to restore if needed

## Recommended Action Plan

### Immediate (Day 1):
1. ✅ Document the issue (this file)
2. Create migration script
3. Test migration on development database

### Short-term (Day 2-3):
4. Update brambler_service.py to enforce encryption
5. Update expedition_service.py to use encryption
6. Add owner-only decryption endpoints
7. Test full flow with encryption

### Medium-term (Week 1):
8. Update all queries to use encrypted data
9. Update API responses to hide original names
10. Add comprehensive tests for encryption/decryption
11. Run migration on production database

### Long-term (Week 2+):
12. Remove legacy code paths
13. Add database constraint to enforce encryption
14. Security audit of all pirate name access points
15. Documentation update

## Testing Requirements

1. **Encryption Tests**:
   - Verify original names are encrypted before storage
   - Verify encrypted data is stored correctly
   - Verify database has no plain text original names

2. **Decryption Tests**:
   - Owner can decrypt their expedition pirates
   - Non-owners cannot decrypt
   - Admin key decryption works
   - Invalid keys fail gracefully

3. **API Tests**:
   - Non-owner sees only pirate names
   - Owner can request decryption
   - Decryption requires valid owner key
   - Responses don't leak original names

4. **Migration Tests**:
   - All existing pirates are encrypted
   - Decryption recovers original names
   - No data loss during migration
   - Rollback works correctly

## Related Files

- [database/schema.py](database/schema.py) - Table definition
- [services/brambler_service.py](services/brambler_service.py) - Pirate name management
- [services/expedition_service.py](services/expedition_service.py) - Consumption tracking
- [utils/encryption.py](utils/encryption.py) - Encryption utilities
- [models/expedition.py](models/expedition.py) - Data models

## Status

- [ ] Issue documented
- [ ] Migration script created
- [ ] Code updated for encryption
- [ ] Tests added
- [ ] Migration tested
- [ ] Production deployment planned
- [ ] Security audit completed

---

**Created**: 2025-10-17
**Severity**: CRITICAL
**Priority**: P0 - Immediate Action Required
