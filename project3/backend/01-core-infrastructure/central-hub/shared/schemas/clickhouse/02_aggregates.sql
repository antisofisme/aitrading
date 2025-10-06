-- =======================================================================
-- CLICKHOUSE AGGREGATES SCHEMA (Historical OHLCV)
-- =======================================================================
-- Purpose: Historical OHLCV bars for backtesting and ML training
-- Source: Polygon Historical Downloader (REST API)
-- Data Flow: Historical Downloader → NATS/Kafka → ClickHouse Writer → ClickHouse
-- Retention: 10 years (for long-term backtesting)
-- Tenant: 'system' (application-level, shared across all user tenants)
-- Timeframes: M5, M15, M30, H1, H4, D1, W1 (7 timeframes for ML multi-timeframe analysis)
-- Version: 2.0.0
-- Last Updated: 2025-10-06
-- =======================================================================

CREATE DATABASE IF NOT EXISTS suho_analytics;

USE suho_analytics;

-- =======================================================================
-- TABLE: aggregates (Historical OHLCV Bars)
-- =======================================================================
-- Stores historical candlestick data for backtesting and ML training
-- Optimized for analytical queries with columnar storage

CREATE TABLE IF NOT EXISTS aggregates (
    -- ===========================================
    -- IDENTIFIERS
    -- ===========================================
    symbol String,                        -- Trading pair: "EUR/USD", "XAU/USD"
    timeframe String,                     -- Timeframe: "1m", "5m", "15m", "1h", "4h", "1d"
    timestamp DateTime64(3, 'UTC'),       -- Bar start time
    timestamp_ms UInt64,                  -- Unix milliseconds

    -- ===========================================
    -- OHLCV DATA
    -- ===========================================
    open Decimal(18, 5),                  -- Open price
    high Decimal(18, 5),                  -- High price
    low Decimal(18, 5),                   -- Low price
    close Decimal(18, 5),                 -- Close price
    volume UInt64,                        -- Tick volume (number of ticks)

    -- ===========================================
    -- ADDITIONAL METRICS
    -- ===========================================
    vwap Decimal(18, 5) DEFAULT 0,        -- Volume-weighted average price
    range_pips Decimal(10, 5),            -- High - low in pips
    body_pips Decimal(10, 5),             -- |close - open| in pips

    -- ===========================================
    -- TIME FIELDS
    -- ===========================================
    start_time DateTime64(3, 'UTC'),      -- Bar start time
    end_time DateTime64(3, 'UTC'),        -- Bar end time

    -- ===========================================
    -- SOURCE & METADATA
    -- ===========================================
    source String,                        -- "polygon_historical", "polygon_aggregate"
    event_type String DEFAULT 'ohlcv',    -- "ohlcv"

    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY (symbol, toYYYYMM(timestamp))  -- Partition by symbol and month
ORDER BY (symbol, timeframe, timestamp)     -- Sort for efficient queries
TTL toDateTime(timestamp) + INTERVAL 3650 DAY  -- 10 years retention
SETTINGS index_granularity = 8192;

-- =======================================================================
-- INDEXES FOR FAST QUERIES
-- =======================================================================

-- Symbol index
CREATE INDEX IF NOT EXISTS idx_aggregates_symbol
ON aggregates (symbol) TYPE set(0);

-- Timeframe index
CREATE INDEX IF NOT EXISTS idx_aggregates_timeframe
ON aggregates (timeframe) TYPE set(0);

-- Source index
CREATE INDEX IF NOT EXISTS idx_aggregates_source
ON aggregates (source) TYPE set(0);

-- Volume index (for volume analysis)
CREATE INDEX IF NOT EXISTS idx_aggregates_volume
ON aggregates (volume) TYPE minmax;

-- Range index (for volatility analysis)
CREATE INDEX IF NOT EXISTS idx_aggregates_range
ON aggregates (range_pips) TYPE minmax;

-- =======================================================================
-- MATERIALIZED VIEWS - PRE-AGGREGATIONS
-- =======================================================================

-- Daily statistics per symbol
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_stats
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (symbol, day)
AS SELECT
    symbol,
    timeframe,
    toDate(timestamp) as day,

    -- Price stats
    minState(low) as daily_low,
    maxState(high) as daily_high,
    avgState(close) as avg_close,
    stddevPopState(close) as stddev_close,

    -- Volume stats
    sumState(volume) as total_volume,
    avgState(volume) as avg_volume,

    -- Range stats
    avgState(range_pips) as avg_range_pips,
    maxState(range_pips) as max_range_pips,

    count() as bar_count
FROM aggregates
GROUP BY symbol, timeframe, day;

-- Monthly statistics for long-term analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_stats
ENGINE = AggregatingMergeTree()
PARTITION BY toYear(month)
ORDER BY (symbol, month)
AS SELECT
    symbol,
    timeframe,
    toStartOfMonth(timestamp) as month,

    -- OHLC for month
    minState(low) as monthly_low,
    maxState(high) as monthly_high,
    argMinState(open, timestamp) as monthly_open,
    argMaxState(close, timestamp) as monthly_close,

    -- Volume
    sumState(volume) as total_volume,

    -- Volatility
    stddevPopState(close) as price_volatility,

    count() as bar_count
FROM aggregates
GROUP BY symbol, timeframe, month;

-- =======================================================================
-- FUNCTIONS FOR TECHNICAL ANALYSIS
-- =======================================================================

-- Calculate Simple Moving Average
-- Usage: SELECT symbol, timestamp, sma(close, 20) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
--        FROM aggregates WHERE symbol = 'EUR/USD' AND timeframe = '1h';

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get last 100 bars for EUR/USD 1-hour
-- SELECT * FROM aggregates
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1h'
-- ORDER BY timestamp DESC
-- LIMIT 100;

-- Get historical data for backtesting (last 2 years)
-- SELECT
--     symbol,
--     timeframe,
--     timestamp,
--     open,
--     high,
--     low,
--     close,
--     volume
-- FROM aggregates
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1h'
--   AND timestamp >= now() - INTERVAL 730 DAY
-- ORDER BY timestamp;

-- Calculate daily returns
-- SELECT
--     symbol,
--     toDate(timestamp) as date,
--     argMin(open, timestamp) as day_open,
--     argMax(close, timestamp) as day_close,
--     round((argMax(close, timestamp) - argMin(open, timestamp)) / argMin(open, timestamp) * 100, 4) as daily_return_pct
-- FROM aggregates
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1h'
--   AND timestamp >= now() - INTERVAL 30 DAY
-- GROUP BY symbol, date
-- ORDER BY date DESC;

-- Volatility analysis (ATR-like calculation)
-- SELECT
--     symbol,
--     timeframe,
--     toDate(timestamp) as date,
--     round(avg(range_pips), 2) as avg_range,
--     round(max(range_pips), 2) as max_range,
--     round(stddevPop(range_pips), 2) as range_volatility,
--     count() as bar_count
-- FROM aggregates
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1h'
--   AND timestamp >= now() - INTERVAL 30 DAY
-- GROUP BY symbol, timeframe, date
-- ORDER BY date DESC;

-- Volume profile (volume distribution by price level)
-- SELECT
--     symbol,
--     round(close, 4) as price_level,
--     sum(volume) as total_volume,
--     count() as bar_count
-- FROM aggregates
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1h'
--   AND timestamp >= now() - INTERVAL 7 DAY
-- GROUP BY symbol, price_level
-- ORDER BY total_volume DESC
-- LIMIT 20;

-- Get daily statistics
-- SELECT
--     symbol,
--     timeframe,
--     day,
--     minMerge(daily_low) as low,
--     maxMerge(daily_high) as high,
--     avgMerge(avg_close) as avg_price,
--     stddevPopMerge(stddev_close) as volatility,
--     sumMerge(total_volume) as volume
-- FROM daily_stats
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1h'
--   AND day >= today() - INTERVAL 30 DAY
-- ORDER BY day DESC;

-- Get monthly performance
-- SELECT
--     symbol,
--     timeframe,
--     month,
--     minMerge(monthly_low) as low,
--     maxMerge(monthly_high) as high,
--     argMinMerge(monthly_open) as open,
--     argMaxMerge(monthly_close) as close,
--     round((argMaxMerge(monthly_close) - argMinMerge(monthly_open)) / argMinMerge(monthly_open) * 100, 2) as monthly_return_pct,
--     sumMerge(total_volume) as total_volume
-- FROM monthly_stats
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1d'
-- ORDER BY month DESC;

-- Candlestick pattern detection (simple doji detection)
-- SELECT
--     symbol,
--     timestamp,
--     open,
--     close,
--     high,
--     low,
--     body_pips,
--     range_pips,
--     CASE
--         WHEN body_pips < (range_pips * 0.1) THEN 'doji'
--         WHEN body_pips < (range_pips * 0.3) AND close > open THEN 'spinning_top_bullish'
--         WHEN body_pips < (range_pips * 0.3) AND close < open THEN 'spinning_top_bearish'
--         WHEN close > open THEN 'bullish'
--         WHEN close < open THEN 'bearish'
--         ELSE 'neutral'
--     END as pattern
-- FROM aggregates
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1h'
--   AND timestamp >= now() - INTERVAL 7 DAY
-- ORDER BY timestamp DESC;

-- =======================================================================
-- PERFORMANCE OPTIMIZATION TIPS
-- =======================================================================

-- 1. Use PREWHERE for filtering large datasets:
-- SELECT * FROM aggregates
-- PREWHERE symbol = 'EUR/USD' AND timeframe = '1h'
-- WHERE timestamp >= now() - INTERVAL 30 DAY;

-- 2. Leverage materialized views for frequent queries:
-- Instead of: SELECT avg(close) FROM aggregates WHERE ...
-- Use: SELECT avgMerge(avg_close) FROM daily_stats WHERE ...

-- 3. Use sampling for exploration:
-- SELECT * FROM aggregates SAMPLE 0.1  -- 10% sample
-- WHERE symbol = 'EUR/USD';

-- 4. Optimize queries with LIMIT:
-- Always use LIMIT when exploring data

-- 5. Monitor query performance:
-- SELECT query, elapsed, rows_read, memory_usage
-- FROM system.query_log
-- WHERE type = 'QueryFinish'
-- ORDER BY event_time DESC
-- LIMIT 10;

-- =======================================================================
-- NOTES
-- =======================================================================
-- 1. TTL: Data retained for 10 years (3650 days)
-- 2. Partitioning: By symbol and month for efficient pruning
-- 3. Sorting: By symbol, timeframe, timestamp for fast lookups
-- 4. Compression: ClickHouse automatically compresses (10-100x)
-- 5. Decimal precision: 5 decimal places for forex pairs
-- 6. Range/Body in pips: Pre-calculated for technical analysis
-- 7. VWAP: Volume-weighted average price (default 0 if not available)
-- 8. Materialized views: Pre-aggregated daily/monthly stats
-- 9. Timeframes: 7 timeframes for ML - "5m", "15m", "30m", "1h", "4h", "1d", "1w"
-- 10. ML Training: Optimized schema for multi-timeframe feature engineering
-- 11. Writer Service: ClickHouse Writer subscribes from NATS/Kafka (filters source='historical')
-- =======================================================================
