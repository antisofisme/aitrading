-- =======================================================================
-- CLICKHOUSE EXTERNAL DATA - FRED ECONOMIC INDICATORS
-- =======================================================================
-- Purpose: Economic indicators from Federal Reserve Economic Data
-- Source: FRED (St. Louis Federal Reserve)
-- Data Flow: External Collector → NATS/Kafka → Data Bridge → ClickHouse
-- Update Frequency: Every 4 hours
-- Retention: 5 years
-- =======================================================================

CREATE DATABASE IF NOT EXISTS suho_analytics;

USE suho_analytics;

-- =======================================================================
-- TABLE: external_fred_economic
-- =======================================================================

CREATE TABLE IF NOT EXISTS external_fred_economic (
    -- Indicator Information
    series_id String,                     -- GDP, UNRATE, CPIAUCSL, DFF, DGS10, etc.
    value Float64,                        -- Indicator value
    observation_date Date,                -- Observation date

    -- Metadata
    source String DEFAULT 'fred',         -- Data source
    collected_at DateTime DEFAULT now()  -- Collection timestamp

) ENGINE = MergeTree()
ORDER BY (series_id, observation_date)
TTL toDateTime(observation_date) + INTERVAL 1825 DAY  -- 5 years retention
SETTINGS index_granularity = 8192;

-- =======================================================================
-- INDEXES
-- =======================================================================

-- Series ID index
CREATE INDEX IF NOT EXISTS idx_fred_series
ON external_fred_economic (series_id) TYPE set(0);

-- Date range index
CREATE INDEX IF NOT EXISTS idx_fred_date
ON external_fred_economic (observation_date) TYPE minmax;

-- =======================================================================
-- MATERIALIZED VIEW - Latest Values
-- =======================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS fred_latest_values
ENGINE = ReplacingMergeTree(collected_at)
ORDER BY series_id
AS SELECT
    series_id,
    value,
    observation_date,
    collected_at
FROM external_fred_economic
ORDER BY observation_date DESC;

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get latest GDP value
-- SELECT series_id, value, observation_date
-- FROM external_fred_economic
-- WHERE series_id = 'GDP'
-- ORDER BY observation_date DESC
-- LIMIT 1;

-- Get all indicators latest values
-- SELECT series_id, value, observation_date
-- FROM fred_latest_values
-- FINAL
-- ORDER BY series_id;

-- GDP trend (last 12 months)
-- SELECT observation_date, value
-- FROM external_fred_economic
-- WHERE series_id = 'GDP'
--   AND observation_date >= today() - INTERVAL 365 DAY
-- ORDER BY observation_date;
