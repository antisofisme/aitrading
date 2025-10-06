-- =======================================================================
-- TIMESCALEDB MARKET CONTEXT SCHEMA (Economic Calendar & Sentiment)
-- =======================================================================
-- Purpose: Store low-frequency contextual data for ML enrichment
-- Source: External Data Collector (Economic Calendar, Sentiment, etc.)
-- Data Flow: Scrapers → Transform → PostgreSQL/TimescaleDB
-- Retention: 5 years (for long-term correlation analysis)
-- Version: 1.0.0
-- Last Updated: 2025-10-06
-- =======================================================================

-- Connect to database
\c suho_trading;

-- Set search path
SET search_path TO public;

-- =======================================================================
-- TABLE: market_context (Economic Events & Sentiment)
-- =======================================================================
-- Stores economic calendar events, sentiment data, and other contextual info
-- Used for ML feature enrichment and fundamental analysis

CREATE TABLE IF NOT EXISTS market_context (
    -- ===========================================
    -- PRIMARY KEY
    -- ===========================================
    id BIGSERIAL PRIMARY KEY,

    -- ===========================================
    -- IDENTIFIERS
    -- ===========================================
    event_id VARCHAR(100) UNIQUE NOT NULL,  -- Generated: {currency}_{event_slug}_{date}
    external_id VARCHAR(100),               -- External system ID (MQL5, FRED, etc.)
    tenant_id VARCHAR(50) DEFAULT 'global', -- Multi-tenant support

    -- ===========================================
    -- CLASSIFICATION
    -- ===========================================
    data_type VARCHAR(30) NOT NULL,         -- 'economic_calendar', 'sentiment', 'news', 'correlation'
    symbol VARCHAR(50) NOT NULL,            -- Event name or indicator (e.g., "Non-Farm Payrolls")
    category VARCHAR(50),                   -- 'employment', 'inflation', 'gdp', 'interest_rate', 'sentiment'

    -- ===========================================
    -- TIME FIELDS
    -- ===========================================
    time TIMESTAMPTZ NOT NULL,              -- Event time (for TimescaleDB hypertable)
    timestamp BIGINT NOT NULL,              -- Unix milliseconds (original format)
    time_status VARCHAR(20),                -- 'historical', 'scheduled', 'future', 'missed_data'

    event_date TIMESTAMP,                   -- Scheduled event date
    release_date TIMESTAMP,                 -- Actual release date (when data was published)

    -- ===========================================
    -- VALUES (Numeric & Text)
    -- ===========================================
    value DECIMAL(20,8),                    -- Primary numeric value (parsed)
    value_text VARCHAR(100),                -- Text representation

    -- Economic Event Values
    actual_value DECIMAL(20,8),             -- Actual reported value
    forecast_value DECIMAL(20,8),           -- Market forecast/consensus
    previous_value DECIMAL(20,8),           -- Previous period value

    -- ===========================================
    -- METADATA
    -- ===========================================
    importance VARCHAR(20),                 -- 'high', 'medium', 'low'
    frequency VARCHAR(20),                  -- 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    units VARCHAR(50),                      -- 'K', 'M', 'B', '%', 'index'

    -- ===========================================
    -- MARKET IMPACT ANALYSIS
    -- ===========================================
    currency_impact TEXT[],                 -- Affected currencies: ['USD', 'EUR']
    forex_impact VARCHAR(30),               -- 'bullish', 'bearish', 'neutral'
    market_impact_score DECIMAL(3,2),       -- 0.0-1.0 (surprise magnitude)

    -- Calculated: |actual - forecast| / |forecast|
    surprise_index DECIMAL(6,4),            -- Positive surprise = actual > forecast

    -- ===========================================
    -- SOURCE & RELIABILITY
    -- ===========================================
    source VARCHAR(50) NOT NULL,            -- 'mql5', 'fred', 'coingecko', 'tradingview'
    reliability VARCHAR(20) DEFAULT 'high', -- 'high', 'medium', 'low'

    -- ===========================================
    -- RAW DATA STORAGE
    -- ===========================================
    metadata JSONB,                         -- Full original event/data (for debugging)

    -- ===========================================
    -- TIMESTAMPS
    -- ===========================================
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =======================================================================
-- CONVERT TO HYPERTABLE
-- =======================================================================

SELECT create_hypertable(
    'market_context',
    'time',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

-- =======================================================================
-- INDEXES
-- =======================================================================

-- Data type + time (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_market_context_type_time
ON market_context (data_type, time DESC);

-- Symbol + time (for event-specific queries)
CREATE INDEX IF NOT EXISTS idx_market_context_symbol_time
ON market_context (symbol, time DESC);

-- Category + time (for thematic analysis)
CREATE INDEX IF NOT EXISTS idx_market_context_category_time
ON market_context (category, time DESC);

-- Importance + time (high-impact events only)
CREATE INDEX IF NOT EXISTS idx_market_context_importance_time
ON market_context (importance, time DESC)
WHERE importance = 'high';

-- Currency impact (for currency-specific queries)
CREATE INDEX IF NOT EXISTS idx_market_context_currency_impact
ON market_context USING GIN (currency_impact);

-- Event ID (for deduplication)
CREATE UNIQUE INDEX IF NOT EXISTS idx_market_context_event_id
ON market_context (event_id);

-- Compound: event_id + symbol + event_date (strict deduplication)
CREATE UNIQUE INDEX IF NOT EXISTS idx_market_context_dedup
ON market_context (event_id, symbol, event_date);

-- Source index
CREATE INDEX IF NOT EXISTS idx_market_context_source
ON market_context (source, time DESC);

-- =======================================================================
-- COMPRESSION
-- =======================================================================

ALTER TABLE market_context SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tenant_id, data_type, category',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('market_context', INTERVAL '90 days');

-- =======================================================================
-- RETENTION POLICY
-- =======================================================================
-- Keep 5 years of economic data for long-term correlation analysis

SELECT add_retention_policy('market_context', INTERVAL '1825 days');

-- =======================================================================
-- CONTINUOUS AGGREGATES
-- =======================================================================

-- Daily economic events summary
CREATE MATERIALIZED VIEW IF NOT EXISTS market_context_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    data_type,
    category,
    COUNT(*) as event_count,
    COUNT(*) FILTER (WHERE importance = 'high') as high_impact_count,
    AVG(market_impact_score) as avg_impact_score,
    ARRAY_AGG(DISTINCT symbol) as events
FROM market_context
GROUP BY day, data_type, category;

SELECT add_continuous_aggregate_policy('market_context_daily',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);

-- =======================================================================
-- TRIGGERS
-- =======================================================================

-- Auto-calculate surprise_index on insert/update
CREATE OR REPLACE FUNCTION calculate_surprise_index()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.actual_value IS NOT NULL AND NEW.forecast_value IS NOT NULL AND NEW.forecast_value <> 0 THEN
        NEW.surprise_index := (NEW.actual_value - NEW.forecast_value) / ABS(NEW.forecast_value);
    ELSE
        NEW.surprise_index := NULL;
    END IF;

    -- Update market_impact_score if not set
    IF NEW.market_impact_score IS NULL AND NEW.surprise_index IS NOT NULL THEN
        NEW.market_impact_score := LEAST(ABS(NEW.surprise_index) * 2.0, 1.0);
    END IF;

    -- Set updated_at
    NEW.updated_at := NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_surprise
BEFORE INSERT OR UPDATE ON market_context
FOR EACH ROW
EXECUTE FUNCTION calculate_surprise_index();

-- =======================================================================
-- FUNCTIONS
-- =======================================================================

-- Get upcoming high-impact events for a currency
CREATE OR REPLACE FUNCTION get_upcoming_events(
    target_currency VARCHAR,
    hours_ahead INT DEFAULT 24
)
RETURNS TABLE (
    event_time TIMESTAMPTZ,
    event_name VARCHAR,
    importance VARCHAR,
    forecast DECIMAL,
    previous DECIMAL,
    currencies TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        mc.time as event_time,
        mc.symbol as event_name,
        mc.importance,
        mc.forecast_value as forecast,
        mc.previous_value as previous,
        mc.currency_impact as currencies
    FROM market_context mc
    WHERE target_currency = ANY(mc.currency_impact)
      AND mc.time > NOW()
      AND mc.time <= NOW() + (hours_ahead || ' hours')::INTERVAL
      AND mc.data_type = 'economic_calendar'
      AND mc.importance IN ('high', 'medium')
    ORDER BY mc.time ASC;
END;
$$ LANGUAGE plpgsql;

-- Check if major event is near (within X minutes)
CREATE OR REPLACE FUNCTION has_major_event_nearby(
    target_time TIMESTAMPTZ,
    window_minutes INT DEFAULT 30
)
RETURNS BOOLEAN AS $$
DECLARE
    event_count INT;
BEGIN
    SELECT COUNT(*) INTO event_count
    FROM market_context
    WHERE data_type = 'economic_calendar'
      AND importance = 'high'
      AND time BETWEEN (target_time - (window_minutes || ' minutes')::INTERVAL)
                   AND (target_time + (window_minutes || ' minutes')::INTERVAL);

    RETURN event_count > 0;
END;
$$ LANGUAGE plpgsql;

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get all high-impact USD events in next 24 hours
-- SELECT * FROM get_upcoming_events('USD', 24);

-- Check if major event is near current time
-- SELECT has_major_event_nearby(NOW(), 30);

-- Get recent Non-Farm Payrolls data
-- SELECT
--     time,
--     actual_value,
--     forecast_value,
--     previous_value,
--     surprise_index,
--     market_impact_score
-- FROM market_context
-- WHERE symbol = 'Non-Farm Payrolls'
--   AND data_type = 'economic_calendar'
-- ORDER BY time DESC
-- LIMIT 12;  -- Last year (monthly)

-- Analyze surprise impact on market
-- SELECT
--     symbol,
--     AVG(surprise_index) as avg_surprise,
--     STDDEV(surprise_index) as surprise_volatility,
--     COUNT(*) as event_count
-- FROM market_context
-- WHERE data_type = 'economic_calendar'
--   AND importance = 'high'
--   AND time >= NOW() - INTERVAL '1 year'
-- GROUP BY symbol
-- ORDER BY surprise_volatility DESC;

-- Get economic calendar for specific date
-- SELECT
--     time,
--     symbol,
--     category,
--     importance,
--     forecast_value,
--     previous_value,
--     currency_impact
-- FROM market_context
-- WHERE data_type = 'economic_calendar'
--   AND DATE(time) = '2024-01-26'
-- ORDER BY time;

-- Count events by category
-- SELECT
--     category,
--     importance,
--     COUNT(*) as event_count
-- FROM market_context
-- WHERE data_type = 'economic_calendar'
--   AND time >= NOW() - INTERVAL '30 days'
-- GROUP BY category, importance
-- ORDER BY category, importance;

-- Find biggest surprises (outliers)
-- SELECT
--     time,
--     symbol,
--     actual_value,
--     forecast_value,
--     surprise_index,
--     market_impact_score
-- FROM market_context
-- WHERE data_type = 'economic_calendar'
--   AND ABS(surprise_index) > 0.5  -- More than 50% deviation
-- ORDER BY ABS(surprise_index) DESC
-- LIMIT 20;

-- =======================================================================
-- GRANTS
-- =======================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON market_context TO suho_service;
GRANT SELECT ON market_context TO suho_readonly;

GRANT SELECT ON market_context_daily TO suho_service;
GRANT SELECT ON market_context_daily TO suho_readonly;

GRANT EXECUTE ON FUNCTION get_upcoming_events(VARCHAR, INT) TO suho_service;
GRANT EXECUTE ON FUNCTION get_upcoming_events(VARCHAR, INT) TO suho_readonly;
GRANT EXECUTE ON FUNCTION has_major_event_nearby(TIMESTAMPTZ, INT) TO suho_service;
GRANT EXECUTE ON FUNCTION has_major_event_nearby(TIMESTAMPTZ, INT) TO suho_readonly;

-- =======================================================================
-- NOTES
-- =======================================================================
-- 1. Retention: 5 years for long-term analysis
-- 2. Compression: After 90 days to save storage
-- 3. Deduplication: event_id prevents duplicate events
-- 4. Surprise index: Auto-calculated (actual - forecast) / forecast
-- 5. Market impact: 0-1 score based on surprise magnitude
-- 6. Currency impact: Array for multi-currency events
-- 7. JSONB metadata: Stores full original event for debugging
-- 8. Helper functions: get_upcoming_events(), has_major_event_nearby()
-- 9. Data types: 'economic_calendar', 'sentiment', 'news', 'correlation'
-- 10. Categories: 'employment', 'inflation', 'gdp', 'interest_rate', etc.
-- =======================================================================

COMMIT;
