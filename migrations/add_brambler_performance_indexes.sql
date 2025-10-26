-- Brambler Performance Optimization Migration
-- Created: 2025-10-25
-- Purpose: Add missing indexes to optimize Brambler Management Console queries

-- ============================================================================
-- CRITICAL PERFORMANCE INDEXES FOR BRAMBLER CONSOLE
-- ============================================================================

-- Index for expedition_pirates JOIN with expeditions (used in get_all_expedition_pirates)
-- This query was causing 10s timeouts due to full table scans
CREATE INDEX IF NOT EXISTS idx_expeditionpirates_expedition_owner
    ON expedition_pirates(expedition_id)
    INCLUDE (id, pirate_name, original_name, encrypted_identity, joined_at);

-- Composite index for expedition_items JOIN with expeditions (used in get_all_encrypted_items)
CREATE INDEX IF NOT EXISTS idx_expeditionitems_expedition_encrypted
    ON expedition_items(expedition_id)
    WHERE encrypted_mapping IS NOT NULL AND encrypted_mapping != '';

-- Index for filtering encrypted items by owner_chat_id (avoids scanning all expeditions)
CREATE INDEX IF NOT EXISTS idx_expeditions_owner_with_fields
    ON expeditions(owner_chat_id)
    INCLUDE (id, name);

-- Index for expedition pirates with encryption filtering
CREATE INDEX IF NOT EXISTS idx_expeditionpirates_encrypted
    ON expedition_pirates(expedition_id, encrypted_identity)
    WHERE encrypted_identity IS NOT NULL AND encrypted_identity != '';

-- Index for expedition items with encryption and status filtering
CREATE INDEX IF NOT EXISTS idx_expeditionitems_encrypted_status
    ON expedition_items(expedition_id, encrypted_mapping, item_status);

-- ============================================================================
-- ANALYTICS AND REPORTING INDEXES
-- ============================================================================

-- Index for expedition list queries with status filtering
CREATE INDEX IF NOT EXISTS idx_expeditions_list_optimization
    ON expeditions(status, owner_chat_id, created_at DESC)
    INCLUDE (id, name, deadline, completed_at);

-- Index for consumption queries by expedition
CREATE INDEX IF NOT EXISTS idx_consumptions_expedition_optimized
    ON item_consumptions(expedition_id, payment_status)
    INCLUDE (consumer_name, pirate_name, quantity_consumed, total_cost, consumed_at);

-- ============================================================================
-- QUERY HINTS FOR POSTGRES PLANNER
-- ============================================================================

-- Analyze tables to update statistics for better query planning
ANALYZE expedition_pirates;
ANALYZE expedition_items;
ANALYZE expeditions;
ANALYZE item_consumptions;

-- ============================================================================
-- MATERIALIZED VIEW FOR DASHBOARD (Optional - for heavy traffic)
-- ============================================================================

-- Uncomment if you need ultra-fast dashboard loading (refreshed periodically)
-- CREATE MATERIALIZED VIEW IF NOT EXISTS mv_expedition_dashboard AS
-- SELECT
--     e.id,
--     e.name,
--     e.owner_chat_id,
--     e.status,
--     e.deadline,
--     e.created_at,
--     COUNT(DISTINCT ep.id) as pirate_count,
--     COUNT(DISTINCT ei.id) as item_count,
--     COALESCE(SUM(ic.total_cost), 0) as total_value
-- FROM expeditions e
-- LEFT JOIN expedition_pirates ep ON e.id = ep.expedition_id
-- LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
-- LEFT JOIN item_consumptions ic ON e.id = ic.expedition_id
-- GROUP BY e.id, e.name, e.owner_chat_id, e.status, e.deadline, e.created_at;

-- CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_expedition_dashboard_id ON mv_expedition_dashboard(id);
-- CREATE INDEX IF NOT EXISTS idx_mv_expedition_dashboard_owner ON mv_expedition_dashboard(owner_chat_id);

-- ============================================================================
-- VACUUM AND MAINTENANCE
-- ============================================================================

-- Clean up dead tuples for better performance
VACUUM ANALYZE expedition_pirates;
VACUUM ANALYZE expedition_items;
VACUUM ANALYZE expeditions;
