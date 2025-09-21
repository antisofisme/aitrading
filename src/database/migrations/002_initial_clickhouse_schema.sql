-- =====================================================
-- Migration 002: Initial ClickHouse Schema Setup
-- Version: 1.0.0
-- Created: 2025-09-21
-- Description: High-frequency trading data and multi-tier log storage
-- =====================================================

-- Create migrations table for ClickHouse
CREATE TABLE IF NOT EXISTS schema_migrations (
    version String,
    description String,
    applied_at DateTime DEFAULT now(),
    applied_by String DEFAULT 'system',
    checksum String,
    execution_time_ms UInt32 DEFAULT 0,
    status String DEFAULT 'pending'
) ENGINE = MergeTree()
ORDER BY version;

-- Record this migration
INSERT INTO schema_migrations (version, description, checksum, status)
VALUES ('002', 'Initial ClickHouse schema for trading analytics and log storage', MD5('002_initial_clickhouse_schema'), 'executing');

-- =====================================================
-- EXECUTION BLOCK
-- =====================================================

-- Market data tables
CREATE TABLE IF NOT EXISTS market_ticks (
    timestamp DateTime64(3, 'UTC'),
    symbol LowCardinality(String),
    bid Float64,
    ask Float64,
    volume UInt64,
    spread Float32 MATERIALIZED ask - bid,
    mid_price Float64 MATERIALIZED (bid + ask) / 2,
    tick_direction Int8,
    is_trade_tick Bool DEFAULT 0,
    trade_size UInt64 DEFAULT 0,
    data_source LowCardinality(String) DEFAULT 'MT5',
    quality_score UInt8 DEFAULT 100,
    date Date MATERIALIZED toDate(timestamp),
    hour UInt8 MATERIALIZED toHour(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS market_ohlcv (
    timestamp DateTime64(3, 'UTC'),
    symbol LowCardinality(String),
    timeframe LowCardinality(String),
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume UInt64,
    tick_count UInt32,
    sma_20 Float64 DEFAULT 0,
    ema_20 Float64 DEFAULT 0,
    rsi_14 Float64 DEFAULT 0,
    atr_14 Float64 DEFAULT 0,
    price_change Float64 MATERIALIZED close - open,
    price_change_pct Float32 MATERIALIZED (close - open) / open * 100,
    true_range Float64 DEFAULT 0,
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY (timeframe, toYYYYMM(timestamp))
ORDER BY (symbol, timeframe, timestamp)
TTL timestamp + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- Trading execution tables
CREATE TABLE IF NOT EXISTS trading_signals (
    id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3, 'UTC'),
    user_id UUID,
    symbol LowCardinality(String),
    timeframe LowCardinality(String),
    signal_type LowCardinality(String),
    signal_strength Float32,
    confidence_score Float32,
    ensemble_prediction Float32,
    market_regime LowCardinality(String),
    regime_confidence Float32,
    correlation_score Float32,
    stop_loss Float64,
    take_profit Float64,
    position_size Float64,
    risk_reward_ratio Float32,
    model_version String,
    feature_importance Array(Float32),
    model_uncertainty Float32,
    executed Bool DEFAULT 0,
    execution_price Float64 DEFAULT 0,
    execution_time DateTime64(3, 'UTC') DEFAULT toDateTime64(0, 3),
    pnl Float64 DEFAULT 0,
    pnl_pct Float32 DEFAULT 0,
    duration_minutes UInt32 DEFAULT 0,
    date Date MATERIALIZED toDate(timestamp),
    created_at DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree()
PARTITION BY (toYYYYMM(timestamp), user_id)
ORDER BY (user_id, symbol, timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS trade_executions (
    id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3, 'UTC'),
    user_id UUID,
    trading_account_id UUID,
    signal_id UUID,
    symbol LowCardinality(String),
    direction LowCardinality(String),
    entry_price Float64,
    exit_price Float64 DEFAULT 0,
    volume Float64,
    stop_loss Float64,
    take_profit Float64,
    actual_stop_loss Float64 DEFAULT 0,
    actual_take_profit Float64 DEFAULT 0,
    execution_type LowCardinality(String),
    slippage Float32 DEFAULT 0,
    commission Float64 DEFAULT 0,
    swap Float64 DEFAULT 0,
    status LowCardinality(String),
    opened_at DateTime64(3, 'UTC'),
    closed_at DateTime64(3, 'UTC') DEFAULT toDateTime64(0, 3),
    gross_pnl Float64 DEFAULT 0,
    net_pnl Float64 DEFAULT 0,
    pnl_pct Float32 DEFAULT 0,
    duration_minutes UInt32 DEFAULT 0,
    max_favorable_excursion Float64 DEFAULT 0,
    max_adverse_excursion Float64 DEFAULT 0,
    mt5_ticket UInt64 DEFAULT 0,
    mt5_order_id UInt64 DEFAULT 0,
    date Date MATERIALIZED toDate(timestamp),
    created_at DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree()
PARTITION BY (toYYYYMM(timestamp), user_id)
ORDER BY (user_id, trading_account_id, timestamp)
TTL timestamp + INTERVAL 7 YEAR
SETTINGS index_granularity = 8192;

-- Multi-tier log storage (81% cost reduction)
CREATE TABLE IF NOT EXISTS logs_hot (
    timestamp DateTime64(3, 'UTC'),
    service_name LowCardinality(String),
    log_level LowCardinality(String),
    user_id UUID,
    session_id UUID,
    message String,
    details String DEFAULT '',
    context Map(String, String),
    trace_id String DEFAULT '',
    span_id String DEFAULT '',
    request_id String DEFAULT '',
    execution_time_ms UInt32 DEFAULT 0,
    memory_usage_mb UInt32 DEFAULT 0,
    cpu_usage_pct Float32 DEFAULT 0,
    error_code String DEFAULT '',
    error_category LowCardinality(String) DEFAULT '',
    stack_trace String DEFAULT '',
    hostname LowCardinality(String),
    process_id UInt32,
    thread_id UInt32,
    date Date MATERIALIZED toDate(timestamp),
    hour UInt8 MATERIALIZED toHour(timestamp)
) ENGINE = MergeTree()
PARTITION BY (log_level, toYYYYMMDD(timestamp))
ORDER BY (service_name, timestamp)
TTL timestamp + INTERVAL 1 DAY
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS logs_warm (
    timestamp DateTime64(3, 'UTC'),
    service_name LowCardinality(String),
    log_level LowCardinality(String),
    user_id UUID,
    message String CODEC(LZ4),
    details String CODEC(LZ4),
    context Map(String, String),
    avg_execution_time_ms Float32,
    max_execution_time_ms UInt32,
    error_count UInt32,
    success_count UInt32,
    error_codes Array(String),
    error_categories Array(LowCardinality(String)),
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY (toYYYYMM(timestamp), log_level)
ORDER BY (service_name, timestamp)
TTL timestamp + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;

CREATE TABLE IF NOT EXISTS logs_cold (
    timestamp DateTime64(3, 'UTC'),
    service_name LowCardinality(String),
    log_level LowCardinality(String),
    user_id UUID,
    audit_event String CODEC(ZSTD(9)),
    regulatory_data String CODEC(ZSTD(9)),
    compliance_category LowCardinality(String),
    message_compressed String CODEC(ZSTD(9)),
    context_compressed String CODEC(ZSTD(9)),
    retention_category LowCardinality(String),
    legal_hold Bool DEFAULT 0,
    date Date MATERIALIZED toDate(timestamp),
    year UInt16 MATERIALIZED toYear(timestamp)
) ENGINE = MergeTree()
PARTITION BY (retention_category, year)
ORDER BY (service_name, timestamp)
TTL timestamp + INTERVAL 7 YEAR
SETTINGS index_granularity = 8192;

-- ML model performance tracking
CREATE TABLE IF NOT EXISTS ml_predictions (
    id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3, 'UTC'),
    user_id UUID,
    model_name LowCardinality(String),
    model_version String,
    symbol LowCardinality(String),
    timeframe LowCardinality(String),
    input_features Array(Float32),
    feature_names Array(String),
    prediction Float32,
    confidence_score Float32,
    probability_distribution Array(Float32),
    ensemble_predictions Array(Float32),
    ensemble_weights Array(Float32),
    ensemble_consensus Float32,
    market_regime LowCardinality(String),
    regime_confidence Float32,
    volatility_regime LowCardinality(String),
    actual_outcome Float32 DEFAULT 0,
    prediction_error Float32 DEFAULT 0,
    accuracy_score Float32 DEFAULT 0,
    inference_time_ms UInt16,
    model_complexity_score UInt8,
    feature_importance Array(Float32),
    date Date MATERIALIZED toDate(timestamp),
    created_at DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree()
PARTITION BY (toYYYYMM(timestamp), model_name)
ORDER BY (model_name, timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- User activity tracking
CREATE TABLE IF NOT EXISTS user_activity (
    timestamp DateTime64(3, 'UTC'),
    user_id UUID,
    session_id UUID,
    activity_type LowCardinality(String),
    page_url String DEFAULT '',
    action String,
    http_method LowCardinality(String) DEFAULT '',
    response_status UInt16 DEFAULT 200,
    response_time_ms UInt32,
    ip_address IPv4,
    user_agent String,
    device_type LowCardinality(String),
    subscription_tier LowCardinality(String),
    feature_used String DEFAULT '',
    api_endpoint String DEFAULT '',
    cpu_time_ms UInt32 DEFAULT 0,
    memory_usage_mb UInt32 DEFAULT 0,
    database_queries UInt16 DEFAULT 0,
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY (toYYYYMM(timestamp), subscription_tier)
ORDER BY (user_id, timestamp)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- Configuration tables for cost optimization
CREATE TABLE IF NOT EXISTS log_retention_policies (
    log_level LowCardinality(String),
    retention_days UInt16,
    storage_tier LowCardinality(String),
    compression_algo LowCardinality(String),
    compliance_required Bool DEFAULT 0,
    cost_per_gb_month Float32,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY log_level;

CREATE TABLE IF NOT EXISTS storage_tiers (
    tier_name LowCardinality(String),
    technology String,
    max_query_latency_ms UInt16,
    cost_per_gb_month Float32,
    compression_ratio Float32,
    is_active Bool DEFAULT 1,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY tier_name;

-- Insert configuration data
INSERT INTO log_retention_policies VALUES
('DEBUG', 7, 'hot', 'none', 0, 0.90, now(), now()),
('INFO', 30, 'warm', 'lz4', 0, 0.425, now(), now()),
('WARNING', 90, 'warm', 'zstd', 0, 0.425, now(), now()),
('ERROR', 180, 'cold', 'zstd', 0, 0.18, now(), now()),
('CRITICAL', 365, 'cold', 'zstd', 1, 0.18, now(), now());

INSERT INTO storage_tiers VALUES
('hot', 'ClickHouse Memory Engine + DragonflyDB', 1, 0.90, 1.0, 1, now()),
('warm', 'ClickHouse SSD with LZ4', 100, 0.425, 3.0, 1, now()),
('cold', 'ClickHouse High Compression ZSTD', 2000, 0.18, 5.0, 1, now());

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_user_signals ON trading_signals(user_id, timestamp) TYPE minmax GRANULARITY 8192;
CREATE INDEX IF NOT EXISTS idx_user_trades ON trade_executions(user_id, timestamp) TYPE minmax GRANULARITY 8192;
CREATE INDEX IF NOT EXISTS idx_symbol_ticks ON market_ticks(symbol, timestamp) TYPE minmax GRANULARITY 8192;
CREATE INDEX IF NOT EXISTS idx_logs_service ON logs_hot(service_name, log_level) TYPE set(100) GRANULARITY 8192;

-- Update migration status
ALTER TABLE schema_migrations UPDATE execution_time_ms = 0, status = 'completed' WHERE version = '002';

-- Verification query
SELECT
    version,
    description,
    applied_at,
    status,
    execution_time_ms || 'ms' as duration
FROM schema_migrations
WHERE version = '002';

-- Table count verification
SELECT 'ClickHouse tables created: ' || toString(count()) as result
FROM system.tables
WHERE database = currentDatabase()
AND name IN (
    'market_ticks', 'market_ohlcv', 'trading_signals', 'trade_executions',
    'logs_hot', 'logs_warm', 'logs_cold', 'ml_predictions',
    'user_activity', 'log_retention_policies', 'storage_tiers'
);