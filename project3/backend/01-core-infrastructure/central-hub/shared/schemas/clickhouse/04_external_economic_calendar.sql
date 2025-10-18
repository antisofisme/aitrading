-- ============================================================================
-- ClickHouse Schema: external_economic_calendar (Economic Events)
-- ============================================================================
-- Purpose: Store economic calendar events from MQL5 for fundamental analysis
-- Retention: 5 years (sufficient for pattern analysis)
-- Engine: MergeTree with partitioning by month
-- ============================================================================

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS suho_analytics.external_economic_calendar;

-- Create external_economic_calendar table
CREATE TABLE IF NOT EXISTS suho_analytics.external_economic_calendar (
    -- Event timestamp (when the economic data is released)
    event_time DateTime64(3, 'UTC') NOT NULL,

    -- Currency affected (e.g., USD, EUR, GBP)
    currency String NOT NULL,

    -- Event name (e.g., "Non-Farm Payrolls", "CPI", "Interest Rate Decision")
    event_name String NOT NULL,

    -- Impact level (high = major market mover, medium = moderate, low = minor)
    impact Enum8('low' = 1, 'medium' = 2, 'high' = 3) NOT NULL,

    -- Forecast value (expected by analysts)
    forecast Nullable(String),

    -- Previous value (last reported value)
    previous Nullable(String),

    -- Actual value (real reported value)
    actual Nullable(String),

    -- Scraping metadata
    scraped_at DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, currency, event_name)
TTL toDateTime(event_time) + INTERVAL 5 YEAR
SETTINGS index_granularity = 8192;

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Index for currency filtering
ALTER TABLE suho_analytics.external_economic_calendar
ADD INDEX idx_currency currency TYPE set(0) GRANULARITY 1;

-- Index for impact level filtering
ALTER TABLE suho_analytics.external_economic_calendar
ADD INDEX idx_impact impact TYPE set(0) GRANULARITY 1;

-- Index for event time range queries
ALTER TABLE suho_analytics.external_economic_calendar
ADD INDEX idx_event_time event_time TYPE minmax GRANULARITY 1;

-- ============================================================================
-- Materialized Views (Statistics)
-- ============================================================================

-- High-impact events per currency (monthly aggregation)
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.economic_calendar_high_impact_monthly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(month)
ORDER BY (currency, month)
AS SELECT
    toStartOfMonth(event_time) AS month,
    currency,
    COUNT(*) AS high_impact_events,
    uniqExact(event_name) AS unique_events
FROM suho_analytics.external_economic_calendar
WHERE impact = 'high'
GROUP BY month, currency;

-- Event frequency per event type
CREATE MATERIALIZED VIEW IF NOT EXISTS suho_analytics.economic_calendar_event_types
ENGINE = SummingMergeTree()
PARTITION BY toYear(year)
ORDER BY (event_name, year)
AS SELECT
    toYear(event_time) AS year,
    event_name,
    currency,
    COUNT(*) AS event_count,
    countIf(impact = 'high') AS high_impact_count,
    countIf(actual IS NOT NULL) AS events_with_actual
FROM suho_analytics.external_economic_calendar
GROUP BY year, event_name, currency;

-- ============================================================================
-- Verification Queries (Post-Deployment)
-- ============================================================================

-- Example query 1: Check upcoming high-impact events
-- SELECT
--     event_time,
--     currency,
--     event_name,
--     impact,
--     forecast,
--     previous,
--     actual
-- FROM suho_analytics.external_economic_calendar
-- WHERE event_time >= now()
--   AND event_time < now() + INTERVAL 7 DAY
--   AND impact = 'high'
-- ORDER BY event_time;

-- Example query 2: Check event coverage per currency
-- SELECT
--     currency,
--     COUNT(*) AS total_events,
--     countIf(impact = 'high') AS high_impact,
--     countIf(impact = 'medium') AS medium_impact,
--     countIf(impact = 'low') AS low_impact,
--     MIN(event_time) AS oldest_event,
--     MAX(event_time) AS newest_event
-- FROM suho_analytics.external_economic_calendar
-- GROUP BY currency
-- ORDER BY total_events DESC;

-- Example query 3: Check actual vs forecast deviation for NFP
-- SELECT
--     event_time,
--     currency,
--     forecast,
--     actual,
--     (toFloat64OrNull(actual) - toFloat64OrNull(forecast)) AS deviation
-- FROM suho_analytics.external_economic_calendar
-- WHERE event_name LIKE '%Non-Farm%'
--   AND actual IS NOT NULL
--   AND forecast IS NOT NULL
-- ORDER BY event_time DESC
-- LIMIT 20;

-- ============================================================================
-- Schema Documentation
-- ============================================================================

COMMENT COLUMN suho_analytics.external_economic_calendar.event_time IS 'Economic event release timestamp';
COMMENT COLUMN suho_analytics.external_economic_calendar.currency IS 'Affected currency (USD, EUR, GBP, etc.)';
COMMENT COLUMN suho_analytics.external_economic_calendar.event_name IS 'Economic indicator name';
COMMENT COLUMN suho_analytics.external_economic_calendar.impact IS 'Market impact level (high/medium/low)';
COMMENT COLUMN suho_analytics.external_economic_calendar.forecast IS 'Analyst forecast value';
COMMENT COLUMN suho_analytics.external_economic_calendar.previous IS 'Previous reported value';
COMMENT COLUMN suho_analytics.external_economic_calendar.actual IS 'Actual reported value';
COMMENT COLUMN suho_analytics.external_economic_calendar.scraped_at IS 'Data collection timestamp';

-- ============================================================================
-- Data Sources
-- ============================================================================
-- Source: MQL5 Economic Calendar (https://www.mql5.com/en/economic-calendar)
-- Collector: external-data-collector → mql5_historical_scraper.py
-- Transport: NATS/Kafka (external.economic_calendar)
-- Writer: data-bridge → clickhouse_writer.py
-- Update Frequency: Every 6 hours (21600s)
-- Backfill: 12 months historical data
-- Coverage: Major currencies (USD, EUR, GBP, JPY, AUD, CAD, CHF, NZD)
-- ============================================================================

-- ============================================================================
-- ML Features Use Cases
-- ============================================================================
-- 1. Pre-event volatility spike detection (1-2 hours before high-impact events)
-- 2. Post-event price movement correlation (actual vs forecast deviation)
-- 3. Currency strength index (number of positive economic surprises)
-- 4. Risk-on/risk-off regime classification
-- 5. Trading session activity prediction (London/NY overlaps with event times)
-- ============================================================================

-- ============================================================================
-- Migration Notes
-- ============================================================================
-- v1.8.0 (2025-10-18):
-- - Created new table for fundamental analysis features
-- - Impact stored as Enum8 for efficient filtering
-- - Forecast/previous/actual stored as String (handles various formats)
-- - TTL: 5 years (sufficient for pattern learning)
-- - Partitioning: Monthly (aligns with economic reporting cycles)
-- ============================================================================
