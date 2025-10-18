-- ============================================================================
-- ClickHouse Schema: external_commodity_prices (Commodity Market Data)
-- ============================================================================
-- Purpose: Store commodity prices (Gold, Oil, etc.) for correlation analysis
-- Retention: 5 years (sufficient for pattern analysis)
-- Engine: MergeTree with partitioning by month
-- ============================================================================

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS suho_analytics.external_commodity_prices;

-- Create external_commodity_prices table
CREATE TABLE IF NOT EXISTS suho_analytics.external_commodity_prices (
    -- Price timestamp
    price_time DateTime64(3, 'UTC') NOT NULL,

    -- Commodity symbol (e.g., "GC=F" for Gold, "CL=F" for Crude Oil)
    symbol String NOT NULL,

    -- Commodity name (human-readable)
    commodity_name String NOT NULL,

    -- Current price
    price Decimal(18,5) NOT NULL,

    -- Currency denomination
    currency String NOT NULL,

    -- Daily change percentage
    change_pct Float64 NOT NULL,

    -- Trading volume (if available)
    volume UInt64 DEFAULT 0,

    -- Scraping metadata
    scraped_at DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(price_time)
ORDER BY (symbol, price_time)
TTL toDateTime(price_time) + INTERVAL 5 YEAR
SETTINGS index_granularity = 8192;

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Index for symbol filtering
ALTER TABLE suho_analytics.external_commodity_prices
ADD INDEX idx_symbol symbol TYPE set(0) GRANULARITY 1;

-- Index for price time range queries
ALTER TABLE suho_analytics.external_commodity_prices
ADD INDEX idx_price_time price_time TYPE minmax GRANULARITY 1;

-- ============================================================================
-- Materialized Views (Statistics)
-- ============================================================================

-- Latest price per commodity
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.commodity_prices_latest
ENGINE = ReplacingMergeTree(price_time)
ORDER BY symbol
AS SELECT
    symbol,
    commodity_name,
    price_time,
    price,
    currency,
    change_pct,
    volume
FROM suho_analytics.external_commodity_prices
ORDER BY price_time DESC;

-- Daily statistics per commodity
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.commodity_prices_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (symbol, day)
AS SELECT
    toDate(price_time) AS day,
    symbol,
    commodity_name,
    first_value(price) AS day_open,
    max(price) AS day_high,
    min(price) AS day_low,
    last_value(price) AS day_close,
    AVG(price) AS day_avg,
    stddevPop(price) AS day_volatility,
    SUM(volume) AS total_volume,
    COUNT(*) AS samples
FROM suho_analytics.external_commodity_prices
GROUP BY day, symbol, commodity_name;

-- ============================================================================
-- Verification Queries (Post-Deployment)
-- ============================================================================

-- Example query 1: Check latest prices for all commodities
-- SELECT
--     symbol,
--     commodity_name,
--     price,
--     currency,
--     change_pct,
--     price_time
-- FROM suho_analytics.commodity_prices_latest
-- ORDER BY symbol;

-- Example query 2: Gold price time series (last 30 days)
-- SELECT
--     price_time,
--     price,
--     change_pct
-- FROM suho_analytics.external_commodity_prices
-- WHERE symbol = 'GC=F'
--   AND price_time >= now() - INTERVAL 30 DAY
-- ORDER BY price_time;

-- Example query 3: Check data coverage per commodity
-- SELECT
--     symbol,
--     commodity_name,
--     COUNT(*) AS data_points,
--     MIN(price_time) AS oldest,
--     MAX(price_time) AS newest,
--     AVG(price) AS avg_price,
--     stddevPop(price) AS price_volatility
-- FROM suho_analytics.external_commodity_prices
-- GROUP BY symbol, commodity_name
-- ORDER BY symbol;

-- Example query 4: Gold vs Oil correlation (daily data)
-- SELECT
--     g.day,
--     g.day_close AS gold_price,
--     o.day_close AS oil_price,
--     corr(g.day_close, o.day_close) OVER (ORDER BY g.day ROWS BETWEEN 30 PRECEDING AND CURRENT ROW) AS rolling_30d_corr
-- FROM (
--     SELECT day, day_close
--     FROM suho_analytics.commodity_prices_daily
--     WHERE symbol = 'GC=F'
-- ) AS g
-- INNER JOIN (
--     SELECT day, day_close
--     FROM suho_analytics.commodity_prices_daily
--     WHERE symbol = 'CL=F'
-- ) AS o
-- ON g.day = o.day
-- ORDER BY g.day DESC
-- LIMIT 90;

-- ============================================================================
-- Schema Documentation
-- ============================================================================

COMMENT COLUMN suho_analytics.external_commodity_prices.price_time IS 'Commodity price timestamp';
COMMENT COLUMN suho_analytics.external_commodity_prices.symbol IS 'Yahoo Finance symbol (e.g., GC=F, CL=F)';
COMMENT COLUMN suho_analytics.external_commodity_prices.commodity_name IS 'Human-readable commodity name';
COMMENT COLUMN suho_analytics.external_commodity_prices.price IS 'Current market price';
COMMENT COLUMN suho_analytics.external_commodity_prices.currency IS 'Price denomination (USD, EUR, etc.)';
COMMENT COLUMN suho_analytics.external_commodity_prices.change_pct IS 'Daily price change percentage';
COMMENT COLUMN suho_analytics.external_commodity_prices.volume IS 'Trading volume';
COMMENT COLUMN suho_analytics.external_commodity_prices.scraped_at IS 'Data collection timestamp';

-- ============================================================================
-- Data Sources
-- ============================================================================
-- Source: Yahoo Finance API
-- Collector: external-data-collector → yahoo_finance_commodity.py
-- Transport: NATS/Kafka (external.commodity_prices)
-- Writer: data-bridge → clickhouse_writer.py
-- Update Frequency: Every 1 hour (3600s)
-- Coverage: Key commodities affecting forex markets
--
-- Tracked Commodities:
-- - GC=F: Gold Futures (safe-haven indicator)
-- - SI=F: Silver Futures
-- - CL=F: Crude Oil Futures (energy sector)
-- - NG=F: Natural Gas Futures
-- ============================================================================

-- ============================================================================
-- ML Features Use Cases
-- ============================================================================
-- 1. Risk-on/risk-off sentiment (Gold as safe-haven)
-- 2. USD correlation analysis (Gold vs USD typically inverse)
-- 3. Energy sector exposure (Oil prices affect CAD, NOK)
-- 4. Inflation expectations (Commodity basket trends)
-- 5. Cross-asset correlation (XAU/USD vs GC=F alignment verification)
-- 6. Market regime classification (commodity supercycles)
-- ============================================================================

-- ============================================================================
-- Migration Notes
-- ============================================================================
-- v1.8.0 (2025-10-18):
-- - Created new table for commodity correlation features
-- - Stores Yahoo Finance commodity data
-- - TTL: 5 years (sufficient for pattern learning)
-- - Partitioning: Monthly (hourly updates)
-- - Materialized views: Latest prices + daily OHLC
-- - Use cases: Risk sentiment, USD strength, inflation proxy
-- ============================================================================
