-- ============================================================================
-- ClickHouse Schema: historical_ticks (Historical Tick Data)
-- ============================================================================
-- Purpose: Store historical tick data from Dukascopy backfill
-- Retention: 10 years (long-term storage for ML training)
-- Engine: MergeTree with partitioning by month + symbol
-- ============================================================================

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS suho_analytics.historical_ticks;

-- Create historical_ticks table (6 columns - same as live_ticks)
CREATE TABLE IF NOT EXISTS suho_analytics.historical_ticks (
    -- Timestamp (primary ordering key)
    time DateTime64(3, 'UTC') NOT NULL,

    -- Symbol (trading pair)
    symbol String NOT NULL,

    -- Price data (5 decimal places for forex precision)
    bid Decimal(18,5) NOT NULL,
    ask Decimal(18,5) NOT NULL,

    -- Original timestamp from data source (milliseconds since epoch)
    timestamp_ms UInt64 NOT NULL,

    -- Ingestion metadata
    ingested_at DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), symbol)
ORDER BY (symbol, time)
TTL toDateTime(time) + INTERVAL 10 YEAR
SETTINGS index_granularity = 8192;

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Index for time range queries
ALTER TABLE suho_analytics.historical_ticks
ADD INDEX idx_time time TYPE minmax GRANULARITY 1;

-- Index for timestamp_ms queries (if needed)
ALTER TABLE suho_analytics.historical_ticks
ADD INDEX idx_timestamp_ms timestamp_ms TYPE minmax GRANULARITY 1;

-- ============================================================================
-- Materialized Views (Statistics)
-- ============================================================================

-- Daily statistics per symbol
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.historical_ticks_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (symbol, day)
AS SELECT
    toDate(time) AS day,
    symbol,
    COUNT(*) AS tick_count,
    MIN(time) AS oldest_tick,
    MAX(time) AS newest_tick,
    AVG(bid) AS avg_bid,
    AVG(ask) AS avg_ask,
    AVG(ask - bid) AS avg_spread,
    MAX(ask - bid) AS max_spread,
    MIN(ask - bid) AS min_spread
FROM suho_analytics.historical_ticks
GROUP BY day, symbol;

-- Monthly statistics per symbol
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.historical_ticks_monthly
ENGINE = SummingMergeTree()
PARTITION BY toYear(month)
ORDER BY (symbol, month)
AS SELECT
    toStartOfMonth(time) AS month,
    symbol,
    COUNT(*) AS tick_count,
    MIN(time) AS oldest_tick,
    MAX(time) AS newest_tick,
    AVG(bid) AS avg_bid,
    AVG(ask) AS avg_ask,
    AVG(ask - bid) AS avg_spread,
    formatReadableSize(COUNT(*) * 64) AS estimated_size  -- Approximate row size
FROM suho_analytics.historical_ticks
GROUP BY month, symbol;

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Calculate mid price on-the-fly
CREATE FUNCTION IF NOT EXISTS get_tick_mid(bid Decimal(18,5), ask Decimal(18,5))
RETURNS Decimal(18,5)
AS (bid + ask) / 2;

-- Calculate spread on-the-fly
CREATE FUNCTION IF NOT EXISTS get_tick_spread(bid Decimal(18,5), ask Decimal(18,5))
RETURNS Decimal(18,5)
AS ask - bid;

-- ============================================================================
-- Verification Queries (Post-Deployment)
-- ============================================================================

-- Example query 1: Check data coverage per symbol
-- SELECT
--     symbol,
--     COUNT(*) AS tick_count,
--     MIN(time) AS oldest,
--     MAX(time) AS newest,
--     dateDiff('day', MIN(time), MAX(time)) AS days_span,
--     AVG(ask - bid) AS avg_spread,
--     formatReadableSize(COUNT(*) * 64) AS approx_size
-- FROM suho_analytics.historical_ticks
-- GROUP BY symbol
-- ORDER BY tick_count DESC;

-- Example query 2: Check ticks per day
-- SELECT
--     toDate(time) AS day,
--     symbol,
--     COUNT(*) AS ticks_per_day
-- FROM suho_analytics.historical_ticks
-- WHERE symbol = 'EURUSD'
--   AND time >= '2023-01-01' AND time < '2023-02-01'
-- GROUP BY day, symbol
-- ORDER BY day;

-- Example query 3: Sample ticks (verify no mid/spread columns)
-- SELECT *
-- FROM suho_analytics.historical_ticks
-- WHERE symbol = 'EURUSD'
-- ORDER BY time DESC
-- LIMIT 10;

-- Example query 4: Check spread distribution
-- SELECT
--     symbol,
--     quantile(0.50)(ask - bid) AS median_spread,
--     quantile(0.95)(ask - bid) AS p95_spread,
--     quantile(0.99)(ask - bid) AS p99_spread,
--     MAX(ask - bid) AS max_spread
-- FROM suho_analytics.historical_ticks
-- WHERE time >= now() - INTERVAL 7 DAY
-- GROUP BY symbol;

-- ============================================================================
-- Schema Documentation
-- ============================================================================

COMMENT COLUMN suho_analytics.historical_ticks.time IS 'Tick timestamp';
COMMENT COLUMN suho_analytics.historical_ticks.symbol IS 'Trading pair (e.g., EURUSD, XAUUSD)';
COMMENT COLUMN suho_analytics.historical_ticks.bid IS 'Bid price (5 decimal precision)';
COMMENT COLUMN suho_analytics.historical_ticks.ask IS 'Ask price (5 decimal precision)';
COMMENT COLUMN suho_analytics.historical_ticks.timestamp_ms IS 'Original millisecond timestamp from Dukascopy';
COMMENT COLUMN suho_analytics.historical_ticks.ingested_at IS 'Ingestion timestamp (for tracking)';

-- ============================================================================
-- Data Sources
-- ============================================================================
-- Source: Dukascopy historical data (.bi5 files)
-- Collector: dukascopy-historical-downloader service
-- Transport: NATS (market.{symbol}.tick)
-- Writer: data-bridge → clickhouse_writer.py
-- Coverage: 2015-01-01 to present (backfill in progress)
-- Update Frequency: One-time backfill + monthly updates
-- ============================================================================

-- ============================================================================
-- Migration Notes
-- ============================================================================
-- v1.8.0 (2025-10-18):
-- - Renamed from ticks to historical_ticks (clarity)
-- - Aligned with live_ticks schema (6 columns)
-- - Removed: mid, spread, exchange, event_type, use_case (calculated on-the-fly)
-- - TTL: 10 years (long-term ML training data)
-- - Partitioning: (month, symbol) for efficient queries
-- - Engine: MergeTree (simple, efficient for bulk inserts)
-- ============================================================================
