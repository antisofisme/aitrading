-- =======================================================================
-- CLICKHOUSE EXTERNAL DATA - FEAR & GREED INDEX
-- =======================================================================
-- Purpose: Crypto market fear & greed index (0-100 sentiment indicator)
-- Source: Alternative.me
-- Data Flow: External Collector → NATS/Kafka → Data Bridge → ClickHouse
-- Update Frequency: Hourly
-- Retention: 2 years
-- =======================================================================

CREATE DATABASE IF NOT EXISTS suho_analytics;

USE suho_analytics;

-- =======================================================================
-- TABLE: external_fear_greed_index
-- =======================================================================

CREATE TABLE IF NOT EXISTS external_fear_greed_index (
    -- Fear & Greed Metrics
    value UInt8,                          -- 0-100 (0=Extreme Fear, 100=Extreme Greed)
    classification String,                -- Extreme Fear, Fear, Neutral, Greed, Extreme Greed
    sentiment_score Float64,              -- Normalized sentiment score

    -- Timestamp
    index_timestamp DateTime,             -- Index timestamp from source

    -- Metadata
    source String DEFAULT 'alternative.me', -- Data source
    collected_at DateTime DEFAULT now()  -- Collection timestamp

) ENGINE = MergeTree()
ORDER BY index_timestamp
TTL index_timestamp + INTERVAL 730 DAY  -- 2 years retention
SETTINGS index_granularity = 8192;

-- =======================================================================
-- INDEXES
-- =======================================================================

-- Timestamp index
CREATE INDEX IF NOT EXISTS idx_fear_greed_time
ON external_fear_greed_index (index_timestamp) TYPE minmax;

-- Value index (for filtering by sentiment level)
CREATE INDEX IF NOT EXISTS idx_fear_greed_value
ON external_fear_greed_index (value) TYPE minmax;

-- Classification index
CREATE INDEX IF NOT EXISTS idx_fear_greed_class
ON external_fear_greed_index (classification) TYPE set(0);

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get latest fear & greed index
-- SELECT value, classification, sentiment_score, index_timestamp
-- FROM external_fear_greed_index
-- ORDER BY index_timestamp DESC
-- LIMIT 1;

-- Fear & greed trend (last 30 days)
-- SELECT index_timestamp, value, classification
-- FROM external_fear_greed_index
-- WHERE index_timestamp >= now() - INTERVAL 30 DAY
-- ORDER BY index_timestamp;

-- Count days by sentiment classification
-- SELECT classification, count() as days
-- FROM external_fear_greed_index
-- WHERE index_timestamp >= now() - INTERVAL 90 DAY
-- GROUP BY classification
-- ORDER BY days DESC;

-- Extreme fear periods (value < 25)
-- SELECT index_timestamp, value, classification
-- FROM external_fear_greed_index
-- WHERE value < 25
--   AND index_timestamp >= now() - INTERVAL 180 DAY
-- ORDER BY value ASC;
