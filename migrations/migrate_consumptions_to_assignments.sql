-- Migration Script: Remove item_consumptions table and migrate to expedition_assignments
-- Date: 2025-11-03
-- Purpose: Consolidate consumption tracking into the modern assignment-based architecture

-- ============================================================================
-- STEP 1: Migrate existing item_consumptions data to expedition_assignments
-- ============================================================================

-- First, ensure we have pirate records for all consumers in item_consumptions
INSERT INTO expedition_pirates (expedition_id, pirate_name, original_name, joined_at, status, role)
SELECT DISTINCT
    ic.expedition_id,
    ic.pirate_name,
    ic.consumer_name,
    ic.consumed_at,
    'active',
    'participant'
FROM item_consumptions ic
WHERE NOT EXISTS (
    SELECT 1 FROM expedition_pirates ep
    WHERE ep.expedition_id = ic.expedition_id
    AND ep.pirate_name = ic.pirate_name
)
ON CONFLICT (expedition_id, pirate_name) DO NOTHING;

-- Migrate consumption records to expedition_assignments
INSERT INTO expedition_assignments
    (expedition_id, pirate_id, expedition_item_id, assigned_quantity,
     consumed_quantity, unit_price, total_cost, assignment_status,
     payment_status, assigned_at, completed_at)
SELECT
    ic.expedition_id,
    ep.id as pirate_id,
    ic.expedition_item_id,
    ic.quantity_consumed,  -- assigned = consumed for completed assignments
    ic.quantity_consumed,
    ic.unit_price,
    ic.total_cost,
    'completed',  -- All legacy consumptions are completed
    ic.payment_status,
    ic.consumed_at,
    ic.consumed_at  -- completed_at = consumed_at for legacy data
FROM item_consumptions ic
JOIN expedition_pirates ep ON
    ep.expedition_id = ic.expedition_id
    AND ep.pirate_name = ic.pirate_name
WHERE NOT EXISTS (
    -- Avoid duplicates if migration is run multiple times
    SELECT 1 FROM expedition_assignments ea
    WHERE ea.expedition_id = ic.expedition_id
        AND ea.pirate_id = ep.id
        AND ea.expedition_item_id = ic.expedition_item_id
        AND ea.consumed_quantity = ic.quantity_consumed
        AND ea.assigned_at = ic.consumed_at
);

-- ============================================================================
-- STEP 2: Migrate payment records to expedition_payments
-- ============================================================================

-- Create payment records for assignments that have been paid (full or partial)
INSERT INTO expedition_payments
    (expedition_id, assignment_id, pirate_id, payment_amount,
     payment_status, processed_at, notes)
SELECT
    ic.expedition_id,
    ea.id as assignment_id,
    ea.pirate_id,
    ic.amount_paid,
    'completed',
    ic.consumed_at,  -- Use consumed_at as processed_at
    'Migrated from item_consumptions table'
FROM item_consumptions ic
JOIN expedition_pirates ep ON
    ep.expedition_id = ic.expedition_id
    AND ep.pirate_name = ic.pirate_name
JOIN expedition_assignments ea ON
    ea.expedition_id = ic.expedition_id
    AND ea.pirate_id = ep.id
    AND ea.expedition_item_id = ic.expedition_item_id
    AND ea.assigned_at = ic.consumed_at
WHERE ic.amount_paid > 0
AND NOT EXISTS (
    -- Avoid duplicates
    SELECT 1 FROM expedition_payments epay
    WHERE epay.assignment_id = ea.id
        AND epay.payment_amount = ic.amount_paid
);

-- ============================================================================
-- STEP 3: Verification queries (run these to check migration)
-- ============================================================================

-- Check counts before migration
-- SELECT 'item_consumptions' as table_name, COUNT(*) as record_count FROM item_consumptions
-- UNION ALL
-- SELECT 'expedition_assignments', COUNT(*) FROM expedition_assignments
-- UNION ALL
-- SELECT 'expedition_payments', COUNT(*) FROM expedition_payments;

-- Check for unmigrated records (should return 0 after migration)
-- SELECT COUNT(*) as unmigrated_consumptions
-- FROM item_consumptions ic
-- WHERE NOT EXISTS (
--     SELECT 1 FROM expedition_assignments ea
--     JOIN expedition_pirates ep ON ea.pirate_id = ep.id
--     WHERE ea.expedition_id = ic.expedition_id
--         AND ep.pirate_name = ic.pirate_name
--         AND ea.expedition_item_id = ic.expedition_item_id
--         AND ea.assigned_at = ic.consumed_at
-- );

-- ============================================================================
-- STEP 4: Drop item_consumptions table and related indexes (DESTRUCTIVE)
-- ============================================================================

-- WARNING: This step is destructive! Run verification queries first!
-- Uncomment these lines when ready to drop the table:

-- DROP INDEX IF EXISTS idx_itemconsumptions_expedition;
-- DROP INDEX IF EXISTS idx_itemconsumptions_expeditionitem;
-- DROP INDEX IF EXISTS idx_itemconsumptions_consumer;
-- DROP INDEX IF EXISTS idx_itemconsumptions_payment;
-- DROP INDEX IF EXISTS idx_itemconsumptions_consumed;
-- DROP INDEX IF EXISTS idx_itemconsumptions_payment_date;
-- DROP INDEX IF EXISTS idx_itemconsumptions_exp_consumer_date;
-- DROP INDEX IF EXISTS idx_itemconsumptions_exp_payment_cost;
-- DROP INDEX IF EXISTS idx_itemconsumptions_date_expedition;
-- DROP INDEX IF EXISTS idx_consumptions_expedition_payment_consumed;
-- DROP INDEX IF EXISTS idx_brambler_consumptions_expedition;

-- DROP TABLE IF EXISTS item_consumptions CASCADE;

-- ============================================================================
-- Migration Complete!
-- ============================================================================
