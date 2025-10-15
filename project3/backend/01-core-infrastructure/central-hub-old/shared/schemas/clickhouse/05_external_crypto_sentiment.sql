-- =======================================================================
-- CLICKHOUSE EXTERNAL DATA - CRYPTO SENTIMENT
-- =======================================================================
-- Purpose: Cryptocurrency sentiment and social metrics
-- Source: CoinGecko API
-- Data Flow: External Collector → NATS/Kafka → Data Bridge → ClickHouse
-- Update Frequency: Every 30 minutes
-- Retention: 1 year
-- =======================================================================

CREATE DATABASE IF NOT EXISTS suho_analytics;

USE suho_analytics;

-- =======================================================================
-- TABLE: external_crypto_sentiment
-- =======================================================================

CREATE TABLE IF NOT EXISTS external_crypto_sentiment (
    -- Crypto Information
    coin_id String,                       -- bitcoin, ethereum, ripple, etc.
    name String,                          -- Bitcoin, Ethereum, etc.
    symbol String,                        -- BTC, ETH, etc.

    -- Price Data
    price_usd Float64,                    -- Current price in USD
    price_change_24h Float64,             -- 24h price change %
    market_cap_rank UInt16,               -- Market cap ranking

    -- Sentiment Metrics
    sentiment_votes_up Float64,           -- Sentiment votes up percentage
    community_score Float64,              -- Community score (0-100)

    -- Social Metrics
    twitter_followers UInt64,             -- Twitter followers count
    reddit_subscribers UInt64,            -- Reddit subscribers count

    -- Metadata
    source String DEFAULT 'coingecko',    -- Data source
    collected_at DateTime DEFAULT now()  -- Collection timestamp

) ENGINE = MergeTree()
ORDER BY (coin_id, collected_at)
TTL collected_at + INTERVAL 365 DAY  -- 1 year retention
SETTINGS index_granularity = 8192;

-- =======================================================================
-- INDEXES
-- =======================================================================

-- Coin ID index
CREATE INDEX IF NOT EXISTS idx_crypto_coin
ON external_crypto_sentiment (coin_id) TYPE set(0);

-- Market cap ranking index
CREATE INDEX IF NOT EXISTS idx_crypto_rank
ON external_crypto_sentiment (market_cap_rank) TYPE minmax;

-- Timestamp index
CREATE INDEX IF NOT EXISTS idx_crypto_time
ON external_crypto_sentiment (collected_at) TYPE minmax;

-- =======================================================================
-- SAMPLE QUERIES
-- =======================================================================

-- Get Bitcoin latest sentiment
-- SELECT *
-- FROM external_crypto_sentiment
-- WHERE coin_id = 'bitcoin'
-- ORDER BY collected_at DESC
-- LIMIT 1;

-- Top 5 cryptos by sentiment
-- SELECT coin_id, name, sentiment_votes_up, community_score
-- FROM external_crypto_sentiment
-- WHERE collected_at >= now() - INTERVAL 1 HOUR
-- ORDER BY sentiment_votes_up DESC
-- LIMIT 5;

-- Bitcoin sentiment trend (24 hours)
-- SELECT collected_at, sentiment_votes_up, price_usd
-- FROM external_crypto_sentiment
-- WHERE coin_id = 'bitcoin'
--   AND collected_at >= now() - INTERVAL 24 HOUR
-- ORDER BY collected_at;
