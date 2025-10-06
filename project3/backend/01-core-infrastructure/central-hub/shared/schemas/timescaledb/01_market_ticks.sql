-- =======================================================================
-- TIMESCALEDB MARKET TICKS SCHEMA (Primary Real-time Storage)
-- =======================================================================
-- Purpose: Primary storage for real-time forex quotes (tick data)
-- Source: Polygon Live Collector (WebSocket tick/quote stream)
-- Data Flow: Live Collector → NATS/Kafka → Data Bridge → TimescaleDB.market_ticks
-- Aggregation: Tick Aggregator queries this table → creates M5-W1 candles
-- Retention: 90 days (compression + retention policy)
-- Tenant: 'system' (application-level, shared across all user tenants)
-- Version: 2.0.0
-- Last Updated: 2025-10-06
-- =======================================================================

-- Connect to database
\c suho_trading;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set search path
SET search_path TO public;

-- =======================================================================
-- TABLE: market_ticks (Real-time Forex Quotes)
-- =======================================================================
-- Stores high-frequency tick data with TimescaleDB optimization
-- Optimized for fast writes and time-series queries

CREATE TABLE IF NOT EXISTS market_ticks (
    -- ===========================================
    -- TIME DIMENSION (Required for TimescaleDB)
    -- ===========================================
    time TIMESTAMPTZ NOT NULL,            -- Primary time column (PostgreSQL timestamp with timezone)

    -- ===========================================
    -- IDENTIFIERS
    -- ===========================================
    tick_id UUID DEFAULT uuid_generate_v4(),  -- Unique tick ID
    tenant_id VARCHAR(50) NOT NULL,       -- Multi-tenant isolation
    symbol VARCHAR(20) NOT NULL,          -- Trading pair: "EUR/USD", "XAU/USD"

    -- ===========================================
    -- PRICE DATA
    -- ===========================================
    bid DECIMAL(18, 5) NOT NULL,          -- Bid price (5 decimal places)
    ask DECIMAL(18, 5) NOT NULL,          -- Ask price
    mid DECIMAL(18, 5) NOT NULL,          -- Mid price = (bid + ask) / 2
    spread DECIMAL(10, 5) NOT NULL,       -- Spread in pips

    -- ===========================================
    -- SOURCE & METADATA
    -- ===========================================
    exchange VARCHAR(50),                 -- Exchange name or ID
    source VARCHAR(50) NOT NULL,          -- Data source: "polygon_websocket"
    event_type VARCHAR(20) NOT NULL,      -- Event type: "quote"

    -- Optional: For confirmation pairs
    use_case VARCHAR(50) DEFAULT '',      -- "confirmation", "trading", "analysis"

    -- ===========================================
    -- TIMESTAMP FIELDS
    -- ===========================================
    timestamp_ms BIGINT NOT NULL,         -- Unix milliseconds (original from Polygon)
    ingested_at TIMESTAMPTZ DEFAULT NOW(), -- Ingestion timestamp

    -- ===========================================
    -- CONSTRAINTS
    -- ===========================================
    PRIMARY KEY (time, tenant_id, symbol, tick_id)
);

-- =======================================================================
-- CONVERT TO HYPERTABLE
-- =======================================================================
-- Convert to TimescaleDB hypertable for time-series optimization
-- Chunk interval: 1 day (optimized for forex data volume)

SELECT create_hypertable(
    'market_ticks',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Add space dimension for multi-tenant partitioning
-- This distributes data across partitions by tenant_id
SELECT add_dimension(
    'market_ticks',
    'tenant_id',
    number_partitions => 4,
    if_not_exists => TRUE
);

-- =======================================================================
-- INDEXES FOR FAST QUERIES
-- =======================================================================

-- Composite index: tenant + symbol + time (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_market_ticks_tenant_symbol_time
ON market_ticks (tenant_id, symbol, time DESC);

-- Symbol index (for cross-tenant queries)
CREATE INDEX IF NOT EXISTS idx_market_ticks_symbol_time
ON market_ticks (symbol, time DESC);

-- Source index (for data quality analysis)
CREATE INDEX IF NOT EXISTS idx_market_ticks_source
ON market_ticks (source, time DESC);

-- Spread index (for spread analysis)
CREATE INDEX IF NOT EXISTS idx_market_ticks_spread
ON market_ticks (spread, time DESC)
WHERE spread > 3.0;  -- Partial index for high spread detection

-- =======================================================================
-- ROW-LEVEL SECURITY (Multi-tenant Isolation)
-- =======================================================================

-- Enable RLS
ALTER TABLE market_ticks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their tenant's data
CREATE POLICY tenant_isolation_market_ticks ON market_ticks
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- COMPRESSION
-- =======================================================================
-- Enable compression for chunks older than 7 days
-- This reduces storage by 10-20x for time-series data

ALTER TABLE market_ticks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tenant_id, symbol',
    timescaledb.compress_orderby = 'time DESC'
);

-- Add compression policy: compress chunks older than 7 days
SELECT add_compression_policy('market_ticks', INTERVAL '7 days');

-- =======================================================================
-- RETENTION POLICY
-- =======================================================================
-- Auto-delete data older than 90 days to save storage

SELECT add_retention_policy('market_ticks', INTERVAL '90 days');

-- =======================================================================
-- CONTINUOUS AGGREGATES
-- =======================================================================

-- 1-minute OHLCV aggregation (for candlestick charts)
CREATE MATERIALIZED VIEW IF NOT EXISTS market_ticks_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    tenant_id,
    symbol,

    -- OHLC from mid price
    FIRST(mid, time) AS open,
    MAX(mid) AS high,
    MIN(mid) AS low,
    LAST(mid, time) AS close,

    -- Bid/Ask extremes
    FIRST(bid, time) AS open_bid,
    LAST(bid, time) AS close_bid,
    FIRST(ask, time) AS open_ask,
    LAST(ask, time) AS close_ask,

    -- Spread statistics
    AVG(spread) AS avg_spread,
    MIN(spread) AS min_spread,
    MAX(spread) AS max_spread,

    -- Volume proxy (tick count)
    COUNT(*) AS tick_count,

    -- Source tracking
    MAX(source) AS source
FROM market_ticks
GROUP BY bucket, tenant_id, symbol;

-- Add refresh policy: update every 1 minute
SELECT add_continuous_aggregate_policy('market_ticks_1m',
    start_offset => INTERVAL '3 minutes',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

-- Latest tick per symbol (for real-time dashboard)
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_market_ticks
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    tenant_id,
    symbol,
    LAST(bid, time) AS latest_bid,
    LAST(ask, time) AS latest_ask,
    LAST(mid, time) AS latest_mid,
    LAST(spread, time) AS latest_spread,
    LAST(time, time) AS latest_time,
    COUNT(*) AS tick_count_last_minute
FROM market_ticks
GROUP BY bucket, tenant_id, symbol;

SELECT add_continuous_aggregate_policy('latest_market_ticks',
    start_offset => INTERVAL '3 minutes',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

-- =======================================================================
-- FUNCTIONS & TRIGGERS
-- =======================================================================

-- Function: Calculate spread in pips
CREATE OR REPLACE FUNCTION calculate_spread(ask DECIMAL, bid DECIMAL)
RETURNS DECIMAL AS $$
BEGIN
    RETURN ROUND((ask - bid) * 10000, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function: Calculate mid price
CREATE OR REPLACE FUNCTION calculate_mid(ask DECIMAL, bid DECIMAL)
RETURNS DECIMAL AS $$
BEGIN
    RETURN ROUND((ask + bid) / 2, 5);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get latest tick for EUR/USD (tenant: tenant_001)
-- SET app.current_tenant_id = 'tenant_001';
-- SELECT * FROM market_ticks
-- WHERE symbol = 'EUR/USD'
-- ORDER BY time DESC
-- LIMIT 1;

-- Get 1-minute candles for last hour
-- SELECT * FROM market_ticks_1m
-- WHERE tenant_id = 'tenant_001'
--   AND symbol = 'EUR/USD'
--   AND bucket >= NOW() - INTERVAL '1 hour'
-- ORDER BY bucket DESC;

-- Analyze spread distribution
-- SELECT
--     symbol,
--     ROUND(spread, 1) as spread_bucket,
--     COUNT(*) as tick_count
-- FROM market_ticks
-- WHERE time >= NOW() - INTERVAL '1 day'
-- GROUP BY symbol, spread_bucket
-- ORDER BY symbol, spread_bucket;

-- Get latest prices (from materialized view)
-- SELECT
--     symbol,
--     latest_bid,
--     latest_ask,
--     latest_spread,
--     latest_time,
--     tick_count_last_minute
-- FROM latest_market_ticks
-- WHERE tenant_id = 'tenant_001'
-- ORDER BY bucket DESC
-- LIMIT 10;

-- =======================================================================
-- GRANTS
-- =======================================================================

-- Grant permissions to service role
GRANT SELECT, INSERT, UPDATE, DELETE ON market_ticks TO suho_service;
GRANT SELECT ON market_ticks TO suho_readonly;

-- Grant access to continuous aggregates
GRANT SELECT ON market_ticks_1m TO suho_service;
GRANT SELECT ON market_ticks_1m TO suho_readonly;
GRANT SELECT ON latest_market_ticks TO suho_service;
GRANT SELECT ON latest_market_ticks TO suho_readonly;

-- =======================================================================
-- NOTES
-- =======================================================================
-- 1. Retention: Data auto-deleted after 90 days via retention policy
-- 2. Compression: Chunks older than 7 days compressed (10-20x size reduction)
-- 3. Partitioning: By time (1 day chunks) and tenant_id (4 partitions)
-- 4. RLS: Row-level security ensures tenant isolation
-- 5. Continuous aggregates: 1-minute candles updated every minute
-- 6. Indexes: Optimized for tenant+symbol+time queries
-- 7. Decimal precision: 5 decimal places for forex (0.00001 = 1 pip)
-- 8. Performance: Can handle 100K+ ticks/second with proper hardware
-- 9. Monitoring: Use pg_stat_statements for query performance
-- 10. Backup: Use pg_dump with --format=custom for efficient backups
-- =======================================================================

COMMIT;
