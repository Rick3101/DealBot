-- Migration Script: Remove pirate_names table and migrate to expedition_pirates
-- Date: 2025-11-03
-- Purpose: Consolidate all pirate name management into expedition_pirates table

-- ============================================================================
-- STEP 1: Migrate pirate_names records to expedition_pirates
-- ============================================================================

-- Migrate records that don't already exist in expedition_pirates
INSERT INTO expedition_pirates
    (expedition_id, pirate_name, original_name, encrypted_identity,
     joined_at, status, role)
SELECT
    pn.expedition_id,
    pn.pirate_name,
    pn.original_name,
    pn.encrypted_mapping as encrypted_identity,  -- Map encrypted_mapping to encrypted_identity
    pn.created_at as joined_at,
    'active' as status,
    'participant' as role
FROM pirate_names pn
WHERE NOT EXISTS (
    -- Avoid duplicates
    SELECT 1 FROM expedition_pirates ep
    WHERE ep.expedition_id = pn.expedition_id
      AND ep.pirate_name = pn.pirate_name
)
AND pn.expedition_id IS NOT NULL;  -- Only migrate expedition-specific records

-- ============================================================================
-- STEP 2: Verification queries (uncomment to check)
-- ============================================================================

-- Check counts before and after
-- SELECT 'pirate_names' as table_name, COUNT(*) FROM pirate_names WHERE expedition_id IS NOT NULL
-- UNION ALL
-- SELECT 'expedition_pirates', COUNT(*) FROM expedition_pirates;

-- Check for unmigrated records
-- SELECT COUNT(*) as unmigrated_count
-- FROM pirate_names pn
-- WHERE pn.expedition_id IS NOT NULL
--   AND NOT EXISTS (
--     SELECT 1 FROM expedition_pirates ep
--     WHERE ep.expedition_id = pn.expedition_id
--       AND ep.pirate_name = pn.pirate_name
--   );

-- ============================================================================
-- STEP 3: Drop pirate_names table (DESTRUCTIVE - uncomment when ready)
-- ============================================================================

-- WARNING: This is destructive! Make sure migration succeeded first!

-- Drop indexes
-- DROP INDEX IF EXISTS idx_piratenames_expedition;
-- DROP INDEX IF EXISTS idx_piratenames_original;
-- DROP INDEX IF EXISTS idx_piratenames_exp_original;

-- Drop table
-- DROP TABLE IF EXISTS pirate_names CASCADE;

-- ============================================================================
-- Migration Complete!
-- ============================================================================
