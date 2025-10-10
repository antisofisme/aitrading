-- ClickHouse Schema Migration: MergeTree → ReplacingMergeTree
-- This migration solves the 178x duplication issue by enabling automatic deduplication
-- Based on composite key: (symbol, timeframe, timestamp)

-- ========================================
-- STEP 1: Create new table with ReplacingMergeTree
-- ========================================

-- ReplacingMergeTree will:
-- 1. Auto-deduplicate rows with same ORDER BY key (symbol, timeframe, timestamp)
-- 2. Keep the row with latest ingested_at value
-- 3. Apply deduplication during OPTIMIZE TABLE FINAL or background merge

CREATE TABLE IF NOT EXISTS aggregates_new
(
    symbol String,
    timeframe String,
    timestamp DateTime,
    timestamp_ms Int64,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume UInt64,
    vwap Float64,
    range_pips Float64,
    body_pips Float64,
    start_time DateTime,
    end_time DateTime,
    source String,
    event_type String,
    indicators String,  -- JSON string of technical indicators
    ingested_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(ingested_at)  -- Use ingested_at as version column
PARTITION BY (symbol, toYYYYMM(timestamp))
ORDER BY (symbol, timeframe, timestamp)
SETTINGS index_granularity = 8192;

-- ========================================
-- STEP 2: Copy unique data from old table
-- ========================================

-- This query copies data while keeping only the latest version of each record
-- The ORDER BY ingested_at DESC ensures we keep the newest data for duplicates

INSERT INTO aggregates_new
SELECT
    symbol,
    timeframe,
    timestamp,
    timestamp_ms,
    open,
    high,
    low,
    close,
    volume,
    vwap,
    range_pips,
    body_pips,
    start_time,
    end_time,
    source,
    event_type,
    indicators,
    ingested_at
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY symbol, timeframe, timestamp
               ORDER BY ingested_at DESC
           ) as rn
    FROM aggregates
) t
WHERE rn = 1;

-- ========================================
-- STEP 3: Verify data integrity
-- ========================================

-- Check row counts
SELECT
    'Original table' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT (symbol, timeframe, timestamp)) as unique_combinations
FROM aggregates

UNION ALL

SELECT
    'New table' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT (symbol, timeframe, timestamp)) as unique_combinations
FROM aggregates_new;

-- Check data range
SELECT
    'Original table' as table_name,
    symbol,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest,
    COUNT(*) as rows
FROM aggregates
GROUP BY symbol
ORDER BY symbol

UNION ALL

SELECT
    'New table' as table_name,
    symbol,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest,
    COUNT(*) as rows
FROM aggregates_new
GROUP BY symbol
ORDER BY symbol;

-- ========================================
-- STEP 4: Rename tables (EXECUTE MANUALLY AFTER VERIFICATION)
-- ========================================

-- IMPORTANT: Run these commands ONE AT A TIME after verifying data integrity above!

-- Rename old table to backup
-- RENAME TABLE aggregates TO aggregates_old;

-- Rename new table to active
-- RENAME TABLE aggregates_new TO aggregates;

-- ========================================
-- STEP 5: Optimize new table (apply deduplication)
-- ========================================

-- This forces ReplacingMergeTree to merge parts and deduplicate
-- Run this AFTER renaming tables

-- OPTIMIZE TABLE aggregates FINAL;

-- ========================================
-- STEP 6: Verify new table
-- ========================================

-- Check for remaining duplicates (should be 0)
-- SELECT
--     symbol,
--     timeframe,
--     timestamp,
--     COUNT(*) as count
-- FROM aggregates FINAL
-- GROUP BY symbol, timeframe, timestamp
-- HAVING count > 1
-- LIMIT 100;

-- Check storage size
-- SELECT
--     table,
--     formatReadableSize(sum(bytes)) as size,
--     sum(rows) as rows,
--     max(modification_time) as latest_modification
-- FROM system.parts
-- WHERE table IN ('aggregates', 'aggregates_old')
--   AND active = 1
-- GROUP BY table;

-- ========================================
-- STEP 7: Drop old table (AFTER VERIFICATION)
-- ========================================

-- IMPORTANT: Only run this after confirming new table works correctly!
-- Keep backup for at least 7 days

-- DROP TABLE IF EXISTS aggregates_old;

-- ========================================
-- EXPECTED RESULTS
-- ========================================

-- Before migration:
-- - Total rows: 91M
-- - Unique combinations: ~35M
-- - Duplication rate: 260% (2.6x)
-- - Storage: 5.3 GB

-- After migration:
-- - Total rows: ~35M (60% reduction)
-- - Unique combinations: ~35M (100%)
-- - Duplication rate: 100% (no duplicates)
-- - Storage: ~2.0 GB (62% reduction)

-- Query performance:
-- - 2-3x faster queries (no scanning duplicates)
-- - Use "SELECT ... FROM aggregates FINAL" for guaranteed unique results
-- - Background merges will auto-deduplicate new duplicates

-- ========================================
-- TROUBLESHOOTING
-- ========================================

-- If migration fails or takes too long:
-- 1. Drop aggregates_new and recreate
-- 2. Copy data in smaller batches (by date range or symbol)
-- 3. Use PARTITION-level operations for faster processing

-- Example: Copy one partition at a time
-- INSERT INTO aggregates_new
-- SELECT * FROM aggregates
-- WHERE symbol = 'EUR/USD' AND toYYYYMM(timestamp) = 202510;
