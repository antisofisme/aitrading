-- =======================================================================
-- CLICKHOUSE EXTERNAL DATA - MARKET SESSIONS
-- =======================================================================
-- Purpose: Forex market sessions and liquidity levels
-- Source: Market Sessions Calculator
-- Data Flow: External Collector → NATS/Kafka → Data Bridge → ClickHouse
-- Update Frequency: Every 5 minutes
-- Retention: 90 days
-- =======================================================================

CREATE DATABASE IF NOT EXISTS suho_analytics;

USE suho_analytics;

-- =======================================================================
-- TABLE: external_market_sessions
-- =======================================================================

CREATE TABLE IF NOT EXISTS external_market_sessions (
    -- Session Information
    current_utc_time String,              -- Current UTC time (HH:MM:SS)
    active_sessions_count UInt8,          -- Number of active sessions (0-4)
    active_sessions String,               -- Comma-separated: tokyo,london,newyork,sydney

    -- Liquidity Assessment
    liquidity_level String,               -- very_low, low, medium, high, very_high

    -- Metadata
    collected_at DateTime DEFAULT now()  -- Collection timestamp

) ENGINE = MergeTree()
ORDER BY collected_at
TTL collected_at + INTERVAL 90 DAY  -- 90 days retention
SETTINGS index_granularity = 8192;

-- =======================================================================
-- INDEXES
-- =======================================================================

-- Timestamp index
CREATE INDEX IF NOT EXISTS idx_sessions_time
ON external_market_sessions (collected_at) TYPE minmax;

-- Active sessions count index
CREATE INDEX IF NOT EXISTS idx_sessions_count
ON external_market_sessions (active_sessions_count) TYPE minmax;

-- Liquidity level index
CREATE INDEX IF NOT EXISTS idx_sessions_liquidity
ON external_market_sessions (liquidity_level) TYPE set(0);

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get current market sessions
-- SELECT current_utc_time, active_sessions_count, active_sessions, liquidity_level
-- FROM external_market_sessions
-- ORDER BY collected_at DESC
-- LIMIT 1;

-- Liquidity level distribution (last 24 hours)
-- SELECT liquidity_level, count() as count
-- FROM external_market_sessions
-- WHERE collected_at >= now() - INTERVAL 24 HOUR
-- GROUP BY liquidity_level
-- ORDER BY count DESC;

-- High liquidity periods (last 7 days)
-- SELECT collected_at, current_utc_time, active_sessions, liquidity_level
-- FROM external_market_sessions
-- WHERE liquidity_level IN ('high', 'very_high')
--   AND collected_at >= now() - INTERVAL 7 DAY
-- ORDER BY collected_at;

-- Session overlap times (3+ active sessions)
-- SELECT collected_at, current_utc_time, active_sessions_count, active_sessions
-- FROM external_market_sessions
-- WHERE active_sessions_count >= 3
--   AND collected_at >= now() - INTERVAL 7 DAY
-- ORDER BY collected_at;
