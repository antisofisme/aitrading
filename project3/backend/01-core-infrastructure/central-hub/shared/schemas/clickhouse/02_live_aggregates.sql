-- ============================================================================
-- ClickHouse Schema: live_aggregates (Real-time OHLCV Candles)
-- ============================================================================
-- Purpose: Store live aggregated candles with ML features (multiple timeframes)
-- Retention: 7 days (automatic TTL cleanup)
-- Engine: MergeTree with partitioning by month + symbol
-- ============================================================================

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS suho_analytics.live_aggregates;

-- Create live_aggregates table (15 columns with ML features)
CREATE TABLE IF NOT EXISTS suho_analytics.live_aggregates (
    -- Timestamp (primary ordering key)
    time DateTime64(3, 'UTC') NOT NULL,

    -- Symbol (trading pair)
    symbol String NOT NULL,

    -- Timeframe (Enum8 for efficient storage)
    timeframe Enum8(
        '5m' = 1,
        '15m' = 2,
        '30m' = 3,
        '1h' = 4,
        '4h' = 5,
        '1d' = 6,
        '1w' = 7
    ) NOT NULL,

    -- OHLC data (5 decimal places for forex precision)
    open Decimal(18,5) NOT NULL,
    high Decimal(18,5) NOT NULL,
    low Decimal(18,5) NOT NULL,
    close Decimal(18,5) NOT NULL,

    -- Tick count (number of ticks in candle)
    tick_count UInt32 NOT NULL,

    -- Spread metrics (ML features for volatility estimation)
    avg_spread Decimal(18,5) NOT NULL DEFAULT 0,
    max_spread Decimal(18,5) NOT NULL DEFAULT 0,
    min_spread Decimal(18,5) NOT NULL DEFAULT 0,

    -- Price metrics (ML features)
    price_range Decimal(18,5) NOT NULL DEFAULT 0,  -- high - low in pips
    pct_change Float64 NOT NULL DEFAULT 0,         -- (close - open) / open * 100

    -- Quality flag (1 = complete candle with sufficient ticks)
    is_complete UInt8 NOT NULL DEFAULT 1,

    -- Metadata
    created_at DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), symbol)
ORDER BY (symbol, timeframe, time)
TTL toDateTime(time) + INTERVAL 7 DAY
SETTINGS index_granularity = 8192;

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Index for timeframe filtering
ALTER TABLE suho_analytics.live_aggregates
ADD INDEX idx_timeframe timeframe TYPE minmax GRANULARITY 1;

-- Index for time range queries
ALTER TABLE suho_analytics.live_aggregates
ADD INDEX idx_time time TYPE minmax GRANULARITY 1;

-- ============================================================================
-- Materialized Views (Pre-aggregated Statistics)
-- ============================================================================

-- Hourly statistics per symbol + timeframe
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.live_aggregates_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (symbol, timeframe, hour)
AS SELECT
    toStartOfHour(time) AS hour,
    symbol,
    timeframe,
    COUNT(*) AS candle_count,
    SUM(tick_count) AS total_ticks,
    AVG(avg_spread) AS mean_avg_spread,
    AVG(max_spread) AS mean_max_spread,
    AVG(min_spread) AS mean_min_spread,
    AVG(price_range) AS mean_price_range,
    AVG(pct_change) AS mean_pct_change,
    SUM(is_complete) AS complete_candles,
    COUNT(*) - SUM(is_complete) AS incomplete_candles
FROM suho_analytics.live_aggregates
GROUP BY hour, symbol, timeframe;

-- Daily statistics per symbol
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.live_aggregates_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (symbol, day)
AS SELECT
    toDate(time) AS day,
    symbol,
    COUNT(*) AS total_candles,
    SUM(tick_count) AS total_ticks,
    AVG(avg_spread) AS daily_avg_spread,
    MAX(max_spread) AS daily_max_spread,
    MIN(min_spread) AS daily_min_spread,
    MAX(high) AS daily_high,
    MIN(low) AS daily_low,
    first_value(open) AS daily_open,
    last_value(close) AS daily_close,
    AVG(pct_change) AS avg_pct_change,
    stddevPop(pct_change) AS volatility
FROM suho_analytics.live_aggregates
GROUP BY day, symbol;

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Calculate mid price from OHLC
CREATE FUNCTION IF NOT EXISTS get_ohlc_mid(open Decimal(18,5), high Decimal(18,5), low Decimal(18,5), close Decimal(18,5))
RETURNS Decimal(18,5)
AS (open + high + low + close) / 4;

-- Calculate candle body size
CREATE FUNCTION IF NOT EXISTS get_body_size(open Decimal(18,5), close Decimal(18,5))
RETURNS Decimal(18,5)
AS abs(close - open);

-- Calculate upper shadow
CREATE FUNCTION IF NOT EXISTS get_upper_shadow(high Decimal(18,5), open Decimal(18,5), close Decimal(18,5))
RETURNS Decimal(18,5)
AS high - greatest(open, close);

-- Calculate lower shadow
CREATE FUNCTION IF NOT EXISTS get_lower_shadow(low Decimal(18,5), open Decimal(18,5), close Decimal(18,5))
RETURNS Decimal(18,5)
AS least(open, close) - low;

-- ============================================================================
-- Verification Queries (Post-Deployment)
-- ============================================================================

-- Example query 1: Check data coverage per symbol/timeframe
-- SELECT
--     symbol,
--     timeframe,
--     COUNT(*) AS candles,
--     MIN(time) AS oldest,
--     MAX(time) AS newest,
--     SUM(tick_count) AS total_ticks,
--     AVG(avg_spread) AS mean_spread,
--     AVG(pct_change) AS mean_pct_change
-- FROM suho_analytics.live_aggregates
-- WHERE time > now() - INTERVAL 24 HOUR
-- GROUP BY symbol, timeframe
-- ORDER BY symbol, timeframe;

-- Example query 2: Check spread metrics (should NOT be 0)
-- SELECT
--     symbol,
--     timeframe,
--     AVG(avg_spread) AS mean_avg_spread,
--     AVG(max_spread) AS mean_max_spread,
--     AVG(min_spread) AS mean_min_spread
-- FROM suho_analytics.live_aggregates
-- WHERE time > now() - INTERVAL 1 HOUR
-- GROUP BY symbol, timeframe;

-- Example query 3: Check completeness ratio
-- SELECT
--     symbol,
--     timeframe,
--     COUNT(*) AS total,
--     SUM(is_complete) AS complete,
--     COUNT(*) - SUM(is_complete) AS incomplete,
--     (SUM(is_complete) * 100.0 / COUNT(*)) AS complete_pct
-- FROM suho_analytics.live_aggregates
-- WHERE time > now() - INTERVAL 24 HOUR
-- GROUP BY symbol, timeframe;

-- ============================================================================
-- Schema Documentation
-- ============================================================================

-- Table comments
COMMENT COLUMN suho_analytics.live_aggregates.time IS 'Candle timestamp (start of period)';
COMMENT COLUMN suho_analytics.live_aggregates.symbol IS 'Trading pair (e.g., EURUSD, XAUUSD)';
COMMENT COLUMN suho_analytics.live_aggregates.timeframe IS 'Candle timeframe (5m, 15m, 30m, 1h, 4h, 1d, 1w)';
COMMENT COLUMN suho_analytics.live_aggregates.open IS 'Opening price';
COMMENT COLUMN suho_analytics.live_aggregates.high IS 'Highest price';
COMMENT COLUMN suho_analytics.live_aggregates.low IS 'Lowest price';
COMMENT COLUMN suho_analytics.live_aggregates.close IS 'Closing price';
COMMENT COLUMN suho_analytics.live_aggregates.tick_count IS 'Number of ticks in candle';
COMMENT COLUMN suho_analytics.live_aggregates.avg_spread IS 'Average bid-ask spread (volatility indicator)';
COMMENT COLUMN suho_analytics.live_aggregates.max_spread IS 'Maximum spread (liquidity indicator)';
COMMENT COLUMN suho_analytics.live_aggregates.min_spread IS 'Minimum spread (best execution price)';
COMMENT COLUMN suho_analytics.live_aggregates.price_range IS 'High - Low in pips';
COMMENT COLUMN suho_analytics.live_aggregates.pct_change IS 'Percentage change: (close - open) / open * 100';
COMMENT COLUMN suho_analytics.live_aggregates.is_complete IS 'Quality flag: 1 = complete (>= 5 ticks), 0 = incomplete';
COMMENT COLUMN suho_analytics.live_aggregates.created_at IS 'Ingestion timestamp';

-- ============================================================================
-- Migration Notes
-- ============================================================================
-- v1.8.0 (2025-10-18):
-- - Renamed from aggregates to live_aggregates
-- - Reduced from 18 columns to 15 columns
-- - Added ML features: avg_spread, max_spread, min_spread, pct_change, is_complete
-- - Removed: vwap, body_pips, start_time, end_time, source, event_type, indicators, version
-- - Changed timeframe from String to Enum8 (8x storage efficiency)
-- - Changed volume to tick_count (more accurate naming)
-- - Changed range_pips to price_range (standardized naming)
-- - Changed timestamp to time (standardized naming)
-- - TTL: 7 days (live data only, historical moved to historical_aggregates)
-- ============================================================================
