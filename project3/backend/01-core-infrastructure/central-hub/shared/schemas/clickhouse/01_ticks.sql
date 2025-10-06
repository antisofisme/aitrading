-- =======================================================================
-- CLICKHOUSE TICKS SCHEMA (Analytics Backup)
-- =======================================================================
-- Purpose: Real-time forex quote storage for analytics
-- Source: Polygon Live Collector (WebSocket)
-- Data Flow: Live Collector → NATS/Kafka → Data Bridge → ClickHouse
-- Retention: 90 days (TTL)
-- Version: 1.0.0
-- Last Updated: 2025-10-06
-- =======================================================================

CREATE DATABASE IF NOT EXISTS suho_analytics;

USE suho_analytics;

-- =======================================================================
-- TABLE: ticks (Real-time Forex Quotes)
-- =======================================================================
-- Stores high-frequency tick data for pattern analysis and backtesting
-- Optimized for analytical queries with columnar storage

CREATE TABLE IF NOT EXISTS ticks (
    -- ===========================================
    -- IDENTIFIERS
    -- ===========================================
    symbol String,                        -- Trading pair: "EUR/USD", "XAU/USD"
    timestamp DateTime64(3, 'UTC'),       -- Quote timestamp (millisecond precision)
    timestamp_ms UInt64,                  -- Unix milliseconds (for compatibility)

    -- ===========================================
    -- PRICE DATA
    -- ===========================================
    bid Decimal(18, 5),                   -- Bid price (5 decimal places for forex)
    ask Decimal(18, 5),                   -- Ask price
    mid Decimal(18, 5),                   -- Mid price = (bid + ask) / 2
    spread Decimal(10, 5),                -- Spread in pips (ask - bid) * 10000

    -- ===========================================
    -- SOURCE & METADATA
    -- ===========================================
    exchange UInt16,                      -- Exchange ID from Polygon
    source String,                        -- Data source: "polygon_websocket"
    event_type String,                    -- Event type: "quote"

    -- Optional: For confirmation pairs
    use_case String DEFAULT '',           -- "confirmation", "trading", "analysis"

    -- ===========================================
    -- SYSTEM METADATA
    -- ===========================================
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)  -- Ingestion timestamp
)
ENGINE = MergeTree()
PARTITION BY (symbol, toYYYYMM(timestamp))   -- Partition by symbol and month
ORDER BY (symbol, timestamp)                  -- Sort by symbol, then timestamp
TTL toDateTime(timestamp) + INTERVAL 90 DAY   -- Auto-delete after 90 days
SETTINGS index_granularity = 8192;

-- =======================================================================
-- INDEXES FOR FAST QUERIES
-- =======================================================================

-- Index for symbol filtering
CREATE INDEX IF NOT EXISTS idx_ticks_symbol
ON ticks (symbol) TYPE set(0);

-- Index for source filtering
CREATE INDEX IF NOT EXISTS idx_ticks_source
ON ticks (source) TYPE set(0);

-- Index for spread analysis (find high spread moments)
CREATE INDEX IF NOT EXISTS idx_ticks_spread
ON ticks (spread) TYPE minmax;

-- =======================================================================
-- MATERIALIZED VIEWS - AGGREGATIONS
-- =======================================================================

-- Latest tick per symbol (for real-time dashboard)
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_ticks
ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY symbol
AS SELECT
    symbol,
    argMax(timestamp, timestamp) as latest_timestamp,
    argMax(bid, timestamp) as latest_bid,
    argMax(ask, timestamp) as latest_ask,
    argMax(mid, timestamp) as latest_mid,
    argMax(spread, timestamp) as latest_spread,
    argMax(exchange, timestamp) as latest_exchange,
    argMax(ingested_at, timestamp) as ingested_at
FROM ticks
GROUP BY symbol;

-- Spread statistics (for spread analysis)
CREATE MATERIALIZED VIEW IF NOT EXISTS spread_stats_1h
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMMDD(hour)
ORDER BY (symbol, hour)
AS SELECT
    symbol,
    toStartOfHour(timestamp) as hour,
    avgState(spread) as avg_spread,
    minState(spread) as min_spread,
    maxState(spread) as max_spread,
    stddevPopState(spread) as stddev_spread,
    count() as tick_count
FROM ticks
GROUP BY symbol, hour;

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get latest tick for EUR/USD
-- SELECT * FROM latest_ticks WHERE symbol = 'EUR/USD';

-- Get all ticks for EUR/USD in last hour
-- SELECT * FROM ticks
-- WHERE symbol = 'EUR/USD'
--   AND timestamp >= now() - INTERVAL 1 HOUR
-- ORDER BY timestamp DESC;

-- Analyze spread distribution
-- SELECT
--     symbol,
--     round(spread, 1) as spread_bucket,
--     count() as tick_count
-- FROM ticks
-- WHERE timestamp >= now() - INTERVAL 1 DAY
-- GROUP BY symbol, spread_bucket
-- ORDER BY symbol, spread_bucket;

-- Get average spread per hour
-- SELECT
--     symbol,
--     hour,
--     avgMerge(avg_spread) as avg_spread,
--     minMerge(min_spread) as min_spread,
--     maxMerge(max_spread) as max_spread,
--     sum(tick_count) as total_ticks
-- FROM spread_stats_1h
-- WHERE hour >= now() - INTERVAL 7 DAY
-- GROUP BY symbol, hour
-- ORDER BY symbol, hour;

-- =======================================================================
-- NOTES
-- =======================================================================
-- 1. TTL: Data auto-deleted after 90 days to save storage
-- 2. Partitioning: By symbol and month for efficient queries
-- 3. Decimal precision: 5 decimal places for forex (0.00001 = 1 pip for JPY pairs)
-- 4. Spread calculation: (ask - bid) * 10000 for standard forex pairs
-- 5. Columnar storage: Optimized for analytical queries
-- 6. Index granularity: 8192 rows per granule (ClickHouse default)
-- 7. Materialized views: Pre-aggregated for fast dashboard queries
-- =======================================================================
