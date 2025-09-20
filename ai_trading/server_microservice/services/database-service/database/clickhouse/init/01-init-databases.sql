-- ClickHouse Initialization Script for Neliti Database Service
-- Uses existing schemas from src/schemas/clickhouse/

-- Create main databases
CREATE DATABASE IF NOT EXISTS trading_data;
CREATE DATABASE IF NOT EXISTS analytics_db;
CREATE DATABASE IF NOT EXISTS ml_features;

-- Use trading_data database for raw data
USE trading_data;

-- Raw Data Tables (from raw_data_schemas.py)
-- Ticks table - Real-time tick data from trading platforms
CREATE TABLE IF NOT EXISTS ticks (
    timestamp DateTime64(3) DEFAULT now64(),
    symbol String CODEC(ZSTD),
    bid Float64 CODEC(Gorilla),
    ask Float64 CODEC(Gorilla),
    last Float64 CODEC(Gorilla),
    volume Float64 CODEC(Gorilla),
    spread Float64 CODEC(Gorilla),
    primary_session LowCardinality(String) DEFAULT 'Unknown',
    active_sessions Array(String),
    session_overlap Boolean DEFAULT false,
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    mid_price Float64 MATERIALIZED (bid + ask) / 2,
    INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, symbol, broker)
TTL timestamp + INTERVAL 90 DAY DELETE
SETTINGS index_granularity = 8192;

-- Account info table
CREATE TABLE IF NOT EXISTS account_info (
    timestamp DateTime64(3) DEFAULT now64(),
    account_number String CODEC(ZSTD),
    balance Float64 CODEC(Gorilla),
    equity Float64 CODEC(Gorilla),
    margin Float64 CODEC(Gorilla),
    free_margin Float64 CODEC(Gorilla),
    margin_level Float64 CODEC(Gorilla),
    currency String CODEC(ZSTD),
    server String CODEC(ZSTD),
    company String CODEC(ZSTD),
    leverage UInt32 CODEC(T64),
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_account account_number TYPE set(1000) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, account_number, broker)
TTL timestamp + INTERVAL 365 DAY DELETE
SETTINGS index_granularity = 8192;

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    timestamp DateTime64(3) DEFAULT now64(),
    ticket String CODEC(ZSTD),
    symbol String CODEC(ZSTD),
    position_type String CODEC(ZSTD),
    volume Float64 CODEC(Gorilla),
    price_open Float64 CODEC(Gorilla),
    price_current Float64 CODEC(Gorilla),
    swap Float64 CODEC(Gorilla),
    profit Float64 CODEC(Gorilla),
    comment String CODEC(ZSTD),
    identifier String CODEC(ZSTD),
    time_setup DateTime64(3),
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, symbol, broker)
TTL timestamp + INTERVAL 365 DAY DELETE
SETTINGS index_granularity = 8192;

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    timestamp DateTime64(3) DEFAULT now64(),
    ticket String CODEC(ZSTD),
    symbol String CODEC(ZSTD),
    order_type String CODEC(ZSTD),
    volume Float64 CODEC(Gorilla),
    price_open Float64 CODEC(Gorilla),
    price_current Float64 CODEC(Gorilla),
    price_sl Float64 CODEC(Gorilla),
    price_tp Float64 CODEC(Gorilla),
    comment String CODEC(ZSTD),
    time_setup DateTime64(3),
    time_expiration DateTime64(3),
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, symbol, broker)
TTL timestamp + INTERVAL 365 DAY DELETE
SETTINGS index_granularity = 8192;

-- Trade History table
CREATE TABLE IF NOT EXISTS trade_history (
    timestamp DateTime64(3) DEFAULT now64(),
    ticket String CODEC(ZSTD),
    symbol String CODEC(ZSTD),
    trade_type String CODEC(ZSTD),
    volume Float64 CODEC(Gorilla),
    price_open Float64 CODEC(Gorilla),
    price_close Float64 CODEC(Gorilla),
    profit Float64 CODEC(Gorilla),
    swap Float64 CODEC(Gorilla),
    commission Float64 CODEC(Gorilla),
    comment String CODEC(ZSTD),
    time_open DateTime64(3),
    time_close DateTime64(3),
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, symbol, broker)
TTL timestamp + INTERVAL 2 YEAR DELETE
SETTINGS index_granularity = 8192;

-- Deals History table
CREATE TABLE IF NOT EXISTS deals_history (
    timestamp DateTime64(3) DEFAULT now64(),
    ticket String CODEC(ZSTD),
    order_ticket String CODEC(ZSTD),
    deal_time DateTime64(3),
    symbol String CODEC(ZSTD),
    deal_type LowCardinality(String),
    entry_type LowCardinality(String),
    volume Float64 CODEC(Gorilla),
    price Float64 CODEC(Gorilla),
    commission Float64 CODEC(Gorilla),
    swap Float64 CODEC(Gorilla),
    profit Float64 CODEC(Gorilla),
    fee Float64 CODEC(Gorilla),
    comment String CODEC(ZSTD),
    magic UInt32 CODEC(T64),
    account_login String CODEC(ZSTD),
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_account account_login TYPE set(1000) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192,
    INDEX idx_deal_time deal_time TYPE minmax GRANULARITY 8192
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(deal_time)
ORDER BY (deal_time, account_login, symbol, broker)
TTL timestamp + INTERVAL 5 YEAR DELETE
SETTINGS index_granularity = 8192;

-- Orders History table
CREATE TABLE IF NOT EXISTS orders_history (
    timestamp DateTime64(3) DEFAULT now64(),
    ticket String CODEC(ZSTD),
    symbol String CODEC(ZSTD),
    order_type LowCardinality(String),
    volume Float64 CODEC(Gorilla),
    price_open Float64 CODEC(Gorilla),
    price_sl Float64 CODEC(Gorilla),
    price_tp Float64 CODEC(Gorilla),
    time_setup DateTime64(3),
    comment String CODEC(ZSTD),
    magic UInt32 CODEC(T64),
    account_login String CODEC(ZSTD),
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_account account_login TYPE set(1000) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192,
    INDEX idx_time_setup time_setup TYPE minmax GRANULARITY 8192
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(time_setup)
ORDER BY (time_setup, account_login, symbol, broker)
TTL timestamp + INTERVAL 5 YEAR DELETE
SETTINGS index_granularity = 8192;

-- Symbols Info table
CREATE TABLE IF NOT EXISTS symbols_info (
    timestamp DateTime64(3) DEFAULT now64(),
    symbol String CODEC(ZSTD),
    description String CODEC(ZSTD),
    currency_base String CODEC(ZSTD),
    currency_profit String CODEC(ZSTD),
    currency_margin String CODEC(ZSTD),
    digits UInt8 CODEC(T64),
    point Float64 CODEC(Gorilla),
    spread UInt32 CODEC(T64),
    stops_level UInt32 CODEC(T64),
    freeze_level UInt32 CODEC(T64),
    trade_mode String CODEC(ZSTD),
    min_lot Float64 CODEC(Gorilla),
    max_lot Float64 CODEC(Gorilla),
    lot_step Float64 CODEC(Gorilla),
    tick_value Float64 CODEC(Gorilla),
    tick_size Float64 CODEC(Gorilla),
    contract_size Float64 CODEC(Gorilla),
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
) ENGINE = ReplacingMergeTree(timestamp)
PARTITION BY broker
ORDER BY (symbol, broker)
TTL timestamp + INTERVAL 1 YEAR DELETE
SETTINGS index_granularity = 8192;

-- Market Depth table (for advanced analysis)
CREATE TABLE IF NOT EXISTS market_depth (
    timestamp DateTime64(3) DEFAULT now64(),
    symbol String CODEC(ZSTD),
    level UInt8 CODEC(T64),
    bid_price Float64 CODEC(Gorilla),
    bid_volume Float64 CODEC(Gorilla),
    ask_price Float64 CODEC(Gorilla),
    ask_volume Float64 CODEC(Gorilla),
    order_flow_imbalance Float64 CODEC(Gorilla),
    volume_weighted_mid Float64 CODEC(Gorilla),
    effective_spread Float64 CODEC(Gorilla),
    price_impact Float64 CODEC(Gorilla),
    liquidity_score Float64 CODEC(Gorilla),
    depth_ratio Float64 CODEC(Gorilla),
    market_impact_cost Float64 CODEC(Gorilla),
    support_level Float64 CODEC(Gorilla),
    resistance_level Float64 CODEC(Gorilla),
    institutional_levels Array(Float64),
    primary_session LowCardinality(String) DEFAULT 'Unknown',
    broker LowCardinality(String) DEFAULT 'FBS-Demo',
    account_type LowCardinality(String) DEFAULT 'demo',
    INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
    INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
    INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192,
    INDEX idx_level level TYPE set(10) GRANULARITY 8192
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, symbol, broker, level)
TTL timestamp + INTERVAL 7 DAY DELETE
SETTINGS index_granularity = 8192;

-- Create materialized views for real-time aggregations
-- Minute-level OHLCV aggregation from ticks
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_minute_ohlcv
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp, broker)
AS SELECT
    toStartOfMinute(timestamp) as timestamp,
    symbol,
    broker,
    argMin(bid, timestamp) as open,
    max(bid) as high,
    min(bid) as low,
    argMax(bid, timestamp) as close,
    sum(volume) as volume,
    count() as tick_count,
    avg(spread) as avg_spread
FROM ticks
GROUP BY symbol, broker, toStartOfMinute(timestamp);

-- Daily statistics view
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_stats
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp, broker)
AS SELECT
    toStartOfDay(timestamp) as timestamp,
    symbol,
    broker,
    count() as total_ticks,
    min(bid) as daily_low,
    max(ask) as daily_high,
    argMin(bid, timestamp) as open_price,
    argMax(ask, timestamp) as close_price,
    sum(volume) as total_volume,
    avg(spread) as avg_spread,
    quantile(0.5)(spread) as median_spread
FROM ticks
GROUP BY symbol, broker, toStartOfDay(timestamp);

-- Log successful initialization
SELECT 'ClickHouse initialization completed successfully - Raw data tables created from existing schemas' as status;