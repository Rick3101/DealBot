-- Fix owner_user_id column type to support large Telegram chat IDs
-- Telegram chat IDs can exceed 32-bit INTEGER range (max: 2,147,483,647)
-- Change to BIGINT to support full range of Telegram chat IDs

-- Change column type from INTEGER to BIGINT
ALTER TABLE expeditions
ALTER COLUMN owner_user_id TYPE BIGINT;
