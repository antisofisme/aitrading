-- ============================================================================
-- ClickHouse Schema: ml_features (ML Training Features - 110 Features)
-- ============================================================================
-- Purpose: Store ONLY derived/calculated features (NOT raw OHLC data)
-- Retention: Historical = Unlimited, Live = 30 days
-- Engine: MergeTree with partitioning by month and timeframe
-- Version: 2.0.0 (2025-10-18)
-- ============================================================================

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS suho_analytics.ml_features;

-- Create ml_features table (110 features total)
CREATE TABLE IF NOT EXISTS suho_analytics.ml_features (
    -- === PRIMARY KEYS & METADATA (5 columns) ===
    time DateTime64(3, 'UTC'),
    symbol String,
    timeframe Enum8('5m'=1, '15m'=2, '30m'=3, '1h'=4, '4h'=5, '1d'=6, '1w'=7),
    feature_version String,
    created_at DateTime64(3, 'UTC'),

    -- === MARKET SESSIONS (5 columns) ===
    active_sessions Array(String),
    active_count UInt8,
    is_overlap UInt8,
    liquidity_level Enum8('very_low'=1, 'low'=2, 'medium'=3, 'high'=4, 'very_high'=5),
    is_london_newyork_overlap UInt8,

    -- === CALENDAR (10 columns) ===
    day_of_week UInt8,
    day_name String,
    is_monday UInt8,
    is_friday UInt8,
    is_weekend UInt8,
    week_of_month UInt8,
    week_of_year UInt8,
    is_month_start UInt8,
    is_month_end UInt8,
    day_of_month UInt8,

    -- === TIME (6 columns) ===
    hour_utc UInt8,
    minute UInt8,
    quarter_hour UInt8,
    is_market_open UInt8,
    is_london_open UInt8,
    is_ny_open UInt8,

    -- === TECHNICAL INDICATORS (14 columns) ===
    rsi_14 Nullable(Float64),
    macd Nullable(Float64),
    macd_signal Nullable(Float64),
    macd_histogram Nullable(Float64),
    bb_upper Nullable(Float64),
    bb_middle Nullable(Float64),
    bb_lower Nullable(Float64),
    stoch_k Nullable(Float64),
    stoch_d Nullable(Float64),
    sma_50 Nullable(Float64),
    sma_200 Nullable(Float64),
    ema_12 Nullable(Float64),
    cci Nullable(Float64),
    mfi Nullable(Float64),

    -- === FIBONACCI (7 columns) ===
    fib_0 Nullable(Float64),
    fib_236 Nullable(Float64),
    fib_382 Nullable(Float64),
    fib_50 Nullable(Float64),
    fib_618 Nullable(Float64),
    fib_786 Nullable(Float64),
    fib_100 Nullable(Float64),

    -- === EXTERNAL DATA (12 columns) ===
    upcoming_event_minutes Nullable(Int32),
    upcoming_event_impact Nullable(String),
    recent_event_minutes Nullable(Int32),
    gdp_latest Nullable(Float64),
    unemployment_latest Nullable(Float64),
    cpi_latest Nullable(Float64),
    interest_rate_latest Nullable(Float64),
    gold_price Nullable(Float64),
    oil_price Nullable(Float64),
    gold_change_pct Nullable(Float64),
    oil_change_pct Nullable(Float64),

    -- === LAGGED FEATURES (15 columns) ===
    close_lag_1 Nullable(Float64),
    close_lag_2 Nullable(Float64),
    close_lag_3 Nullable(Float64),
    close_lag_5 Nullable(Float64),
    close_lag_10 Nullable(Float64),
    rsi_lag_1 Nullable(Float64),
    rsi_lag_2 Nullable(Float64),
    macd_lag_1 Nullable(Float64),
    return_lag_1 Nullable(Float64),
    return_lag_2 Nullable(Float64),
    return_lag_3 Nullable(Float64),
    volume_lag_1 Nullable(UInt32),
    volume_lag_2 Nullable(UInt32),
    spread_lag_1 Nullable(Float64),
    spread_lag_2 Nullable(Float64),

    -- === ROLLING STATISTICS (8 columns) ===
    price_rolling_mean_10 Nullable(Float64),
    price_rolling_mean_20 Nullable(Float64),
    price_rolling_mean_50 Nullable(Float64),
    price_rolling_std_10 Nullable(Float64),
    price_rolling_std_20 Nullable(Float64),
    price_rolling_max_20 Nullable(Float64),
    price_rolling_min_20 Nullable(Float64),
    dist_from_rolling_mean_20 Nullable(Float64),

    -- === MULTI-TIMEFRAME (10 columns) ===
    htf_trend_direction Nullable(String),
    htf_rsi Nullable(Float64),
    htf_macd Nullable(Float64),
    htf_sma_50 Nullable(Float64),
    ltf_volatility Nullable(Float64),
    ltf_volume Nullable(Float64),
    is_all_tf_aligned UInt8,
    tf_alignment_score Float64,
    htf_support_level Nullable(Float64),
    htf_resistance_level Nullable(Float64),

    -- === TARGET VARIABLES (5 columns) - CRITICAL ===
    target_return_5min Nullable(Float64),
    target_return_15min Nullable(Float64),
    target_return_1h Nullable(Float64),
    target_direction Nullable(String),
    target_is_profitable Nullable(UInt8)
)
ENGINE = MergeTree()
PARTITION BY (toYYYYMM(time), timeframe)
ORDER BY (symbol, timeframe, time)
SETTINGS index_granularity = 8192;

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

ALTER TABLE suho_analytics.ml_features
ADD INDEX idx_symbol symbol TYPE set(0) GRANULARITY 1;

ALTER TABLE suho_analytics.ml_features
ADD INDEX idx_time time TYPE minmax GRANULARITY 1;

-- ============================================================================
-- Verification Query (Post-Deployment)
-- ============================================================================

-- Example: Check feature completeness
-- SELECT
--     symbol,
--     timeframe,
--     COUNT(*) AS total_rows,
--     countIf(rsi_14 IS NOT NULL) AS has_rsi,
--     countIf(target_return_1h IS NOT NULL) AS has_targets
-- FROM suho_analytics.ml_features
-- WHERE time >= today() - 7
-- GROUP BY symbol, timeframe
-- ORDER BY symbol, timeframe;

-- ============================================================================
-- ML Training Query Example (JOIN with aggregates for raw OHLC)
-- ============================================================================

-- SELECT
--     a.time, a.symbol, a.timeframe,
--     a.open, a.high, a.low, a.close,  -- Raw data from aggregates
--     a.tick_count, a.avg_spread,      -- Volume & spread from aggregates
--     f.*                               -- All 110 derived features
-- FROM suho_analytics.live_aggregates a
-- LEFT JOIN suho_analytics.ml_features f
--     ON a.time = f.time AND a.symbol = f.symbol AND a.timeframe = f.timeframe
-- WHERE a.time BETWEEN '2023-01-01' AND '2025-09-01'
--   AND f.target_return_1h IS NOT NULL
-- ORDER BY a.time;

-- ============================================================================
-- Schema Documentation
-- ============================================================================

COMMENT COLUMN suho_analytics.ml_features.time IS 'Feature timestamp (same as candle time)';
COMMENT COLUMN suho_analytics.ml_features.symbol IS 'Trading symbol (C:EURUSD, C:XAUUSD, etc.)';
COMMENT COLUMN suho_analytics.ml_features.timeframe IS 'Candle timeframe';
COMMENT COLUMN suho_analytics.ml_features.feature_version IS 'Feature calculation version';
COMMENT COLUMN suho_analytics.ml_features.created_at IS 'When features were calculated';

-- ============================================================================
-- Migration Notes
-- ============================================================================
-- v2.0.0 (2025-10-18):
-- - Complete redesign: 110 ML features for MVP
-- - Removed raw data duplication (OHLC stored ONLY in aggregates)
-- - Added 38 critical features: lagged (15), rolling (8), multi-TF (10), targets (5)
-- - Phase 1 MVP: 97 features implemented
-- - JOIN with aggregates required for complete training dataset
-- ============================================================================
