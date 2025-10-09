-- ClickHouse ML Training Data Table
-- Stores 63 features + metadata + target variable for ML training

CREATE TABLE IF NOT EXISTS suho_analytics.ml_training_data
(
    -- Metadata
    symbol String,
    timeframe String,
    timestamp DateTime64(3),
    timestamp_ms UInt64,

    -- Price data (for reference)
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume UInt64,

    -- === TIER 1: CRITICAL FEATURES (50%+ Importance) ===

    -- News/Calendar Features (8 features - 20%)
    upcoming_high_impact_events_4h UInt8,
    time_to_next_event_minutes Int32,
    event_impact_score UInt8,
    is_pre_news_zone UInt8,
    is_post_news_zone UInt8,
    event_type_category String,
    actual_vs_forecast_deviation Float64,
    historical_event_volatility Float64,

    -- Price Action/Structure Features (10 features - 18%)
    support_resistance_distance Float64,
    is_at_key_level UInt8,
    order_block_zone UInt8,
    swing_high_low_distance Float64,
    price_rejection_wick Float64,
    h4_trend_direction Int8,
    h4_support_resistance_distance Float64,
    d1_support_resistance_distance Float64,
    w1_swing_high_low Float64,
    multi_tf_alignment UInt8,

    -- === TIER 2: HIGH IMPORTANCE (15% each) ===

    -- Multi-Timeframe Features (9 features - 15%)
    m5_momentum Float64,
    m15_consolidation UInt8,
    h1_trend Int8,
    h4_structure String,
    d1_bias Int8,
    w1_major_level Float64,
    tf_alignment_score UInt8,
    h4_h1_divergence UInt8,
    d1_w1_alignment UInt8,

    -- Candlestick Pattern Features (9 features - 15%)
    bullish_engulfing UInt8,
    bearish_engulfing UInt8,
    pin_bar_bullish UInt8,
    pin_bar_bearish UInt8,
    doji_indecision UInt8,
    hammer_reversal UInt8,
    shooting_star UInt8,
    morning_star UInt8,
    evening_star UInt8,

    -- Volume Analysis Features (8 features - 15%)
    volume_spike UInt8,
    volume_profile Float64,
    buying_pressure Float64,
    selling_pressure Float64,
    volume_momentum Float64,
    volume_at_level UInt64,
    delta_volume Float64,
    volume_divergence Int8,

    -- === TIER 3: MEDIUM IMPORTANCE ===

    -- Volatility/Regime Features (6 features - 12%)
    atr_current Float64,
    atr_expansion UInt8,
    true_range_pct Float64,
    volatility_regime UInt8,
    adx_value Float64,
    bb_width Float64,

    -- Divergence Features (4 features - 10%)
    rsi_price_divergence Int8,
    macd_price_divergence Int8,
    volume_price_divergence Int8,
    divergence_strength Float64,

    -- Market Context Features (6 features - 8%)
    is_london_session UInt8,
    is_new_york_session UInt8,
    is_asian_session UInt8,
    liquidity_level UInt8,
    day_of_week UInt8,
    time_of_day_category String,

    -- === TIER 4: LOW IMPORTANCE ===

    -- Momentum Features (3 features - 5%)
    rsi_value Float64,
    macd_histogram Float64,
    stochastic_k Float64,

    -- Moving Average Features (2 features - 2%)
    sma_200 Float64,
    ema_50 Float64,

    -- Structure SL/TP Features (5 features - 5%)
    nearest_support_distance Float64,
    nearest_resistance_distance Float64,
    structure_risk_reward Float64,
    atr_based_sl_distance Float64,
    structure_based_tp_distance Float64,

    -- === TARGET VARIABLE ===
    target UInt8,  -- Binary: 0 = not profitable, 1 = profitable
    target_pips Float64,  -- Actual pips moved (for regression models)

    -- Metadata
    data_quality_score Float64,  -- 0-1 score for data completeness
    feature_version String,  -- Feature calculation version (e.g., "1.0.0")
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timeframe, timestamp)
SETTINGS index_granularity = 8192;

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_target ON suho_analytics.ml_training_data (target) TYPE minmax GRANULARITY 4;
CREATE INDEX IF NOT EXISTS idx_volatility_regime ON suho_analytics.ml_training_data (volatility_regime) TYPE set(0) GRANULARITY 4;
CREATE INDEX IF NOT EXISTS idx_event_type ON suho_analytics.ml_training_data (event_type_category) TYPE bloom_filter GRANULARITY 4;

-- Create materialized view for training data statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.ml_training_stats
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timeframe, date)
AS
SELECT
    symbol,
    timeframe,
    toDate(timestamp) AS date,
    count() AS total_samples,
    sumIf(target, target = 1) AS profitable_samples,
    sumIf(target, target = 0) AS unprofitable_samples,
    avg(target_pips) AS avg_pips,
    avg(data_quality_score) AS avg_quality,
    min(timestamp) AS min_timestamp,
    max(timestamp) AS max_timestamp
FROM suho_analytics.ml_training_data
GROUP BY symbol, timeframe, date;

-- Grant permissions
GRANT SELECT, INSERT ON suho_analytics.ml_training_data TO suho_analytics;
GRANT SELECT ON suho_analytics.ml_training_stats TO suho_analytics;
