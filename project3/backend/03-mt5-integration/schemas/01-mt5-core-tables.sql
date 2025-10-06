-- ============================================================================
-- MT5 EA Integration - Core Tables
-- ============================================================================
-- Multi-tenant trading platform with real-time MT5 account synchronization
-- Handles account profiles, balance tracking, broker quotes, and trade execution
--
-- SECURITY: Row-Level Security (RLS) enforces strict tenant isolation
-- PERFORMANCE: TimescaleDB hypertables with smart partitioning
-- COMPLIANCE: Full audit trail for regulatory requirements
-- ============================================================================

\c suho_trading;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- 1. USER ACCOUNTS & PROFILES
-- ============================================================================
-- Stores MT5 user account profiles and credentials
-- Links platform users to their MT5 broker accounts
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_user_accounts (
    -- Primary identifiers
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,

    -- MT5 Broker Information
    broker_name VARCHAR(100) NOT NULL,
    broker_server VARCHAR(100) NOT NULL,
    mt5_login BIGINT NOT NULL,                    -- MT5 account login number
    mt5_account_number VARCHAR(50) NOT NULL,       -- Broker account number

    -- Account Configuration
    account_type VARCHAR(20) NOT NULL DEFAULT 'demo',  -- 'demo', 'live', 'contest'
    account_currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    leverage INTEGER NOT NULL DEFAULT 100,

    -- Account Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'suspended', 'closed'
    is_verified BOOLEAN DEFAULT false,
    verification_date TIMESTAMPTZ,

    -- Connection & Security
    api_key_hash VARCHAR(255),                     -- Hashed EA API key for authentication
    last_connection_ip INET,
    last_connection_time TIMESTAMPTZ,
    connection_status VARCHAR(20) DEFAULT 'offline', -- 'online', 'offline', 'error'

    -- EA Configuration
    ea_version VARCHAR(20),
    ea_build INTEGER,
    ea_settings JSONB DEFAULT '{}'::jsonb,         -- EA-specific settings

    -- Risk Management Settings
    max_daily_loss DECIMAL(15,2),
    max_position_size DECIMAL(10,2),
    allowed_symbols TEXT[],
    trading_enabled BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    UNIQUE(tenant_id, mt5_login, broker_server),
    CHECK (leverage > 0),
    CHECK (account_type IN ('demo', 'live', 'contest'))
);

-- Indexes for performance
CREATE INDEX idx_mt5_accounts_tenant_user ON mt5_user_accounts(tenant_id, user_id);
CREATE INDEX idx_mt5_accounts_broker_login ON mt5_user_accounts(broker_server, mt5_login);
CREATE INDEX idx_mt5_accounts_status ON mt5_user_accounts(status, connection_status);
CREATE INDEX idx_mt5_accounts_updated ON mt5_user_accounts(updated_at DESC);

-- Row-Level Security
ALTER TABLE mt5_user_accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_mt5_accounts ON mt5_user_accounts
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_user_accounts IS 'MT5 user account profiles and broker connection settings';
COMMENT ON COLUMN mt5_user_accounts.mt5_login IS 'MT5 login number (unique per broker)';
COMMENT ON COLUMN mt5_user_accounts.api_key_hash IS 'Hashed API key for EA authentication (bcrypt)';
COMMENT ON COLUMN mt5_user_accounts.ea_settings IS 'EA-specific configuration (JSON)';


-- ============================================================================
-- 2. ACCOUNT BALANCE HISTORY (TIME-SERIES)
-- ============================================================================
-- Tracks account balance, equity, margin over time
-- Used for performance analytics and drawdown calculations
-- IMPORTANT: This is a TimescaleDB hypertable for efficient time-series queries
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_account_balance_history (
    -- Time-series primary key
    time TIMESTAMPTZ NOT NULL,

    -- Account identifiers
    account_id UUID NOT NULL REFERENCES mt5_user_accounts(account_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,

    -- Financial snapshot
    balance DECIMAL(15,2) NOT NULL,
    equity DECIMAL(15,2) NOT NULL,
    margin_used DECIMAL(15,2) DEFAULT 0,
    margin_free DECIMAL(15,2) DEFAULT 0,
    margin_level DECIMAL(8,2),                     -- Percentage: (equity/margin)*100

    -- Position metrics
    floating_profit DECIMAL(15,2) DEFAULT 0,
    realized_profit_today DECIMAL(15,2) DEFAULT 0,
    open_positions INTEGER DEFAULT 0,
    pending_orders INTEGER DEFAULT 0,

    -- Daily statistics
    daily_pnl DECIMAL(15,2),
    daily_trades INTEGER DEFAULT 0,
    daily_volume DECIMAL(15,4) DEFAULT 0,

    -- Risk metrics
    drawdown DECIMAL(15,2),                        -- Current drawdown from peak
    drawdown_percent DECIMAL(8,4),                 -- Percentage drawdown
    max_balance_today DECIMAL(15,2),               -- Peak balance today

    -- Data source
    source VARCHAR(20) DEFAULT 'ea_heartbeat',     -- 'ea_heartbeat', 'trade_execution', 'snapshot'

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Convert to TimescaleDB hypertable (1-hour chunks)
SELECT create_hypertable(
    'mt5_account_balance_history',
    'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Add tenant partitioning (space dimension)
SELECT add_dimension(
    'mt5_account_balance_history',
    'tenant_id',
    number_partitions => 4,
    if_not_exists => TRUE
);

-- Indexes for optimal query performance
CREATE INDEX idx_balance_history_account_time
    ON mt5_account_balance_history(account_id, time DESC);
CREATE INDEX idx_balance_history_tenant_time
    ON mt5_account_balance_history(tenant_id, time DESC);
CREATE INDEX idx_balance_history_user_time
    ON mt5_account_balance_history(tenant_id, user_id, time DESC);

-- Continuous aggregate for 5-minute snapshots
CREATE MATERIALIZED VIEW mt5_balance_5min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS bucket,
    account_id,
    tenant_id,
    user_id,
    LAST(balance, time) AS balance,
    LAST(equity, time) AS equity,
    LAST(margin_used, time) AS margin_used,
    LAST(margin_free, time) AS margin_free,
    AVG(margin_level) AS avg_margin_level,
    MIN(drawdown_percent) AS max_drawdown_percent,
    SUM(daily_trades) AS total_trades
FROM mt5_account_balance_history
GROUP BY bucket, account_id, tenant_id, user_id;

-- Refresh policy (automatic updates)
SELECT add_continuous_aggregate_policy('mt5_balance_5min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

-- Row-Level Security
ALTER TABLE mt5_account_balance_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_balance_history ON mt5_account_balance_history
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_account_balance_history IS 'Time-series account balance and equity tracking';
COMMENT ON COLUMN mt5_account_balance_history.margin_level IS 'Margin level percentage (equity/margin * 100)';
COMMENT ON COLUMN mt5_account_balance_history.source IS 'Data source: ea_heartbeat, trade_execution, snapshot';


-- ============================================================================
-- 3. BROKER QUOTES (TIME-SERIES)
-- ============================================================================
-- Stores real-time bid/ask quotes from user's broker
-- CRITICAL: Broker quotes may differ from Polygon market data
-- Used for: Signal execution, slippage tracking, arbitrage detection
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_broker_quotes (
    -- Time-series primary key
    time TIMESTAMPTZ NOT NULL,

    -- Account & Symbol
    account_id UUID NOT NULL REFERENCES mt5_user_accounts(account_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,

    -- Price data
    bid DECIMAL(10,5) NOT NULL,
    ask DECIMAL(10,5) NOT NULL,
    spread DECIMAL(6,2) NOT NULL,                  -- Pip spread (ask - bid)

    -- Quote metadata
    broker_server VARCHAR(100),
    quote_quality INTEGER DEFAULT 100,             -- 0-100, quality indicator
    is_tradeable BOOLEAN DEFAULT true,             -- Can execute trades?

    -- Market context
    market_session VARCHAR(20),                    -- 'asian', 'london', 'ny', 'overlap'
    volatility_index DECIMAL(8,4),                 -- Estimated volatility

    -- Deviation tracking (vs Polygon data)
    polygon_mid_price DECIMAL(10,5),               -- Polygon midpoint price (optional)
    price_deviation DECIMAL(8,5),                  -- Difference from Polygon
    deviation_percent DECIMAL(6,4),                -- Percentage deviation

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Convert to TimescaleDB hypertable (30-minute chunks for high-frequency data)
SELECT create_hypertable(
    'mt5_broker_quotes',
    'time',
    chunk_time_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE
);

-- Add composite partitioning (tenant + symbol)
SELECT add_dimension(
    'mt5_broker_quotes',
    'tenant_id',
    number_partitions => 4,
    if_not_exists => TRUE
);

-- Indexes for fast lookups
CREATE INDEX idx_broker_quotes_account_symbol_time
    ON mt5_broker_quotes(account_id, symbol, time DESC);
CREATE INDEX idx_broker_quotes_tenant_symbol_time
    ON mt5_broker_quotes(tenant_id, symbol, time DESC);
CREATE INDEX idx_broker_quotes_deviation
    ON mt5_broker_quotes(time DESC)
    WHERE ABS(deviation_percent) > 0.01; -- Index significant deviations only

-- Continuous aggregate for 1-minute OHLC
CREATE MATERIALIZED VIEW mt5_broker_quotes_1min_ohlc
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    account_id,
    tenant_id,
    symbol,
    FIRST(bid, time) AS open_bid,
    LAST(bid, time) AS close_bid,
    MAX(bid) AS high_bid,
    MIN(bid) AS low_bid,
    FIRST(ask, time) AS open_ask,
    LAST(ask, time) AS close_ask,
    MAX(ask) AS high_ask,
    MIN(ask) AS low_ask,
    AVG(spread) AS avg_spread,
    COUNT(*) AS tick_count,
    AVG(price_deviation) AS avg_deviation
FROM mt5_broker_quotes
GROUP BY bucket, account_id, tenant_id, symbol;

-- Refresh policy
SELECT add_continuous_aggregate_policy('mt5_broker_quotes_1min_ohlc',
    start_offset => INTERVAL '10 minutes',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- Row-Level Security
ALTER TABLE mt5_broker_quotes ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_broker_quotes ON mt5_broker_quotes
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_broker_quotes IS 'Real-time broker bid/ask quotes from MT5 EA';
COMMENT ON COLUMN mt5_broker_quotes.price_deviation IS 'Difference from Polygon market data (broker - polygon)';
COMMENT ON COLUMN mt5_broker_quotes.deviation_percent IS 'Percentage deviation from market data';


-- ============================================================================
-- 4. EA HEARTBEAT (TIME-SERIES)
-- ============================================================================
-- Tracks EA connection status and health
-- Used for: Connection monitoring, latency tracking, error detection
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_ea_heartbeat (
    -- Time-series primary key
    time TIMESTAMPTZ NOT NULL,

    -- Account identifiers
    account_id UUID NOT NULL REFERENCES mt5_user_accounts(account_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,

    -- Connection status
    status VARCHAR(20) NOT NULL,                   -- 'online', 'offline', 'degraded', 'error'
    connection_quality INTEGER DEFAULT 100,        -- 0-100
    latency_ms INTEGER,                            -- Round-trip latency

    -- EA Information
    ea_version VARCHAR(20),
    ea_uptime_seconds BIGINT,
    mt5_terminal_build INTEGER,
    mt5_terminal_connected BOOLEAN DEFAULT true,

    -- System resources
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,

    -- Error tracking
    error_count INTEGER DEFAULT 0,
    last_error_code INTEGER,
    last_error_message TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Convert to TimescaleDB hypertable (1-hour chunks)
SELECT create_hypertable(
    'mt5_ea_heartbeat',
    'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_ea_heartbeat_account_time
    ON mt5_ea_heartbeat(account_id, time DESC);
CREATE INDEX idx_ea_heartbeat_status
    ON mt5_ea_heartbeat(time DESC)
    WHERE status != 'online'; -- Index only non-online status

-- Retention policy (keep heartbeats for 30 days)
SELECT add_retention_policy('mt5_ea_heartbeat',
    INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Row-Level Security
ALTER TABLE mt5_ea_heartbeat ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_ea_heartbeat ON mt5_ea_heartbeat
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_ea_heartbeat IS 'MT5 EA connection status and health monitoring';


-- ============================================================================
-- 5. HELPER FUNCTIONS
-- ============================================================================

-- Function: Get latest account balance
CREATE OR REPLACE FUNCTION get_latest_account_balance(p_account_id UUID)
RETURNS TABLE (
    balance DECIMAL(15,2),
    equity DECIMAL(15,2),
    margin_level DECIMAL(8,2),
    snapshot_time TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        h.balance,
        h.equity,
        h.margin_level,
        h.time
    FROM mt5_account_balance_history h
    WHERE h.account_id = p_account_id
    ORDER BY h.time DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get broker quote vs market data deviation
CREATE OR REPLACE FUNCTION get_broker_price_deviation(
    p_account_id UUID,
    p_symbol VARCHAR(20),
    p_time_range INTERVAL DEFAULT INTERVAL '1 hour'
)
RETURNS TABLE (
    avg_deviation DECIMAL(8,5),
    max_deviation DECIMAL(8,5),
    avg_deviation_percent DECIMAL(6,4),
    sample_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        AVG(q.price_deviation) AS avg_deviation,
        MAX(ABS(q.price_deviation)) AS max_deviation,
        AVG(q.deviation_percent) AS avg_deviation_percent,
        COUNT(*) AS sample_count
    FROM mt5_broker_quotes q
    WHERE q.account_id = p_account_id
      AND q.symbol = p_symbol
      AND q.time >= NOW() - p_time_range
      AND q.polygon_mid_price IS NOT NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_latest_account_balance(UUID) TO suho_service;
GRANT EXECUTE ON FUNCTION get_broker_price_deviation(UUID, VARCHAR, INTERVAL) TO suho_service;


-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON mt5_user_accounts TO suho_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON mt5_account_balance_history TO suho_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON mt5_broker_quotes TO suho_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON mt5_ea_heartbeat TO suho_service;

GRANT SELECT ON mt5_user_accounts TO suho_readonly;
GRANT SELECT ON mt5_account_balance_history TO suho_readonly;
GRANT SELECT ON mt5_broker_quotes TO suho_readonly;
GRANT SELECT ON mt5_ea_heartbeat TO suho_readonly;

COMMIT;
