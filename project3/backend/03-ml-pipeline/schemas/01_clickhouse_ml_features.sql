-- =======================================================================
-- CLICKHOUSE ML FEATURE ENGINEERING SCHEMA
-- =======================================================================
-- Optimized for ML/DL training data with multi-horizon predictions
-- Stores engineered features, technical indicators, and labels
-- =======================================================================

CREATE DATABASE IF NOT EXISTS ml_training;

USE ml_training;

-- =======================================================================
-- TABLE 1: FEATURE STORE - TRAINING DATA
-- =======================================================================
-- Wide table design for ML training (denormalized for performance)
-- Each row = complete feature vector for one timestamp + symbol

CREATE TABLE IF NOT EXISTS ml_features (
    -- ===========================================
    -- PRIMARY IDENTIFIERS
    -- ===========================================
    tenant_id String,                      -- Multi-tenant isolation
    user_id String,                        -- User-specific models
    symbol String,                         -- Trading pair (EUR/USD, XAU/USD)
    timeframe String,                      -- Base timeframe (1m, 5m, 15m, 1h, 4h, 1d)
    timestamp DateTime64(3, 'UTC'),        -- Feature timestamp
    timestamp_ms UInt64,                   -- Unix milliseconds

    -- ===========================================
    -- RAW OHLCV DATA (Base Features)
    -- ===========================================
    open Decimal(18, 5),
    high Decimal(18, 5),
    low Decimal(18, 5),
    close Decimal(18, 5),
    volume UInt64,

    -- Price derivatives
    mid_price Decimal(18, 5),              -- (bid + ask) / 2
    spread Decimal(10, 5),                 -- ask - bid
    range_pips Decimal(10, 5),             -- high - low
    body_pips Decimal(10, 5),              -- |close - open|

    -- ===========================================
    -- TECHNICAL INDICATORS - TREND
    -- ===========================================
    -- Moving Averages
    sma_10 Decimal(18, 5),
    sma_20 Decimal(18, 5),
    sma_50 Decimal(18, 5),
    sma_100 Decimal(18, 5),
    sma_200 Decimal(18, 5),

    ema_10 Decimal(18, 5),
    ema_20 Decimal(18, 5),
    ema_50 Decimal(18, 5),
    ema_100 Decimal(18, 5),
    ema_200 Decimal(18, 5),

    -- Moving Average Convergence
    ma_cross_10_20 Int8,                  -- 1 if sma10 > sma20, -1 otherwise
    ma_cross_20_50 Int8,
    ma_cross_50_200 Int8,                 -- Golden/Death cross

    -- MACD
    macd_line Decimal(18, 8),
    macd_signal Decimal(18, 8),
    macd_histogram Decimal(18, 8),
    macd_cross Int8,                       -- 1 if bullish cross, -1 bearish

    -- ADX (Trend Strength)
    adx_14 Decimal(8, 4),
    plus_di_14 Decimal(8, 4),
    minus_di_14 Decimal(8, 4),
    adx_trend String,                      -- 'strong_up', 'strong_down', 'weak'

    -- Ichimoku Cloud
    tenkan_sen Decimal(18, 5),
    kijun_sen Decimal(18, 5),
    senkou_span_a Decimal(18, 5),
    senkou_span_b Decimal(18, 5),
    chikou_span Decimal(18, 5),
    cloud_position String,                 -- 'above', 'below', 'inside'

    -- ===========================================
    -- TECHNICAL INDICATORS - MOMENTUM
    -- ===========================================
    -- RSI
    rsi_14 Decimal(8, 4),
    rsi_zone String,                       -- 'overbought', 'oversold', 'neutral'
    rsi_divergence Int8,                   -- Bullish/bearish divergence signal

    -- Stochastic
    stoch_k Decimal(8, 4),
    stoch_d Decimal(8, 4),
    stoch_cross Int8,
    stoch_zone String,                     -- 'overbought', 'oversold', 'neutral'

    -- CCI (Commodity Channel Index)
    cci_20 Decimal(10, 4),
    cci_zone String,

    -- Williams %R
    williams_r_14 Decimal(8, 4),

    -- Rate of Change
    roc_10 Decimal(10, 6),
    roc_20 Decimal(10, 6),
    momentum_10 Decimal(10, 6),

    -- ===========================================
    -- TECHNICAL INDICATORS - VOLATILITY
    -- ===========================================
    -- Bollinger Bands
    bb_upper_20_2 Decimal(18, 5),
    bb_middle_20_2 Decimal(18, 5),
    bb_lower_20_2 Decimal(18, 5),
    bb_width Decimal(10, 6),               -- (upper - lower) / middle
    bb_percent_b Decimal(8, 6),            -- Position within bands
    bb_squeeze Int8,                       -- 1 if squeeze detected

    -- ATR (Average True Range)
    atr_14 Decimal(18, 5),
    atr_percent Decimal(8, 6),             -- ATR / close * 100

    -- Keltner Channels
    kc_upper Decimal(18, 5),
    kc_middle Decimal(18, 5),
    kc_lower Decimal(18, 5),

    -- Donchian Channels
    dc_upper_20 Decimal(18, 5),
    dc_lower_20 Decimal(18, 5),

    -- Historical Volatility
    realized_vol_20 Decimal(10, 6),        -- 20-period realized volatility

    -- ===========================================
    -- TECHNICAL INDICATORS - VOLUME
    -- ===========================================
    volume_sma_20 UInt64,
    volume_ratio Decimal(8, 4),            -- current / sma_20

    obv Int64,                             -- On-Balance Volume
    obv_sma_20 Int64,

    vwap Decimal(18, 5),                   -- Volume Weighted Average Price
    vwap_distance Decimal(8, 6),           -- (close - vwap) / vwap

    mfi_14 Decimal(8, 4),                  -- Money Flow Index

    -- ===========================================
    -- PATTERN RECOGNITION
    -- ===========================================
    -- Candlestick patterns (encoded as integers)
    pattern_doji Int8,
    pattern_hammer Int8,
    pattern_shooting_star Int8,
    pattern_engulfing Int8,
    pattern_morning_star Int8,
    pattern_evening_star Int8,

    -- Chart patterns
    pattern_support_resistance String,     -- JSON: levels detected
    pattern_trend_channel String,          -- 'ascending', 'descending', 'none'

    -- ===========================================
    -- MARKET STRUCTURE
    -- ===========================================
    support_level_1 Decimal(18, 5),
    support_level_2 Decimal(18, 5),
    resistance_level_1 Decimal(18, 5),
    resistance_level_2 Decimal(18, 5),

    pivot_point Decimal(18, 5),
    pivot_r1 Decimal(18, 5),
    pivot_r2 Decimal(18, 5),
    pivot_s1 Decimal(18, 5),
    pivot_s2 Decimal(18, 5),

    -- Higher timeframe context
    htf_trend_1h String,                   -- 'bullish', 'bearish', 'ranging'
    htf_trend_4h String,
    htf_trend_1d String,

    -- ===========================================
    -- EXTERNAL DATA (Enrichment)
    -- ===========================================
    -- Economic Calendar
    upcoming_event_impact String,          -- 'high', 'medium', 'low', 'none'
    time_to_event_minutes Int32,           -- -1 if no event

    -- Sentiment Indicators
    sentiment_score Decimal(6, 4),         -- -1 to 1 (bearish to bullish)
    fear_greed_index UInt8,                -- 0-100

    -- Correlation features
    corr_eurusd Decimal(6, 4),             -- Correlation with EUR/USD
    corr_gold Decimal(6, 4),               -- Correlation with XAU/USD
    corr_dxy Decimal(6, 4),                -- Correlation with Dollar Index

    -- ===========================================
    -- MULTI-HORIZON LABELS (SUPERVISED LEARNING)
    -- ===========================================
    -- Classification labels: direction prediction
    label_direction_1h Int8,               -- 1 (up), 0 (neutral), -1 (down)
    label_direction_4h Int8,
    label_direction_1d Int8,

    -- Regression labels: price change prediction
    label_return_1h Decimal(10, 8),        -- Percentage return in 1 hour
    label_return_4h Decimal(10, 8),
    label_return_1d Decimal(10, 8),

    -- Max favorable/adverse movement (for risk analysis)
    label_max_gain_1h Decimal(10, 8),      -- Max upward move in next 1h
    label_max_loss_1h Decimal(10, 8),      -- Max downward move in next 1h
    label_max_gain_4h Decimal(10, 8),
    label_max_loss_4h Decimal(10, 8),

    -- Trading outcome labels (for RL)
    label_trade_outcome String,            -- 'profitable', 'loss', 'breakeven'
    label_profit_pips Decimal(10, 4),      -- Actual profit if trade executed
    label_optimal_entry Decimal(18, 5),    -- Best entry in next period
    label_optimal_exit Decimal(18, 5),     -- Best exit in next period

    -- ===========================================
    -- METADATA
    -- ===========================================
    data_quality_score Decimal(4, 3),      -- 0-1 quality score
    missing_features Array(String),         -- List of missing indicator names
    feature_version String,                 -- Feature engineering version

    created_at DateTime64(3, 'UTC') DEFAULT now64(3),
    updated_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY (tenant_id, symbol, toYYYYMM(timestamp))
ORDER BY (tenant_id, user_id, symbol, timeframe, timestamp)
TTL toDateTime(timestamp) + INTERVAL 3650 DAY  -- Keep 10 years
SETTINGS index_granularity = 8192;

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_ml_features_tenant_user ON ml_features (tenant_id, user_id) TYPE set(0);
CREATE INDEX IF NOT EXISTS idx_ml_features_symbol ON ml_features (symbol) TYPE set(0);
CREATE INDEX IF NOT EXISTS idx_ml_features_timeframe ON ml_features (timeframe) TYPE set(0);
CREATE INDEX IF NOT EXISTS idx_ml_features_quality ON ml_features (data_quality_score) TYPE minmax;

-- =======================================================================
-- TABLE 2: FEATURE ENGINEERING JOBS
-- =======================================================================
-- Tracks feature computation jobs (for monitoring and debugging)

CREATE TABLE IF NOT EXISTS feature_jobs (
    job_id UUID,
    tenant_id String,
    symbol String,
    timeframe String,
    start_time DateTime64(3, 'UTC'),
    end_time DateTime64(3, 'UTC'),
    rows_processed UInt64,
    rows_inserted UInt64,
    duration_seconds UInt32,
    status String,                         -- 'success', 'failed', 'partial'
    error_message String,
    feature_version String,
    created_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree()
ORDER BY (tenant_id, created_at)
TTL toDateTime(created_at) + INTERVAL 90 DAY;

-- =======================================================================
-- TABLE 3: FEATURE IMPORTANCE TRACKING
-- =======================================================================
-- Stores feature importance from trained models (for feature selection)

CREATE TABLE IF NOT EXISTS feature_importance (
    model_id UUID,
    tenant_id String,
    feature_name String,
    importance_score Decimal(10, 8),
    importance_rank UInt16,
    feature_type String,                   -- 'trend', 'momentum', 'volatility', 'volume'
    created_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(created_at)
ORDER BY (tenant_id, model_id, importance_rank);

-- =======================================================================
-- MATERIALIZED VIEWS - AGGREGATED FEATURES
-- =======================================================================

-- Latest feature vector per symbol (for real-time prediction)
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_features
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (tenant_id, user_id, symbol, timeframe)
AS SELECT
    tenant_id,
    user_id,
    symbol,
    timeframe,
    argMax(timestamp, timestamp) as latest_timestamp,
    argMax(close, timestamp) as latest_close,
    argMax(rsi_14, timestamp) as latest_rsi,
    argMax(macd_histogram, timestamp) as latest_macd_hist,
    argMax(bb_percent_b, timestamp) as latest_bb_pct,
    argMax(adx_14, timestamp) as latest_adx,
    argMax(atr_14, timestamp) as latest_atr,
    argMax(sentiment_score, timestamp) as latest_sentiment,
    argMax(htf_trend_1d, timestamp) as latest_htf_trend,
    argMax(updated_at, timestamp) as updated_at
FROM ml_features
GROUP BY tenant_id, user_id, symbol, timeframe;

-- Feature statistics for normalization
CREATE MATERIALIZED VIEW IF NOT EXISTS feature_stats
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(stats_date)
ORDER BY (tenant_id, symbol, timeframe, stats_date)
AS SELECT
    tenant_id,
    symbol,
    timeframe,
    toDate(timestamp) as stats_date,

    -- Close price stats
    avgState(close) as close_mean,
    stddevPopState(close) as close_std,
    minState(close) as close_min,
    maxState(close) as close_max,

    -- RSI stats
    avgState(rsi_14) as rsi_mean,
    stddevPopState(rsi_14) as rsi_std,

    -- ATR stats
    avgState(atr_14) as atr_mean,
    stddevPopState(atr_14) as atr_std,

    count() as sample_count
FROM ml_features
WHERE data_quality_score > 0.8  -- Only high-quality data
GROUP BY tenant_id, symbol, timeframe, stats_date;

-- =======================================================================
-- SAMPLE QUERIES (For ML Pipeline)
-- =======================================================================

-- Get training dataset for EUR/USD, 1h timeframe, last 2 years
-- SELECT * FROM ml_features
-- WHERE tenant_id = 'tenant_001'
--   AND symbol = 'EUR/USD'
--   AND timeframe = '1h'
--   AND timestamp >= now() - INTERVAL 730 DAY
--   AND data_quality_score > 0.9
-- ORDER BY timestamp;

-- Get feature importance for model selection
-- SELECT feature_name, avg(importance_score) as avg_importance
-- FROM feature_importance
-- WHERE tenant_id = 'tenant_001'
-- GROUP BY feature_name
-- ORDER BY avg_importance DESC
-- LIMIT 20;

-- Check data quality distribution
-- SELECT
--     symbol,
--     timeframe,
--     round(data_quality_score, 1) as quality_bucket,
--     count() as row_count
-- FROM ml_features
-- WHERE timestamp >= now() - INTERVAL 30 DAY
-- GROUP BY symbol, timeframe, quality_bucket
-- ORDER BY symbol, timeframe, quality_bucket;

-- =======================================================================
-- NOTES
-- =======================================================================
-- 1. Wide table design: Optimized for analytical queries (ML training)
-- 2. Multi-tenant isolation: Partitioned by tenant_id
-- 3. User-specific features: Allows personalized models
-- 4. Multi-horizon labels: Support 1h, 4h, 1d predictions
-- 5. Quality tracking: Filter low-quality data during training
-- 6. Feature versioning: Track feature engineering changes
-- 7. 10-year retention: Sufficient for backtesting and research
-- =======================================================================
