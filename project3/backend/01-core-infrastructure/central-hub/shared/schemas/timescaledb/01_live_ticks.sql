-- ============================================================================
-- TimescaleDB Schema: live_ticks (Real-time Tick Data)
-- ============================================================================
-- Purpose: Store raw bid/ask ticks from live market data (Polygon WebSocket)
-- Retention: 90 days (automatic compression after 7 days)
-- Storage: Hypertable with automatic partitioning by time
-- ============================================================================

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS public.live_ticks CASCADE;

-- Create live_ticks table (6-column lean schema)
CREATE TABLE IF NOT EXISTS public.live_ticks (
    -- Timestamp (hypertable partition key)
    time TIMESTAMPTZ NOT NULL,

    -- Symbol (trading pair)
    symbol TEXT NOT NULL,

    -- Price data (5 decimal places for forex precision)
    bid NUMERIC(18,5) NOT NULL,
    ask NUMERIC(18,5) NOT NULL,

    -- Original timestamp from data source (milliseconds since epoch)
    timestamp_ms BIGINT NOT NULL,

    -- Ingestion metadata
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Hypertable Configuration
-- ============================================================================

-- Convert to hypertable (1-day chunks for optimal performance)
SELECT create_hypertable(
    'live_ticks',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Primary index: symbol + time (for efficient range queries)
CREATE INDEX IF NOT EXISTS idx_live_ticks_symbol_time
ON public.live_ticks (symbol, time DESC);

-- Secondary index: time only (for global time-based queries)
CREATE INDEX IF NOT EXISTS idx_live_ticks_time
ON public.live_ticks (time DESC);

-- Unique index for deduplication (prevent duplicate ticks)
CREATE UNIQUE INDEX IF NOT EXISTS idx_live_ticks_unique
ON public.live_ticks (symbol, time, timestamp_ms);

-- ============================================================================
-- Compression Policy (Compress data older than 7 days)
-- ============================================================================

ALTER TABLE public.live_ticks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('live_ticks', INTERVAL '7 days', if_not_exists => TRUE);

-- ============================================================================
-- Retention Policy (Drop data older than 90 days)
-- ============================================================================

SELECT add_retention_policy('live_ticks', INTERVAL '90 days', if_not_exists => TRUE);

-- ============================================================================
-- Statistics & Optimization
-- ============================================================================

-- Enable parallel query execution
ALTER TABLE public.live_ticks SET (parallel_workers = 4);

-- Update table statistics
ANALYZE public.live_ticks;

-- ============================================================================
-- Continuous Aggregates (Pre-computed Views)
-- ============================================================================

-- 1-minute OHLC aggregate (for fast queries)
CREATE MATERIALIZED VIEW IF NOT EXISTS live_ticks_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    first(bid, time) AS open_bid,
    max(bid) AS high_bid,
    min(bid) AS low_bid,
    last(bid, time) AS close_bid,
    first(ask, time) AS open_ask,
    max(ask) AS high_ask,
    min(ask) AS low_ask,
    last(ask, time) AS close_ask,
    COUNT(*) AS tick_count,
    AVG((bid + ask) / 2) AS avg_mid,
    AVG(ask - bid) AS avg_spread,
    MAX(ask - bid) AS max_spread,
    MIN(ask - bid) AS min_spread
FROM public.live_ticks
GROUP BY bucket, symbol;

-- Refresh policy: update every 1 minute
SELECT add_continuous_aggregate_policy('live_ticks_1m',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to calculate mid price on-the-fly
CREATE OR REPLACE FUNCTION get_mid_price(bid NUMERIC, ask NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    RETURN (bid + ask) / 2;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate spread on-the-fly
CREATE OR REPLACE FUNCTION get_spread(bid NUMERIC, ask NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    RETURN ask - bid;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Grants (Security)
-- ============================================================================

-- Grant read/write to application user
GRANT SELECT, INSERT ON public.live_ticks TO suho_admin;
GRANT SELECT ON live_ticks_1m TO suho_admin;

-- ============================================================================
-- Schema Documentation
-- ============================================================================

COMMENT ON TABLE public.live_ticks IS 'Live tick data from Polygon WebSocket (90-day retention, 7-day compression)';
COMMENT ON COLUMN public.live_ticks.time IS 'Timestamp of tick (partition key)';
COMMENT ON COLUMN public.live_ticks.symbol IS 'Trading pair (e.g., EURUSD, XAUUSD)';
COMMENT ON COLUMN public.live_ticks.bid IS 'Bid price (5 decimal precision)';
COMMENT ON COLUMN public.live_ticks.ask IS 'Ask price (5 decimal precision)';
COMMENT ON COLUMN public.live_ticks.timestamp_ms IS 'Original millisecond timestamp from data source';
COMMENT ON COLUMN public.live_ticks.ingested_at IS 'Ingestion timestamp (for debugging)';

-- ============================================================================
-- Migration Notes
-- ============================================================================
-- v1.8.0 (2025-10-18):
-- - Renamed from market_ticks to live_ticks
-- - Reduced from 14 columns to 6 columns (57% storage reduction)
-- - Removed: tick_id, tenant_id, mid, spread, exchange, source, event_type, use_case
-- - Mid and spread now calculated on-the-fly using helper functions
-- - Added continuous aggregate for 1-minute OHLC with spread metrics
-- ============================================================================
