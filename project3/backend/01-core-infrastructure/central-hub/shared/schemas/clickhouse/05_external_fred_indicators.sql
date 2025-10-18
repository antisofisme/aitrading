-- ============================================================================
-- ClickHouse Schema: external_fred_indicators (FRED Economic Data)
-- ============================================================================
-- Purpose: Store FRED economic indicators for macro-economic analysis
-- Retention: 10 years (long-term economic data)
-- Engine: MergeTree with partitioning by year
-- ============================================================================

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS suho_analytics.external_fred_indicators;

-- Create external_fred_indicators table
CREATE TABLE IF NOT EXISTS suho_analytics.external_fred_indicators (
    -- Release timestamp (when the data point was published)
    release_time DateTime64(3, 'UTC') NOT NULL,

    -- FRED series ID (e.g., "GDP", "UNRATE", "CPIAUCSL")
    series_id String NOT NULL,

    -- Series name (human-readable description)
    series_name String NOT NULL,

    -- Indicator value
    value Float64 NOT NULL,

    -- Unit of measurement (e.g., "Billions of Dollars", "Percent", "Index")
    unit String NOT NULL,

    -- Scraping metadata
    scraped_at DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYear(release_time)
ORDER BY (series_id, release_time)
TTL toDateTime(release_time) + INTERVAL 10 YEAR
SETTINGS index_granularity = 8192;

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Index for series_id filtering (most common query pattern)
ALTER TABLE suho_analytics.external_fred_indicators
ADD INDEX idx_series_id series_id TYPE set(0) GRANULARITY 1;

-- Index for release time range queries
ALTER TABLE suho_analytics.external_fred_indicators
ADD INDEX idx_release_time release_time TYPE minmax GRANULARITY 1;

-- ============================================================================
-- Materialized Views (Statistics)
-- ============================================================================

-- Latest value per indicator
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.fred_indicators_latest
ENGINE = ReplacingMergeTree(release_time)
ORDER BY series_id
AS SELECT
    series_id,
    series_name,
    release_time,
    value,
    unit
FROM suho_analytics.external_fred_indicators
ORDER BY release_time DESC;

-- Quarterly aggregates per indicator
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.fred_indicators_quarterly
ENGINE = SummingMergeTree()
PARTITION BY toYear(quarter)
ORDER BY (series_id, quarter)
AS SELECT
    toStartOfQuarter(release_time) AS quarter,
    series_id,
    series_name,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    stddevPop(value) AS volatility,
    COUNT(*) AS data_points
FROM suho_analytics.external_fred_indicators
GROUP BY quarter, series_id, series_name;

-- ============================================================================
-- Verification Queries (Post-Deployment)
-- ============================================================================

-- Example query 1: Check latest values for all indicators
-- SELECT
--     series_id,
--     series_name,
--     value,
--     unit,
--     release_time
-- FROM suho_analytics.fred_indicators_latest
-- ORDER BY series_id;

-- Example query 2: GDP time series (last 5 years)
-- SELECT
--     release_time,
--     value,
--     unit
-- FROM suho_analytics.external_fred_indicators
-- WHERE series_id = 'GDP'
--   AND release_time >= now() - INTERVAL 5 YEAR
-- ORDER BY release_time;

-- Example query 3: Check data coverage per indicator
-- SELECT
--     series_id,
--     series_name,
--     COUNT(*) AS data_points,
--     MIN(release_time) AS oldest,
--     MAX(release_time) AS newest,
--     dateDiff('day', MIN(release_time), MAX(release_time)) AS days_span
-- FROM suho_analytics.external_fred_indicators
-- GROUP BY series_id, series_name
-- ORDER BY series_id;

-- Example query 4: Correlation matrix (GDP vs Unemployment)
-- SELECT
--     g.release_time,
--     g.value AS gdp,
--     u.value AS unemployment
-- FROM (
--     SELECT release_time, value
--     FROM suho_analytics.external_fred_indicators
--     WHERE series_id = 'GDP'
-- ) AS g
-- INNER JOIN (
--     SELECT release_time, value
--     FROM suho_analytics.external_fred_indicators
--     WHERE series_id = 'UNRATE'
-- ) AS u
-- ON g.release_time = u.release_time
-- ORDER BY g.release_time DESC
-- LIMIT 100;

-- ============================================================================
-- Schema Documentation
-- ============================================================================

COMMENT COLUMN suho_analytics.external_fred_indicators.release_time IS 'Economic data release timestamp';
COMMENT COLUMN suho_analytics.external_fred_indicators.series_id IS 'FRED series identifier (e.g., GDP, UNRATE)';
COMMENT COLUMN suho_analytics.external_fred_indicators.series_name IS 'Human-readable series name';
COMMENT COLUMN suho_analytics.external_fred_indicators.value IS 'Indicator value';
COMMENT COLUMN suho_analytics.external_fred_indicators.unit IS 'Unit of measurement';
COMMENT COLUMN suho_analytics.external_fred_indicators.scraped_at IS 'Data collection timestamp';

-- ============================================================================
-- Data Sources
-- ============================================================================
-- Source: FRED (Federal Reserve Economic Data) API
-- Collector: external-data-collector → fred_economic.py
-- Transport: NATS/Kafka (external.fred_indicators)
-- Writer: data-bridge → clickhouse_writer.py
-- Update Frequency: Every 6 hours (21600s)
-- Coverage: Key US economic indicators
--
-- Tracked Indicators:
-- - GDP: Gross Domestic Product
-- - UNRATE: Unemployment Rate
-- - CPIAUCSL: Consumer Price Index (All Urban Consumers)
-- - FEDFUNDS: Federal Funds Rate
-- - DGS10: 10-Year Treasury Constant Maturity Rate
-- - DEXUSEU: USD/EUR Exchange Rate
-- ============================================================================

-- ============================================================================
-- ML Features Use Cases
-- ============================================================================
-- 1. Macro regime classification (recession vs expansion)
-- 2. USD strength prediction (correlation with interest rates)
-- 3. Risk-on/risk-off sentiment (flight to safety indicators)
-- 4. Inflation expectations (CPI trends)
-- 5. Central bank policy prediction (FEDFUNDS trajectory)
-- 6. Cross-asset correlation (bonds vs forex)
-- ============================================================================

-- ============================================================================
-- Migration Notes
-- ============================================================================
-- v1.8.0 (2025-10-18):
-- - Created new table for macro-economic features
-- - Stores FRED API data points
-- - TTL: 10 years (long-term economic analysis)
-- - Partitioning: Yearly (economic data updated infrequently)
-- - Materialized views: Latest values + quarterly aggregates
-- ============================================================================
