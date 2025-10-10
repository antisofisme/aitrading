-- TimescaleDB Migration: Add UNIQUE Constraint to market_ticks
-- Prevents duplicate ticks with same (symbol, timestamp)
-- Solves 23.7% duplication issue

-- ========================================
-- STEP 1: Check current duplicates
-- ========================================

SELECT
    'Current State' as status,
    COUNT(*) as total_ticks,
    COUNT(DISTINCT (symbol, timestamp)) as unique_ticks,
    ROUND(100.0 * (COUNT(*) - COUNT(DISTINCT (symbol, timestamp))) / COUNT(*), 2) as duplicate_percentage
FROM market_ticks;

-- ========================================
-- STEP 2: Create deduplicated table (RECOMMENDED)
-- ========================================

-- Option A: Create new table with unique constraint
CREATE TABLE IF NOT EXISTS market_ticks_new (
    LIKE market_ticks INCLUDING ALL
);

-- Add unique constraint to new table
ALTER TABLE market_ticks_new
ADD CONSTRAINT unique_tick_timestamp
UNIQUE (symbol, timestamp);

-- Copy unique data (keep latest based on created_at or bid/ask)
INSERT INTO market_ticks_new
SELECT DISTINCT ON (symbol, timestamp)
    *
FROM market_ticks
ORDER BY symbol, timestamp, id DESC;  -- Keep latest by id

-- ========================================
-- STEP 3: Verify new table
-- ========================================

SELECT
    'market_ticks (OLD)' as table_name,
    COUNT(*) as total_rows
FROM market_ticks

UNION ALL

SELECT
    'market_ticks_new (NEW)' as table_name,
    COUNT(*) as total_rows
FROM market_ticks_new;

-- Check for any missed symbols
SELECT symbol, COUNT(*) as tick_count
FROM market_ticks
GROUP BY symbol
ORDER BY symbol

EXCEPT

SELECT symbol, COUNT(*) as tick_count
FROM market_ticks_new
GROUP BY symbol
ORDER BY symbol;

-- ========================================
-- STEP 4: Rename tables (EXECUTE MANUALLY!)
-- ========================================

-- IMPORTANT: Run these ONE AT A TIME after verification!

-- Rename old table to backup
-- ALTER TABLE market_ticks RENAME TO market_ticks_old;

-- Rename new table to active
-- ALTER TABLE market_ticks_new RENAME TO market_ticks;

-- ========================================
-- STEP 5: Drop old table (After 7 days)
-- ========================================

-- IMPORTANT: Only after confirming new table works!
-- DROP TABLE IF EXISTS market_ticks_old;

-- ========================================
-- EXPECTED RESULTS
-- ========================================

-- Before:
-- - Total ticks: ~2,477,392
-- - Unique ticks: ~1,892,392
-- - Duplicates: ~585,000 (23.7%)

-- After:
-- - Total ticks: ~1,892,392
-- - Unique ticks: ~1,892,392
-- - Duplicates: 0 (0%)
-- - Storage saved: ~23.7%

-- ========================================
-- ALTERNATIVE: Add constraint to existing table
-- ========================================

-- Option B: Try to add constraint directly (may fail if duplicates exist)
-- This will FAIL if there are duplicates!

-- ALTER TABLE market_ticks
-- ADD CONSTRAINT unique_tick_timestamp
-- UNIQUE (symbol, timestamp);

-- If this fails, you MUST use Option A (create new table)
