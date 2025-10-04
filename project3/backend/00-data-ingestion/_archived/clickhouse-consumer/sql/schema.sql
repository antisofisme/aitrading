-- =======================================================================
-- CLICKHOUSE SCHEMA - FOREX TRADING DATA
-- =======================================================================
-- Polygon.io data ingestion: Ticks, Aggregates, Confirmation pairs
-- Optimized for time-series analytics and backtesting

-- =======================================================================
-- DATABASE SETUP
-- =======================================================================
CREATE DATABASE IF NOT EXISTS forex_data;

USE forex_data;

-- =======================================================================
-- TABLE 1: TICK DATA (Quote/Bid-Ask)
-- =======================================================================
-- Real-time tick data from Polygon.io WebSocket (CA stream)
-- Source: polygon-live-collector (quotes)

CREATE TABLE IF NOT EXISTS ticks (
    -- Primary Fields
    symbol String,                    -- "EUR/USD", "XAU/USD"
    timestamp DateTime64(3, 'UTC'),   -- Millisecond precision
    timestamp_ms UInt64,              -- Unix timestamp in milliseconds

    -- Price Data
    bid Decimal(18, 5),               -- Bid price
    ask Decimal(18, 5),               -- Ask price
    mid Decimal(18, 5),               -- Mid price (calculated)
    spread Decimal(10, 5),            -- Spread in pips

    -- Metadata
    exchange UInt16,                  -- Exchange ID from Polygon
    source String,                    -- "polygon_websocket", "polygon_rest"
    event_type String,                -- "quote", "confirmation"
    use_case String DEFAULT '',       -- For confirmation pairs

    -- Ingestion Metadata
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)  -- When inserted to ClickHouse
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)  -- Monthly partitions
ORDER BY (symbol, timestamp)
TTL toDateTime(timestamp) + INTERVAL 90 DAY   -- Keep 90 days (convert DateTime64 to DateTime)
SETTINGS index_granularity = 8192;

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_ticks_symbol ON ticks (symbol) TYPE set(0);
CREATE INDEX IF NOT EXISTS idx_ticks_source ON ticks (source) TYPE set(0);
CREATE INDEX IF NOT EXISTS idx_ticks_event_type ON ticks (event_type) TYPE set(0);

-- =======================================================================
-- TABLE 2: AGGREGATE DATA (OHLCV Bars)
-- =======================================================================
-- OHLCV bars with tick volume (like MT5)
-- Source: polygon-live-collector (aggregates - CAS stream)

CREATE TABLE IF NOT EXISTS aggregates (
    -- Primary Fields
    symbol String,                    -- "EUR/USD", "XAU/USD"
    timeframe String,                 -- "1s", "1m", "5m", "1h", "1d"
    timestamp DateTime64(3, 'UTC'),   -- Bar start time
    timestamp_ms UInt64,              -- Unix timestamp in milliseconds

    -- OHLCV Data
    open Decimal(18, 5),              -- Open price
    high Decimal(18, 5),              -- High price
    low Decimal(18, 5),               -- Low price
    close Decimal(18, 5),             -- Close price
    volume UInt64,                    -- Tick volume (like MT5!)

    -- Additional Metrics
    vwap Decimal(18, 5) DEFAULT 0,   -- Volume Weighted Average Price
    range_pips Decimal(10, 5),        -- High-Low range in pips

    -- Time Range
    start_time DateTime64(3, 'UTC'),  -- Bar start
    end_time DateTime64(3, 'UTC'),    -- Bar end

    -- Metadata
    source String,                    -- "polygon_aggregate"
    event_type String DEFAULT 'ohlcv', -- "ohlcv"

    -- Ingestion Metadata
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY (symbol, toYYYYMM(timestamp))  -- Partition by symbol and month
ORDER BY (symbol, timeframe, timestamp)
TTL toDateTime(timestamp) + INTERVAL 365 DAY   -- Keep 1 year (convert DateTime64 to DateTime)
SETTINGS index_granularity = 8192;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agg_symbol ON aggregates (symbol) TYPE set(0);
CREATE INDEX IF NOT EXISTS idx_agg_timeframe ON aggregates (timeframe) TYPE set(0);

-- =======================================================================
-- TABLE 3: DEDUPLICATION TRACKING
-- =======================================================================
-- Track processed message IDs for NATS+Kafka complementary pattern
-- Prevents duplicate processing when receiving from both sources

CREATE TABLE IF NOT EXISTS message_dedup (
    message_id String,                -- Composite: "symbol:timestamp_ms:source"
    source String,                    -- "nats" or "kafka"
    data_type String,                 -- "tick" or "aggregate"
    processed_at DateTime64(3, 'UTC') DEFAULT now64(3),

    -- For memory efficiency: expire after 1 hour (older messages won't be duplicated)
    INDEX idx_message_id message_id TYPE bloom_filter(0.01) GRANULARITY 1
)
ENGINE = MergeTree()
ORDER BY (message_id, processed_at)
TTL toDateTime(processed_at) + INTERVAL 1 HOUR  -- Only need to track recent messages
SETTINGS index_granularity = 8192;

-- =======================================================================
-- MATERIALIZED VIEWS - PRE-AGGREGATED DATA
-- =======================================================================

-- 1-minute candles from 1-second aggregates (if needed)
CREATE MATERIALIZED VIEW IF NOT EXISTS aggregates_1m
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(minute_start)
ORDER BY (symbol, minute_start)
AS SELECT
    symbol,
    '1m' as timeframe,
    toStartOfMinute(timestamp) as minute_start,
    argMinState(open, timestamp) as open_state,
    maxState(high) as high_state,
    minState(low) as low_state,
    argMaxState(close, timestamp) as close_state,
    sumState(volume) as volume_state
FROM aggregates
WHERE timeframe = '1s'
GROUP BY symbol, minute_start;

-- Latest tick per symbol (for real-time display)
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_ticks
ENGINE = ReplacingMergeTree()
ORDER BY symbol
AS SELECT
    symbol,
    argMax(timestamp, timestamp) as latest_timestamp,
    argMax(bid, timestamp) as latest_bid,
    argMax(ask, timestamp) as latest_ask,
    argMax(mid, timestamp) as latest_mid,
    argMax(spread, timestamp) as latest_spread,
    argMax(source, timestamp) as latest_source
FROM ticks
GROUP BY symbol;

-- =======================================================================
-- SAMPLE QUERIES (for reference)
-- =======================================================================

-- Get latest tick for each pair
-- SELECT * FROM latest_ticks ORDER BY symbol;

-- Get 1-hour candles for EUR/USD
-- SELECT * FROM aggregates
-- WHERE symbol = 'EUR/USD' AND timeframe = '1h'
-- ORDER BY timestamp DESC LIMIT 100;

-- Calculate average spread per hour
-- SELECT
--     symbol,
--     toStartOfHour(timestamp) as hour,
--     avg(spread) as avg_spread,
--     count() as tick_count
-- FROM ticks
-- WHERE timestamp >= now() - INTERVAL 1 DAY
-- GROUP BY symbol, hour
-- ORDER BY symbol, hour DESC;

-- Get volume profile
-- SELECT
--     symbol,
--     toStartOfHour(timestamp) as hour,
--     sum(volume) as total_volume,
--     avg(close) as avg_price
-- FROM aggregates
-- WHERE timeframe = '1s' AND timestamp >= now() - INTERVAL 1 DAY
-- GROUP BY symbol, hour
-- ORDER BY symbol, hour DESC;

-- =======================================================================
-- NOTES
-- =======================================================================

-- Performance Optimization:
-- 1. Partitioning by month keeps query scans small
-- 2. ORDER BY (symbol, timestamp) enables efficient range queries
-- 3. TTL automatically drops old data to save storage
-- 4. Materialized views pre-compute common aggregations

-- Data Retention:
-- - Ticks: 90 days (detailed data for recent analysis)
-- - Aggregates: 365 days (for backtesting)
-- - Dedup: 1 hour (only need recent for duplicate detection)

-- Complementary Pattern:
-- - Consumer subscribes to BOTH NATS and Kafka
-- - Deduplication prevents processing same message twice
-- - Kafka fills gaps when NATS fails (zero data loss)

-- Scaling:
-- - ClickHouse handles billions of rows easily
-- - Can shard by symbol if needed (future optimization)
-- - Materialized views keep aggregates fast

-- =======================================================================
