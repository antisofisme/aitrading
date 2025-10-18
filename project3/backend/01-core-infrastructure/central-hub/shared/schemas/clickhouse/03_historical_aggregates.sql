-- ============================================================================
-- ClickHouse Schema: historical_aggregates (Historical OHLCV Candles)
-- ============================================================================
-- Purpose: Store historical aggregated candles (long-term storage for ML training)
-- Retention: 10 years (unlimited historical data)
-- Engine: MergeTree with partitioning by year + symbol
-- ============================================================================

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS suho_analytics.historical_aggregates;

-- Create historical_aggregates table (15 columns - same as live_aggregates)
CREATE TABLE IF NOT EXISTS suho_analytics.historical_aggregates (
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
PARTITION BY (toYear(time), symbol)
ORDER BY (symbol, timeframe, time)
TTL toDateTime(time) + INTERVAL 10 YEAR
SETTINGS index_granularity = 8192;

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Index for timeframe filtering
ALTER TABLE suho_analytics.historical_aggregates
ADD INDEX idx_timeframe timeframe TYPE minmax GRANULARITY 1;

-- Index for time range queries
ALTER TABLE suho_analytics.historical_aggregates
ADD INDEX idx_time time TYPE minmax GRANULARITY 1;

-- ============================================================================
-- Materialized Views (Statistics)
-- ============================================================================

-- Yearly statistics per symbol + timeframe
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.historical_aggregates_yearly
ENGINE = SummingMergeTree()
PARTITION BY year
ORDER BY (symbol, timeframe, year)
AS SELECT
    toYear(time) AS year,
    symbol,
    timeframe,
    COUNT(*) AS candle_count,
    SUM(tick_count) AS total_ticks,
    AVG(avg_spread) AS mean_avg_spread,
    AVG(max_spread) AS mean_max_spread,
    AVG(min_spread) AS mean_min_spread,
    AVG(price_range) AS mean_price_range,
    AVG(pct_change) AS mean_pct_change,
    stddevPop(pct_change) AS volatility,
    SUM(is_complete) AS complete_candles,
    COUNT(*) - SUM(is_complete) AS incomplete_candles
FROM suho_analytics.historical_aggregates
GROUP BY year, symbol, timeframe;

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
--     dateDiff('day', MIN(time), MAX(time)) AS days_span,
--     SUM(tick_count) AS total_ticks,
--     AVG(avg_spread) AS mean_spread,
--     formatReadableSize(COUNT(*) * 256) AS approx_size
-- FROM suho_analytics.historical_aggregates
-- GROUP BY symbol, timeframe
-- ORDER BY symbol, timeframe;

-- Example query 2: Check yearly distribution
-- SELECT
--     toYear(time) AS year,
--     symbol,
--     COUNT(*) AS candles,
--     SUM(tick_count) AS total_ticks
-- FROM suho_analytics.historical_aggregates
-- WHERE timeframe = '1h'
-- GROUP BY year, symbol
-- ORDER BY year, symbol;

-- ============================================================================
-- Schema Documentation
-- ============================================================================

COMMENT COLUMN suho_analytics.historical_aggregates.time IS 'Candle timestamp (start of period)';
COMMENT COLUMN suho_analytics.historical_aggregates.symbol IS 'Trading pair (e.g., EURUSD, XAUUSD)';
COMMENT COLUMN suho_analytics.historical_aggregates.timeframe IS 'Candle timeframe (5m, 15m, 30m, 1h, 4h, 1d, 1w)';
COMMENT COLUMN suho_analytics.historical_aggregates.open IS 'Opening price';
COMMENT COLUMN suho_analytics.historical_aggregates.high IS 'Highest price';
COMMENT COLUMN suho_analytics.historical_aggregates.low IS 'Lowest price';
COMMENT COLUMN suho_analytics.historical_aggregates.close IS 'Closing price';
COMMENT COLUMN suho_analytics.historical_aggregates.tick_count IS 'Number of ticks in candle';
COMMENT COLUMN suho_analytics.historical_aggregates.avg_spread IS 'Average bid-ask spread (volatility indicator)';
COMMENT COLUMN suho_analytics.historical_aggregates.max_spread IS 'Maximum spread (liquidity indicator)';
COMMENT COLUMN suho_analytics.historical_aggregates.min_spread IS 'Minimum spread (best execution price)';
COMMENT COLUMN suho_analytics.historical_aggregates.price_range IS 'High - Low in pips';
COMMENT COLUMN suho_analytics.historical_aggregates.pct_change IS 'Percentage change: (close - open) / open * 100';
COMMENT COLUMN suho_analytics.historical_aggregates.is_complete IS 'Quality flag: 1 = complete (>= 5 ticks), 0 = incomplete';
COMMENT COLUMN suho_analytics.historical_aggregates.created_at IS 'Ingestion timestamp';

-- ============================================================================
-- Data Sources
-- ============================================================================
-- Source 1: Historical tick aggregation from historical_ticks
-- Source 2: polygon-historical-downloader (OHLCV bars from Polygon API)
-- Transport: NATS (market.{symbol}.{timeframe})
-- Writer: data-bridge → clickhouse_writer.py
-- Coverage: 2015-01-01 to present
-- ============================================================================

-- ============================================================================
-- Migration Notes
-- ============================================================================
-- v1.8.0 (2025-10-18):
-- - Created new table for long-term historical storage
-- - Same schema as live_aggregates (15 columns with ML features)
-- - TTL: 10 years (vs 7 days for live_aggregates)
-- - Partitioning: (year, symbol) for efficient historical queries
-- - Purpose: ML training data, backtesting, feature engineering
-- ============================================================================
