-- =======================================================================
-- TIMESCALEDB MARKET CANDLES SCHEMA (OHLCV Bars)
-- =======================================================================
-- Purpose: Store aggregated OHLCV candles from Live Polygon aggregates
-- Source: Polygon Live Collector (Aggregate WebSocket CAS stream)
-- Data Flow: Live Collector → NATS/Kafka → TimescaleDB Writer → TimescaleDB
-- Retention: 90 days (compression + retention policy)
-- Tenant: 'system' (application-level, shared across all user tenants)
-- Timeframe: 1s (1-second bars from live stream)
-- Version: 2.0.0
-- Last Updated: 2025-10-06
-- =======================================================================

-- Connect to database
\c suho_trading;

-- Set search path
SET search_path TO public;

-- =======================================================================
-- TABLE: market_candles (OHLCV Bars)
-- =======================================================================
-- Stores OHLCV candles from Polygon aggregate stream (CAS)
-- Similar to MT5 bars with tick volume

CREATE TABLE IF NOT EXISTS market_candles (
    -- ===========================================
    -- TIME DIMENSION (Required for TimescaleDB)
    -- ===========================================
    time TIMESTAMPTZ NOT NULL,            -- Candle start time

    -- ===========================================
    -- IDENTIFIERS
    -- ===========================================
    candle_id UUID DEFAULT uuid_generate_v4(),  -- Unique candle ID
    tenant_id VARCHAR(50) NOT NULL,       -- Multi-tenant isolation
    symbol VARCHAR(20) NOT NULL,          -- Trading pair: "EUR/USD"
    timeframe VARCHAR(10) NOT NULL,       -- Timeframe: "1s", "1m", "5m", "1h", "1d"

    -- ===========================================
    -- OHLCV DATA
    -- ===========================================
    open DECIMAL(18, 5) NOT NULL,         -- Open price
    high DECIMAL(18, 5) NOT NULL,         -- High price
    low DECIMAL(18, 5) NOT NULL,          -- Low price
    close DECIMAL(18, 5) NOT NULL,        -- Close price
    volume BIGINT NOT NULL DEFAULT 0,     -- Tick volume (number of ticks)

    -- ===========================================
    -- ADDITIONAL METRICS
    -- ===========================================
    vwap DECIMAL(18, 5),                  -- Volume-weighted average price
    range_pips DECIMAL(10, 5),            -- High - low in pips
    body_pips DECIMAL(10, 5),             -- |close - open| in pips

    -- ===========================================
    -- TIME FIELDS
    -- ===========================================
    start_time TIMESTAMPTZ NOT NULL,      -- Bar start time
    end_time TIMESTAMPTZ NOT NULL,        -- Bar end time
    timestamp_ms BIGINT NOT NULL,         -- Unix milliseconds

    -- ===========================================
    -- SOURCE & METADATA
    -- ===========================================
    source VARCHAR(50) NOT NULL,          -- "polygon_aggregate"
    event_type VARCHAR(20) DEFAULT 'ohlcv', -- "ohlcv"

    ingested_at TIMESTAMPTZ DEFAULT NOW(), -- Ingestion timestamp

    -- ===========================================
    -- CONSTRAINTS
    -- ===========================================
    PRIMARY KEY (time, tenant_id, symbol, timeframe, candle_id),
    CHECK (high >= low),
    CHECK (high >= open),
    CHECK (high >= close),
    CHECK (low <= open),
    CHECK (low <= close)
);

-- =======================================================================
-- CONVERT TO HYPERTABLE
-- =======================================================================

SELECT create_hypertable(
    'market_candles',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Add space dimension for tenant partitioning
SELECT add_dimension(
    'market_candles',
    'tenant_id',
    number_partitions => 4,
    if_not_exists => TRUE
);

-- =======================================================================
-- INDEXES
-- =======================================================================

-- Composite index: tenant + symbol + timeframe + time
CREATE INDEX IF NOT EXISTS idx_market_candles_tenant_symbol_tf_time
ON market_candles (tenant_id, symbol, timeframe, time DESC);

-- Symbol + timeframe index (cross-tenant queries)
CREATE INDEX IF NOT EXISTS idx_market_candles_symbol_tf_time
ON market_candles (symbol, timeframe, time DESC);

-- Volume index (for volume analysis)
CREATE INDEX IF NOT EXISTS idx_market_candles_volume
ON market_candles (volume, time DESC)
WHERE volume > 1000;  -- Partial index for high volume candles

-- =======================================================================
-- ROW-LEVEL SECURITY
-- =======================================================================

ALTER TABLE market_candles ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_market_candles ON market_candles
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- COMPRESSION
-- =======================================================================

ALTER TABLE market_candles SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tenant_id, symbol, timeframe',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('market_candles', INTERVAL '7 days');

-- =======================================================================
-- RETENTION POLICY
-- =======================================================================

SELECT add_retention_policy('market_candles', INTERVAL '90 days');

-- =======================================================================
-- CONTINUOUS AGGREGATES
-- =======================================================================

-- 5-minute candles (aggregated from 1-second candles)
CREATE MATERIALIZED VIEW IF NOT EXISTS market_candles_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS bucket,
    tenant_id,
    symbol,
    '5m' AS timeframe,

    -- OHLC
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,

    -- Volume
    SUM(volume) AS volume,

    -- VWAP
    SUM(vwap * volume) / NULLIF(SUM(volume), 0) AS vwap,

    -- Range
    MAX(high) - MIN(low) AS range_pips,
    ABS(LAST(close, time) - FIRST(open, time)) AS body_pips,

    MAX(source) AS source
FROM market_candles
WHERE timeframe = '1s'  -- Aggregate from 1-second candles
GROUP BY bucket, tenant_id, symbol;

SELECT add_continuous_aggregate_policy('market_candles_5m',
    start_offset => INTERVAL '10 minutes',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes'
);

-- Hourly candles
CREATE MATERIALIZED VIEW IF NOT EXISTS market_candles_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    tenant_id,
    symbol,
    '1h' AS timeframe,

    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,

    SUM(volume) AS volume,
    SUM(vwap * volume) / NULLIF(SUM(volume), 0) AS vwap,

    MAX(high) - MIN(low) AS range_pips,
    ABS(LAST(close, time) - FIRST(open, time)) AS body_pips,

    MAX(source) AS source
FROM market_candles
WHERE timeframe IN ('1s', '1m')  -- Can aggregate from seconds or minutes
GROUP BY bucket, tenant_id, symbol;

SELECT add_continuous_aggregate_policy('market_candles_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- =======================================================================
-- TRIGGERS
-- =======================================================================

-- Auto-calculate range_pips and body_pips on insert
CREATE OR REPLACE FUNCTION calculate_candle_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate range in pips
    NEW.range_pips := ROUND((NEW.high - NEW.low) * 10000, 2);

    -- Calculate body size in pips
    NEW.body_pips := ROUND(ABS(NEW.close - NEW.open) * 10000, 2);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_candle_metrics
BEFORE INSERT OR UPDATE ON market_candles
FOR EACH ROW
EXECUTE FUNCTION calculate_candle_metrics();

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get latest 100 candles for EUR/USD 1-minute
-- SET app.current_tenant_id = 'tenant_001';
-- SELECT * FROM market_candles
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1m'
-- ORDER BY time DESC
-- LIMIT 100;

-- Get 5-minute candles for last 24 hours
-- SELECT * FROM market_candles_5m
-- WHERE tenant_id = 'tenant_001'
--   AND symbol = 'EUR/USD'
--   AND bucket >= NOW() - INTERVAL '24 hours'
-- ORDER BY bucket DESC;

-- Analyze candle patterns (doji detection)
-- SELECT
--     time,
--     symbol,
--     open,
--     close,
--     high,
--     low,
--     body_pips,
--     range_pips,
--     CASE
--         WHEN body_pips < (range_pips * 0.1) THEN 'doji'
--         WHEN close > open THEN 'bullish'
--         WHEN close < open THEN 'bearish'
--         ELSE 'neutral'
--     END as candle_type
-- FROM market_candles
-- WHERE symbol = 'EUR/USD'
--   AND timeframe = '1m'
--   AND time >= NOW() - INTERVAL '1 hour'
-- ORDER BY time DESC;

-- Volume analysis
-- SELECT
--     symbol,
--     timeframe,
--     AVG(volume) as avg_volume,
--     MAX(volume) as max_volume,
--     MIN(volume) as min_volume,
--     STDDEV(volume) as stddev_volume
-- FROM market_candles
-- WHERE time >= NOW() - INTERVAL '7 days'
-- GROUP BY symbol, timeframe
-- ORDER BY symbol, timeframe;

-- =======================================================================
-- GRANTS
-- =======================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON market_candles TO suho_service;
GRANT SELECT ON market_candles TO suho_readonly;

GRANT SELECT ON market_candles_5m TO suho_service;
GRANT SELECT ON market_candles_5m TO suho_readonly;
GRANT SELECT ON market_candles_1h TO suho_service;
GRANT SELECT ON market_candles_1h TO suho_readonly;

-- =======================================================================
-- NOTES
-- =======================================================================
-- 1. Timeframes: Primary "1s" (1-second bars from live stream)
-- 2. Tick volume: Number of ticks aggregated (not notional volume)
-- 3. VWAP: Volume-weighted average price for better entry/exit
-- 4. Range: High-low in pips for volatility analysis
-- 5. Compression: Saves 10-20x storage after 7 days
-- 6. Retention: Auto-delete after 90 days
-- 7. Continuous aggregates: Auto-generate 5m and 1h from 1s bars
-- 8. Triggers: Auto-calculate range_pips and body_pips
-- 9. Pattern detection: Use body_pips/range_pips ratio
-- 10. Performance: Indexed for fast time-series queries
-- 11. Writer Service: TimescaleDB Writer subscribes from NATS/Kafka (filters source!='historical')
-- 12. Tenant: 'system' level (application data, not per-user)
-- =======================================================================

COMMIT;
