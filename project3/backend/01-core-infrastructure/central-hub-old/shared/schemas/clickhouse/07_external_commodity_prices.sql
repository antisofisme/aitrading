-- =======================================================================
-- CLICKHOUSE EXTERNAL DATA - COMMODITY PRICES
-- =======================================================================
-- Purpose: Commodity prices (Gold, Oil, Silver, Copper, Natural Gas)
-- Source: Yahoo Finance
-- Data Flow: External Collector → NATS/Kafka → Data Bridge → ClickHouse
-- Update Frequency: Every 30 minutes
-- Retention: 2 years
-- =======================================================================

CREATE DATABASE IF NOT EXISTS suho_analytics;

USE suho_analytics;

-- =======================================================================
-- TABLE: external_commodity_prices
-- =======================================================================

CREATE TABLE IF NOT EXISTS external_commodity_prices (
    -- Commodity Information
    symbol String,                        -- GC=F (Gold), CL=F (Oil), SI=F (Silver), etc.
    name String,                          -- Gold, Crude Oil, Silver, etc.
    currency String,                      -- USD, EUR, etc.

    -- Price Data
    price Float64,                        -- Current price
    previous_close Float64,               -- Previous close price
    change Float64,                       -- Price change
    change_percent Float64,               -- Price change percentage

    -- Volume
    volume UInt64,                        -- Trading volume

    -- Metadata
    source String DEFAULT 'yahoo',        -- Data source
    collected_at DateTime DEFAULT now()  -- Collection timestamp

) ENGINE = MergeTree()
ORDER BY (symbol, collected_at)
TTL collected_at + INTERVAL 730 DAY  -- 2 years retention
SETTINGS index_granularity = 8192;

-- =======================================================================
-- INDEXES
-- =======================================================================

-- Symbol index
CREATE INDEX IF NOT EXISTS idx_commodity_symbol
ON external_commodity_prices (symbol) TYPE set(0);

-- Timestamp index
CREATE INDEX IF NOT EXISTS idx_commodity_time
ON external_commodity_prices (collected_at) TYPE minmax;

-- Price change index (for filtering big movers)
CREATE INDEX IF NOT EXISTS idx_commodity_change
ON external_commodity_prices (change_percent) TYPE minmax;

-- =======================================================================
-- MATERIALIZED VIEW - Latest Prices
-- =======================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS commodity_latest_prices
ENGINE = ReplacingMergeTree(collected_at)
ORDER BY symbol
AS SELECT
    symbol,
    name,
    price,
    previous_close,
    change,
    change_percent,
    collected_at
FROM external_commodity_prices
ORDER BY collected_at DESC;

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get latest Gold price
-- SELECT symbol, name, price, change_percent, collected_at
-- FROM external_commodity_prices
-- WHERE symbol = 'GC=F'
-- ORDER BY collected_at DESC
-- LIMIT 1;

-- All commodities latest prices
-- SELECT symbol, name, price, change_percent
-- FROM commodity_latest_prices
-- FINAL
-- ORDER BY symbol;

-- Gold price trend (last 24 hours)
-- SELECT collected_at, price, change_percent
-- FROM external_commodity_prices
-- WHERE symbol = 'GC=F'
--   AND collected_at >= now() - INTERVAL 24 HOUR
-- ORDER BY collected_at;

-- Top movers (biggest % change in last hour)
-- SELECT symbol, name, price, change_percent
-- FROM external_commodity_prices
-- WHERE collected_at >= now() - INTERVAL 1 HOUR
-- ORDER BY abs(change_percent) DESC
-- LIMIT 5;

-- Gold/Oil ratio calculation
-- SELECT
--     g.collected_at,
--     g.price as gold_price,
--     o.price as oil_price,
--     round(g.price / o.price, 2) as gold_oil_ratio
-- FROM external_commodity_prices g
-- INNER JOIN external_commodity_prices o
--     ON toStartOfHour(g.collected_at) = toStartOfHour(o.collected_at)
-- WHERE g.symbol = 'GC=F'
--   AND o.symbol = 'CL=F'
--   AND g.collected_at >= now() - INTERVAL 7 DAY
-- ORDER BY g.collected_at DESC;
