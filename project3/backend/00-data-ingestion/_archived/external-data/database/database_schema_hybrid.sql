-- HYBRID DATABASE SCHEMA FOR TRADING OPTIMIZATION
-- Separated tables: market_ticks (high-freq patterns) + market_context (low-freq supporting)
-- Optimized for ML training and real-time trading pattern analysis

-- =========================================================================
-- TABLE 1: MARKET_TICKS - HIGH FREQUENCY OHLCV DATA
-- Purpose: Pattern formation, technical analysis, real-time trading
-- Sources: Yahoo Finance, Dukascopy, broker feeds
-- =========================================================================

CREATE TABLE IF NOT EXISTS market_ticks (
    -- Primary key and identity
    id BIGSERIAL PRIMARY KEY,

    -- Instrument and timeframe identification
    symbol VARCHAR(20) NOT NULL,              -- EURUSD, GBPUSD, XAUUSD, etc.
    timeframe VARCHAR(5) NOT NULL,            -- M1, M5, M15, H1, H4, D1
    timestamp BIGINT NOT NULL,                -- Unix timestamp in milliseconds

    -- OHLCV data for pattern analysis
    price_open DECIMAL(12,6) NOT NULL,        -- Opening price
    price_high DECIMAL(12,6) NOT NULL,        -- High price
    price_low DECIMAL(12,6) NOT NULL,         -- Low price
    price_close DECIMAL(12,6) NOT NULL,       -- Closing price
    volume BIGINT DEFAULT 0,                  -- Trading volume (0 for forex)

    -- Price movement metrics
    change_percent DECIMAL(8,4),              -- Price change %
    change_pips DECIMAL(8,2),                 -- Price change in pips

    -- Trading context
    session VARCHAR(20),                      -- London, NewYork, Tokyo, Sydney
    is_high_volatility BOOLEAN DEFAULT FALSE, -- Session overlap periods

    -- Data quality
    source VARCHAR(30) NOT NULL,              -- Yahoo, Dukascopy, MT5, etc.
    data_quality VARCHAR(20) DEFAULT 'good',  -- good, fair, poor

    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_ohlc_valid CHECK (
        price_high >= price_open AND
        price_high >= price_close AND
        price_low <= price_open AND
        price_low <= price_close
    ),
    CONSTRAINT chk_timeframe_valid CHECK (
        timeframe IN ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN')
    ),
    CONSTRAINT chk_timestamp_positive CHECK (timestamp > 0)
);

-- HIGH PERFORMANCE INDEXES FOR PATTERN QUERIES
CREATE UNIQUE INDEX IF NOT EXISTS idx_ticks_unique ON market_ticks (symbol, timeframe, timestamp);
CREATE INDEX IF NOT EXISTS idx_ticks_symbol_tf_time ON market_ticks (symbol, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_symbol_session ON market_ticks (symbol, session, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_timeframe_time ON market_ticks (timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_source_time ON market_ticks (source, timestamp DESC);

-- Partial indexes for common trading queries
CREATE INDEX IF NOT EXISTS idx_ticks_major_pairs ON market_ticks (symbol, timestamp DESC)
    WHERE symbol IN ('EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD');

CREATE INDEX IF NOT EXISTS idx_ticks_h1_recent ON market_ticks (symbol, timestamp DESC)
    WHERE timeframe = 'H1';

CREATE INDEX IF NOT EXISTS idx_ticks_high_vol ON market_ticks (symbol, timestamp DESC)
    WHERE is_high_volatility = true;

-- =========================================================================
-- TABLE 2: MARKET_CONTEXT - LOW FREQUENCY SUPPORTING DATA
-- Purpose: Economic context, sentiment, news, sessions for ML enhancement
-- Sources: FRED, CoinGecko, Fear&Greed, Exchange Rates, Economic Calendar
-- =========================================================================

CREATE TABLE IF NOT EXISTS market_context (
    -- Primary key and identity
    id BIGSERIAL PRIMARY KEY,

    -- Unique constraint for event deduplication (NEW)
    event_id VARCHAR(100),                    -- External API event identifier
    external_id VARCHAR(100),                 -- External system ID for deduplication

    -- Data classification
    data_type VARCHAR(30) NOT NULL,           -- economic, sentiment, crypto, exchange_rate, session, news
    symbol VARCHAR(50) NOT NULL,              -- CPIAUCSL, BTC, FEAR_GREED_INDEX, etc.
    timestamp BIGINT NOT NULL,                -- Unix timestamp in milliseconds

    -- Time classification (NEW)
    time_status VARCHAR(20) NOT NULL DEFAULT 'historical', -- historical, future, scheduled, live

    -- Universal value fields
    value DECIMAL(20,8),                      -- Main numeric value
    value_text VARCHAR(100),                  -- Text classification (Fear, Greed, etc.)

    -- Context metadata
    category VARCHAR(50),                     -- inflation, gdp, sentiment, etc.
    importance VARCHAR(20),                   -- high, medium, low
    frequency VARCHAR(20),                    -- monthly, daily, real-time
    units VARCHAR(50),                        -- %, Index, USD, etc.

    -- Event-specific fields (NEW)
    actual_value DECIMAL(20,8),               -- Actual result (for historical)
    forecast_value DECIMAL(20,8),             -- Predicted value (for future)
    previous_value DECIMAL(20,8),             -- Previous period result
    event_date TIMESTAMP,                     -- Scheduled event date
    release_date TIMESTAMP,                   -- Data release date

    -- Market impact assessment
    currency_impact TEXT[],                   -- Array of affected currencies [USD, EUR]
    forex_impact VARCHAR(30),                 -- bullish_usd, bearish_risk_currencies, etc.
    market_impact_score DECIMAL(3,2),         -- 0.0 to 1.0 impact score

    -- Source and quality
    source VARCHAR(50) NOT NULL,              -- FRED, CoinGecko, Alternative.me, etc.
    reliability VARCHAR(20) DEFAULT 'high',   -- high, medium, low

    -- Full context preservation
    metadata JSONB,                           -- Complete API response

    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_data_type_valid CHECK (
        data_type IN (
            'economic_indicator', 'cryptocurrency', 'market_sentiment',
            'exchange_rate', 'market_session', 'news_event', 'commodity',
            'economic_calendar', 'news_forecast'
        )
    ),
    CONSTRAINT chk_time_status_valid CHECK (
        time_status IN ('historical', 'future', 'scheduled', 'live', 'forecast')
    ),
    CONSTRAINT chk_timestamp_positive CHECK (timestamp > 0),
    CONSTRAINT chk_impact_score CHECK (market_impact_score BETWEEN 0.0 AND 1.0)
);

-- CONTEXT-OPTIMIZED INDEXES
CREATE INDEX IF NOT EXISTS idx_context_type_time ON market_context (data_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_context_symbol_time ON market_context (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_context_impact_time ON market_context (market_impact_score DESC, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_context_source_time ON market_context (source, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_context_currency_impact ON market_context USING GIN (currency_impact);

-- NEW: Unique constraint for deduplication
CREATE UNIQUE INDEX IF NOT EXISTS idx_context_event_dedup ON market_context (event_id, symbol, event_date)
    WHERE event_id IS NOT NULL;

-- Alternative deduplication by external_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_context_external_dedup ON market_context (external_id)
    WHERE external_id IS NOT NULL;

-- JSONB index for metadata queries
CREATE INDEX IF NOT EXISTS idx_context_metadata_gin ON market_context USING GIN (metadata);

-- Partial indexes for frequent context queries
CREATE INDEX IF NOT EXISTS idx_context_high_impact ON market_context (data_type, timestamp DESC)
    WHERE market_impact_score >= 0.7;

CREATE INDEX IF NOT EXISTS idx_context_economic ON market_context (symbol, timestamp DESC)
    WHERE data_type = 'economic_indicator';

CREATE INDEX IF NOT EXISTS idx_context_sentiment ON market_context (timestamp DESC)
    WHERE data_type IN ('market_sentiment', 'cryptocurrency');

-- NEW: Time-based indexes for historical vs future analysis
CREATE INDEX IF NOT EXISTS idx_context_historical ON market_context (data_type, symbol, timestamp DESC)
    WHERE time_status = 'historical';

CREATE INDEX IF NOT EXISTS idx_context_future ON market_context (event_date, importance DESC)
    WHERE time_status IN ('future', 'scheduled', 'forecast');

CREATE INDEX IF NOT EXISTS idx_context_calendar_events ON market_context (event_date, currency_impact)
    WHERE time_status = 'scheduled' AND importance = 'high';

-- =========================================================================
-- OPTIMIZED QUERY PATTERNS FOR TRADING & ML
-- =========================================================================

-- 1. GET PATTERN DATA FOR TECHNICAL ANALYSIS (Fast - Primary Table)
/*
SELECT symbol, timestamp, timeframe, price_open, price_high, price_low, price_close, volume
FROM market_ticks
WHERE symbol = 'EURUSD' AND timeframe = 'H1' AND session = 'London'
ORDER BY timestamp DESC
LIMIT 200;
*/

-- 2. GET SUPPORTING CONTEXT FOR TIME RANGE (Fast - Context Table)
/*
SELECT data_type, symbol, value, value_text, market_impact_score, forex_impact
FROM market_context
WHERE timestamp BETWEEN ? AND ?
  AND data_type IN ('economic_indicator', 'market_sentiment')
  AND market_impact_score >= 0.5
ORDER BY market_impact_score DESC;
*/

-- 3. COMBINED ML FEATURE QUERY (Join when needed)
/*
WITH price_patterns AS (
  SELECT * FROM market_ticks
  WHERE symbol = 'EURUSD' AND timeframe = 'H1'
  ORDER BY timestamp DESC LIMIT 100
),
context_data AS (
  SELECT * FROM market_context
  WHERE timestamp >= (SELECT MIN(timestamp) FROM price_patterns)
    AND market_impact_score >= 0.6
)
SELECT p.*, c.data_type, c.value as context_value, c.forex_impact
FROM price_patterns p
LEFT JOIN context_data c ON c.timestamp <= p.timestamp
ORDER BY p.timestamp DESC;
*/

-- 4. REAL-TIME TRADING CONTEXT (Latest data)
/*
WITH latest_price AS (
  SELECT * FROM market_ticks
  WHERE symbol = 'EURUSD' AND timeframe = 'M5'
  ORDER BY timestamp DESC LIMIT 1
),
current_context AS (
  SELECT * FROM market_context
  WHERE timestamp >= EXTRACT(EPOCH FROM NOW() - INTERVAL '1 hour') * 1000
    AND data_type IN ('market_sentiment', 'market_session')
)
SELECT lp.price_close, lp.session, cc.data_type, cc.value_text, cc.forex_impact
FROM latest_price lp
CROSS JOIN current_context cc;
*/

-- =========================================================================
-- UPSERT PATTERNS FOR FORECAST → ACTUAL DATA FLOW
-- =========================================================================

-- 1. INSERT OR UPDATE ECONOMIC CALENDAR EVENT (PostgreSQL UPSERT)
/*
INSERT INTO market_context (
    event_id, symbol, data_type, source, time_status,
    event_date, forecast_value, actual_value, importance, currency_impact
) VALUES (
    'nfp_2024_03_01', 'NFP', 'economic_calendar', 'EconomicCalendar', 'scheduled',
    '2024-03-01 13:30:00', 340000, NULL, 'high', ARRAY['USD']
)
ON CONFLICT (event_id, symbol, event_date)
DO UPDATE SET
    -- PRESERVE FORECAST, ADD ACTUAL (both must exist for AI learning)
    forecast_value = COALESCE(market_context.forecast_value, EXCLUDED.forecast_value),
    actual_value = COALESCE(EXCLUDED.actual_value, market_context.actual_value),
    previous_value = COALESCE(EXCLUDED.previous_value, market_context.previous_value),

    -- Update status when actual data arrives
    time_status = CASE
        WHEN EXCLUDED.actual_value IS NOT NULL THEN 'historical'
        ELSE market_context.time_status
    END,

    -- Calculate surprise factor automatically
    market_impact_score = CASE
        WHEN EXCLUDED.actual_value IS NOT NULL AND market_context.forecast_value IS NOT NULL
        THEN LEAST(
            ABS(EXCLUDED.actual_value - market_context.forecast_value) /
            NULLIF(ABS(market_context.forecast_value), 0) * 2.0,  -- Surprise factor * 2
            1.0
        )
        ELSE COALESCE(EXCLUDED.market_impact_score, market_context.market_impact_score)
    END,

    -- Update metadata with learning data
    metadata = COALESCE(market_context.metadata, '{}')::jsonb ||
               COALESCE(EXCLUDED.metadata, '{}')::jsonb ||
               CASE
                   WHEN EXCLUDED.actual_value IS NOT NULL AND market_context.forecast_value IS NOT NULL
                   THEN jsonb_build_object(
                       'surprise_magnitude',
                       ABS(EXCLUDED.actual_value - market_context.forecast_value) /
                       NULLIF(ABS(market_context.forecast_value), 0),
                       'forecast_accuracy',
                       CASE
                           WHEN ABS(EXCLUDED.actual_value - market_context.forecast_value) /
                                NULLIF(ABS(market_context.forecast_value), 0) > 0.1
                           THEN 'poor'
                           WHEN ABS(EXCLUDED.actual_value - market_context.forecast_value) /
                                NULLIF(ABS(market_context.forecast_value), 0) > 0.05
                           THEN 'moderate'
                           ELSE 'good'
                       END,
                       'directional_accuracy',
                       CASE
                           WHEN (EXCLUDED.actual_value > market_context.forecast_value AND
                                 market_context.forecast_value > market_context.previous_value) OR
                                (EXCLUDED.actual_value < market_context.forecast_value AND
                                 market_context.forecast_value < market_context.previous_value)
                           THEN 'correct'
                           ELSE 'wrong'
                       END
                   )
                   ELSE '{}'::jsonb
               END,

    updated_at = NOW();
*/

-- 2. QUERY PATTERN: GET FORECAST WITH LATEST ACTUAL DATA
/*
WITH latest_events AS (
    SELECT DISTINCT ON (event_id) *
    FROM market_context
    WHERE data_type = 'economic_calendar'
    ORDER BY event_id, created_at DESC
)
SELECT
    event_id,
    symbol,
    event_date,
    forecast_value,
    actual_value,
    CASE
        WHEN actual_value IS NOT NULL THEN 'completed'
        WHEN event_date < NOW() THEN 'missed_data'
        ELSE 'upcoming'
    END as event_status,
    ABS(actual_value - forecast_value) as surprise_magnitude
FROM latest_events
WHERE event_date BETWEEN NOW() - INTERVAL '7 days' AND NOW() + INTERVAL '7 days';
*/

-- 3. AI LEARNING DATASET: FORECAST VS ACTUAL ANALYSIS
/*
-- Complete learning dataset with both forecast and actual values
WITH learning_data AS (
    SELECT
        symbol,
        event_date,
        forecast_value,
        actual_value,
        previous_value,

        -- Surprise metrics for AI learning
        ABS(actual_value - forecast_value) / NULLIF(ABS(forecast_value), 0) as surprise_magnitude,
        (actual_value - forecast_value) / NULLIF(ABS(forecast_value), 0) as directional_surprise,

        -- Trend analysis
        CASE
            WHEN actual_value > forecast_value AND forecast_value > previous_value THEN 'accelerating_positive'
            WHEN actual_value < forecast_value AND forecast_value < previous_value THEN 'accelerating_negative'
            WHEN actual_value > forecast_value AND forecast_value < previous_value THEN 'reversal_positive'
            WHEN actual_value < forecast_value AND forecast_value > previous_value THEN 'reversal_negative'
            ELSE 'inline_trend'
        END as trend_pattern,

        -- Market impact score (calculated automatically)
        market_impact_score,

        -- Get price reaction (for supervised learning)
        LAG(price_close) OVER w as price_before,
        LEAD(price_close, 1) OVER w as price_1h_after,
        LEAD(price_close, 24) OVER w as price_24h_after

    FROM market_context mc
    LEFT JOIN market_ticks mt ON mt.symbol = CASE
        WHEN mc.currency_impact @> ARRAY['USD'] THEN 'EURUSD'
        WHEN mc.currency_impact @> ARRAY['EUR'] THEN 'EURUSD'
        WHEN mc.currency_impact @> ARRAY['GBP'] THEN 'GBPUSD'
        ELSE 'EURUSD'
    END
    AND mt.timestamp BETWEEN
        EXTRACT(EPOCH FROM mc.event_date) * 1000 - 3600000 AND  -- 1 hour before
        EXTRACT(EPOCH FROM mc.event_date) * 1000 + 86400000     -- 24 hours after

    WHERE mc.time_status = 'historical'
        AND mc.forecast_value IS NOT NULL
        AND mc.actual_value IS NOT NULL
        AND mc.event_date >= NOW() - INTERVAL '2 years'

    WINDOW w AS (PARTITION BY symbol ORDER BY event_date)
)
SELECT
    symbol,
    event_date,
    forecast_value,
    actual_value,
    surprise_magnitude,
    directional_surprise,
    trend_pattern,

    -- Price impact (TARGET for ML model)
    (price_1h_after - price_before) / NULLIF(price_before, 0) as price_impact_1h,
    (price_24h_after - price_before) / NULLIF(price_before, 0) as price_impact_24h,

    -- Classification target
    CASE
        WHEN ABS((price_1h_after - price_before) / NULLIF(price_before, 0)) > 0.001 THEN 'significant_move'
        ELSE 'minor_move'
    END as move_classification

FROM learning_data
ORDER BY event_date DESC;
*/

-- 4. FORECAST ACCURACY IMPROVEMENT TRACKING
/*
WITH accuracy_trends AS (
    SELECT
        symbol,
        DATE_TRUNC('month', event_date) as month,

        -- Accuracy metrics
        AVG(ABS(actual_value - forecast_value) / NULLIF(ABS(actual_value), 0)) as avg_error_rate,

        -- Directional accuracy
        COUNT(CASE
            WHEN (actual_value > forecast_value) = (forecast_value > previous_value)
            THEN 1
        END) * 100.0 / COUNT(*) as directional_accuracy_pct,

        -- Surprise frequency
        COUNT(CASE
            WHEN ABS(actual_value - forecast_value) / NULLIF(ABS(forecast_value), 0) > 0.1
            THEN 1
        END) * 100.0 / COUNT(*) as major_surprise_pct,

        COUNT(*) as total_events

    FROM market_context
    WHERE time_status = 'historical'
        AND forecast_value IS NOT NULL
        AND actual_value IS NOT NULL
        AND event_date >= NOW() - INTERVAL '12 months'
    GROUP BY symbol, DATE_TRUNC('month', event_date)
)
SELECT
    symbol,
    month,
    avg_error_rate,
    directional_accuracy_pct,
    major_surprise_pct,
    total_events,

    -- Trend analysis (improving vs deteriorating forecasts)
    LAG(avg_error_rate) OVER (PARTITION BY symbol ORDER BY month) as prev_error_rate,
    CASE
        WHEN avg_error_rate < LAG(avg_error_rate) OVER (PARTITION BY symbol ORDER BY month)
        THEN 'improving'
        ELSE 'deteriorating'
    END as accuracy_trend

FROM accuracy_trends
ORDER BY symbol, month DESC;
*/

-- =========================================================================
-- DATA ROUTING LOGIC (for collectors)
-- =========================================================================

-- HIGH FREQUENCY → market_ticks table:
-- - Yahoo Finance OHLCV data
-- - Dukascopy historical ticks
-- - Broker MT5/API real-time feeds
-- - All price/volume time series data

-- LOW FREQUENCY → market_context table:
-- - FRED economic indicators
-- - CoinGecko crypto prices/sentiment
-- - Fear & Greed Index
-- - Exchange rates (for reference)
-- - Market session data
-- - News events
-- - Economic calendar events

-- =========================================================================
-- MAINTENANCE & PERFORMANCE
-- =========================================================================

-- Data retention policies
-- Keep 1 year of tick data for most timeframes
-- DELETE FROM market_ticks
-- WHERE timestamp < EXTRACT(EPOCH FROM NOW() - INTERVAL '1 year') * 1000
--   AND timeframe IN ('M1', 'M5');

-- Keep 2 years for H1 and higher timeframes
-- DELETE FROM market_ticks
-- WHERE timestamp < EXTRACT(EPOCH FROM NOW() - INTERVAL '2 years') * 1000
--   AND timeframe IN ('H1', 'H4', 'D1');

-- Keep context data longer (5 years) - much smaller volume
-- DELETE FROM market_context
-- WHERE timestamp < EXTRACT(EPOCH FROM NOW() - INTERVAL '5 years') * 1000;

-- Vacuum and analyze for performance
-- VACUUM ANALYZE market_ticks;
-- VACUUM ANALYZE market_context;

-- Monitor table sizes
-- SELECT
--   schemaname,
--   tablename,
--   attname,
--   n_distinct,
--   most_common_vals
-- FROM pg_stats
-- WHERE tablename IN ('market_ticks', 'market_context');