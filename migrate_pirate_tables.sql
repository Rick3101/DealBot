-- Pirate Tables Migration Script
-- Migrates data from pirate_names to expedition_pirates table
-- Safe to run multiple times (uses ON CONFLICT DO NOTHING)

-- Step 1: Migrate expedition-specific pirate names
INSERT INTO expedition_pirates (
    expedition_id,
    pirate_name,
    original_name,
    encrypted_identity,
    joined_at
)
SELECT
    expedition_id,
    pirate_name,
    original_name,
    COALESCE(encrypted_mapping, ''),
    created_at
FROM pirate_names
WHERE expedition_id IS NOT NULL
ON CONFLICT (expedition_id, original_name) DO NOTHING;

-- Step 2: Verify migration counts
SELECT
    'pirate_names (expedition-specific)' as source,
    COUNT(*) as count
FROM pirate_names
WHERE expedition_id IS NOT NULL
UNION ALL
SELECT
    'expedition_pirates' as source,
    COUNT(*) as count
FROM expedition_pirates
UNION ALL
SELECT
    'pirate_names (global mappings)' as source,
    COUNT(*) as count
FROM pirate_names
WHERE expedition_id IS NULL
UNION ALL
SELECT
    'item_mappings' as source,
    COUNT(*) as count
FROM item_mappings;

-- Step 3: Show duplicate check (should be 0 if migration is complete)
SELECT
    'Potential duplicates in pirate_names' as check_type,
    COUNT(*) as count
FROM pirate_names
WHERE expedition_id IS NOT NULL
AND (expedition_id, original_name) IN (
    SELECT expedition_id, original_name
    FROM expedition_pirates
);
