-- Backfill expedition_pirates table from existing expedition_assignments
-- This script creates pirate records for any assignments that don't have them

-- Insert missing pirate records from expedition_assignments
-- We only create records for unique (expedition_id, original_name) combinations
INSERT INTO expedition_pirates (
    expedition_id,
    pirate_name,
    original_name,
    role,
    status,
    joined_at
)
SELECT DISTINCT
    ea.expedition_id,
    -- Generate a simple pirate name from original name for existing records
    -- This will be a placeholder until proper pirate names are generated
    CONCAT('Pirate ', INITCAP(SPLIT_PART(ep_temp.original_name, ' ', 1))),
    ep_temp.original_name,
    'participant',
    'active',
    MIN(ea.assigned_at)
FROM expedition_assignments ea
CROSS JOIN LATERAL (
    -- Get the original name from the old consumer tracking
    -- We need to lookup the consumer from assignment records
    SELECT
        COALESCE(
            (SELECT original_name FROM expedition_pirates WHERE id = ea.pirate_id),
            'Unknown'
        ) as original_name
) ep_temp
WHERE ea.pirate_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM expedition_pirates ep2
      WHERE ep2.expedition_id = ea.expedition_id
        AND ep2.id = ea.pirate_id
  )
GROUP BY ea.expedition_id, ep_temp.original_name;

-- Output status
SELECT
    'Backfill complete' as status,
    COUNT(*) as pirates_created
FROM expedition_pirates
WHERE pirate_name LIKE 'Pirate %';
