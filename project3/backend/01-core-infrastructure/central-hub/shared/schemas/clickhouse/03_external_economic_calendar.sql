-- =======================================================================
-- CLICKHOUSE EXTERNAL DATA - ECONOMIC CALENDAR
-- =======================================================================
-- Purpose: Economic events and news for fundamental analysis
-- Source: MQL5.com Economic Calendar
-- Data Flow: External Collector → NATS/Kafka → Data Bridge → ClickHouse
-- Update Frequency: Hourly
-- Retention: 2 years
-- =======================================================================

CREATE DATABASE IF NOT EXISTS suho_analytics;

USE suho_analytics;

-- =======================================================================
-- TABLE: external_economic_calendar
-- =======================================================================

CREATE TABLE IF NOT EXISTS external_economic_calendar (
    -- Event Information
    date Date,                            -- Event date
    time String,                          -- Event time (HH:MM format)
    currency String,                      -- Currency code: USD, EUR, GBP, etc.
    event String,                         -- Event name: "Non-Farm Payrolls", "CPI", etc.

    -- Event Values
    forecast Nullable(String),            -- Forecasted value
    previous Nullable(String),            -- Previous value
    actual Nullable(String),              -- Actual value (after release)

    -- Impact Assessment
    impact String,                        -- low, medium, high

    -- Metadata
    source String DEFAULT 'mql5',         -- Data source
    collected_at DateTime DEFAULT now()  -- Collection timestamp

) ENGINE = MergeTree()
ORDER BY (date, time, currency)
TTL toDateTime(date) + INTERVAL 730 DAY  -- 2 years retention
SETTINGS index_granularity = 8192;

-- =======================================================================
-- INDEXES
-- =======================================================================

-- High impact events index
CREATE INDEX IF NOT EXISTS idx_economic_high_impact
ON external_economic_calendar (impact, date)
WHERE impact = 'high';

-- Currency index
CREATE INDEX IF NOT EXISTS idx_economic_currency
ON external_economic_calendar (currency) TYPE set(0);

-- Date range index
CREATE INDEX IF NOT EXISTS idx_economic_date
ON external_economic_calendar (date) TYPE minmax;

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get high impact USD events for next 7 days
-- SELECT * FROM external_economic_calendar
-- WHERE currency = 'USD'
--   AND impact = 'high'
--   AND date >= today()
--   AND date <= today() + INTERVAL 7 DAY
-- ORDER BY date, time;

-- Count events by impact level
-- SELECT impact, count() as event_count
-- FROM external_economic_calendar
-- WHERE date >= today() - INTERVAL 30 DAY
-- GROUP BY impact
-- ORDER BY event_count DESC;
