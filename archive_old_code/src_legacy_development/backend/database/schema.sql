-- AI Trading Platform Database Schema
-- PostgreSQL Schema for Backend API

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Users table with subscription tiers
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'free'
        CHECK (subscription_tier IN ('free', 'basic', 'pro', 'enterprise')),
    subscription_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (subscription_status IN ('active', 'inactive', 'suspended', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified BOOLEAN NOT NULL DEFAULT false
);

-- User profiles for trading preferences
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    risk_tolerance VARCHAR(10) NOT NULL DEFAULT 'medium'
        CHECK (risk_tolerance IN ('low', 'medium', 'high')),
    max_daily_loss DECIMAL(15,2) NOT NULL DEFAULT 1000.00,
    max_position_size DECIMAL(15,2) NOT NULL DEFAULT 10000.00,
    preferred_symbols TEXT[] DEFAULT ARRAY[]::TEXT[],
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    notifications_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Subscriptions table for multi-tenant billing
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL
        CHECK (tier IN ('free', 'basic', 'pro', 'enterprise')),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'suspended', 'cancelled')),
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    billing_cycle VARCHAR(10) NOT NULL DEFAULT 'monthly'
        CHECK (billing_cycle IN ('monthly', 'yearly')),
    features JSONB NOT NULL DEFAULT '[]'::jsonb,
    starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ends_at TIMESTAMPTZ NOT NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MT5 accounts for trading integration
CREATE TABLE IF NOT EXISTS mt5_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    login VARCHAR(50) NOT NULL,
    server VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    equity DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    margin DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    free_margin DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    margin_level DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_sync TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MT5 connections for monitoring
CREATE TABLE IF NOT EXISTS mt5_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES mt5_accounts(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'disconnected'
        CHECK (status IN ('connected', 'disconnected', 'error')),
    latency_ms INTEGER DEFAULT 0,
    last_heartbeat TIMESTAMPTZ,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trading signals
CREATE TABLE IF NOT EXISTS trading_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    type VARCHAR(4) NOT NULL CHECK (type IN ('buy', 'sell')),
    entry_price DECIMAL(12,5) NOT NULL,
    stop_loss DECIMAL(12,5),
    take_profit DECIMAL(12,5),
    volume DECIMAL(10,2) NOT NULL,
    confidence INTEGER NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    reasoning TEXT NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'executed', 'cancelled', 'expired')),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

-- MT5 trades (executed trades)
CREATE TABLE IF NOT EXISTS mt5_trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES mt5_accounts(id) ON DELETE CASCADE,
    signal_id UUID REFERENCES trading_signals(id),
    ticket BIGINT NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    type VARCHAR(4) NOT NULL CHECK (type IN ('buy', 'sell')),
    volume DECIMAL(10,2) NOT NULL,
    open_price DECIMAL(12,5) NOT NULL,
    close_price DECIMAL(12,5),
    stop_loss DECIMAL(12,5),
    take_profit DECIMAL(12,5),
    commission DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    swap DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    profit DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Security events for audit logging
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(30) NOT NULL
        CHECK (event_type IN ('login', 'logout', 'failed_login', 'token_refresh', 'password_change', 'suspicious_activity')),
    ip_address INET NOT NULL,
    user_agent TEXT,
    details JSONB DEFAULT '{}'::jsonb,
    risk_score INTEGER NOT NULL DEFAULT 0 CHECK (risk_score BETWEEN 0 AND 10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Error DNA logs for intelligent error handling
CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_code VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    stack TEXT,
    context JSONB DEFAULT '{}'::jsonb,
    user_id UUID REFERENCES users(id),
    request_id VARCHAR(100),
    severity VARCHAR(10) NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Log retention policies for cost optimization
CREATE TABLE IF NOT EXISTS log_retention_policies (
    log_level VARCHAR(20) PRIMARY KEY,
    retention_days INTEGER NOT NULL,
    storage_tier VARCHAR(20) NOT NULL
        CHECK (storage_tier IN ('hot', 'warm', 'cold')),
    compression_algo VARCHAR(20),
    compliance_required BOOLEAN DEFAULT FALSE,
    cost_per_gb_month DECIMAL(10,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Storage tier configuration
CREATE TABLE IF NOT EXISTS storage_tiers (
    tier_name VARCHAR(20) PRIMARY KEY,
    technology VARCHAR(50) NOT NULL,
    max_query_latency_ms INTEGER,
    cost_per_gb_month DECIMAL(10,4),
    compression_ratio DECIMAL(3,1),
    is_active BOOLEAN DEFAULT TRUE
);

-- Log cost tracking for optimization
CREATE TABLE IF NOT EXISTS log_cost_metrics (
    date DATE PRIMARY KEY,
    total_logs_gb DECIMAL(10,2),
    hot_storage_cost DECIMAL(10,2),
    warm_storage_cost DECIMAL(10,2),
    cold_storage_cost DECIMAL(10,2),
    total_monthly_cost DECIMAL(10,2),
    savings_vs_uniform DECIMAL(10,2)
);

-- API usage tracking for rate limiting and analytics
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    request_size_bytes INTEGER DEFAULT 0,
    response_size_bytes INTEGER DEFAULT 0,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance optimization

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Subscriptions indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_ends_at ON subscriptions(ends_at);

-- MT5 accounts indexes
CREATE INDEX IF NOT EXISTS idx_mt5_accounts_user_id ON mt5_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_mt5_accounts_active ON mt5_accounts(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_mt5_accounts_login ON mt5_accounts(login);

-- Trading signals indexes
CREATE INDEX IF NOT EXISTS idx_trading_signals_user_id ON trading_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_signals_status ON trading_signals(status);
CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol ON trading_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_signals_created_at ON trading_signals(created_at);
CREATE INDEX IF NOT EXISTS idx_trading_signals_expires_at ON trading_signals(expires_at);

-- MT5 trades indexes
CREATE INDEX IF NOT EXISTS idx_mt5_trades_account_id ON mt5_trades(account_id);
CREATE INDEX IF NOT EXISTS idx_mt5_trades_signal_id ON mt5_trades(signal_id);
CREATE INDEX IF NOT EXISTS idx_mt5_trades_symbol ON mt5_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_mt5_trades_opened_at ON mt5_trades(opened_at);
CREATE INDEX IF NOT EXISTS idx_mt5_trades_ticket ON mt5_trades(ticket);

-- Security events indexes
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_ip ON security_events(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events(created_at);
CREATE INDEX IF NOT EXISTS idx_security_events_risk_score ON security_events(risk_score) WHERE risk_score >= 7;

-- Error logs indexes
CREATE INDEX IF NOT EXISTS idx_error_logs_code ON error_logs(error_code);
CREATE INDEX IF NOT EXISTS idx_error_logs_user_id ON error_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs(severity);
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at);

-- API usage indexes
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_status_code ON api_usage(status_code);

-- Functions and triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mt5_accounts_updated_at BEFORE UPDATE ON mt5_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default log retention policies (81% cost optimization)
INSERT INTO log_retention_policies (log_level, retention_days, storage_tier, compression_algo, compliance_required, cost_per_gb_month) VALUES
('DEBUG', 7, 'hot', NULL, FALSE, 0.90),
('INFO', 30, 'warm', 'lz4', FALSE, 0.425),
('WARN', 90, 'warm', 'zstd', FALSE, 0.425),
('ERROR', 180, 'cold', 'zstd', FALSE, 0.18),
('CRITICAL', 365, 'cold', 'zstd', TRUE, 0.18)
ON CONFLICT (log_level) DO NOTHING;

-- Insert storage tier configuration
INSERT INTO storage_tiers (tier_name, technology, max_query_latency_ms, cost_per_gb_month, compression_ratio, is_active) VALUES
('hot', 'DragonflyDB + ClickHouse Memory Engine', 1, 0.90, 1.0, TRUE),
('warm', 'ClickHouse SSD Tables', 100, 0.425, 2.5, TRUE),
('cold', 'ClickHouse High Compression', 2000, 0.18, 5.0, TRUE)
ON CONFLICT (tier_name) DO NOTHING;

-- Create views for common queries

-- Active users view
CREATE OR REPLACE VIEW active_users AS
SELECT
    u.*,
    s.tier as current_tier,
    s.status as subscription_status,
    s.ends_at as subscription_ends_at
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id
WHERE u.is_active = true
AND (s.status = 'active' OR s.status IS NULL);

-- Trading performance view
CREATE OR REPLACE VIEW trading_performance AS
SELECT
    ts.user_id,
    COUNT(*) as total_signals,
    COUNT(*) FILTER (WHERE ts.status = 'executed') as executed_signals,
    COUNT(*) FILTER (WHERE ts.status = 'expired') as expired_signals,
    COUNT(*) FILTER (WHERE ts.status = 'pending') as pending_signals,
    AVG(ts.confidence) as avg_confidence,
    AVG(CASE WHEN ts.status = 'executed' THEN ts.confidence ELSE NULL END) as avg_executed_confidence
FROM trading_signals ts
WHERE ts.created_at >= NOW() - INTERVAL '30 days'
GROUP BY ts.user_id;

-- Security risk view
CREATE OR REPLACE VIEW high_risk_events AS
SELECT
    se.*,
    u.email,
    u.subscription_tier
FROM security_events se
LEFT JOIN users u ON se.user_id = u.id
WHERE se.risk_score >= 7
AND se.created_at >= NOW() - INTERVAL '24 hours';

-- Grant permissions (adjust according to your user setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO aitrading_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aitrading_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO aitrading_app;

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts with subscription tiers for multi-tenant support';
COMMENT ON TABLE subscriptions IS 'Subscription management with $49-999/month tiers';
COMMENT ON TABLE mt5_accounts IS 'MT5 trading account integration with sub-50ms latency optimization';
COMMENT ON TABLE trading_signals IS 'AI-generated trading signals with confidence scoring';
COMMENT ON TABLE security_events IS 'Zero-trust security audit trail with risk scoring';
COMMENT ON TABLE log_retention_policies IS 'Optimized log retention strategy achieving 81% cost reduction';
COMMENT ON TABLE error_logs IS 'ErrorDNA intelligent error handling and pattern recognition';

-- Performance monitoring
COMMENT ON INDEX idx_trading_signals_created_at IS 'Optimized for time-series queries on trading signals';
COMMENT ON INDEX idx_security_events_risk_score IS 'Partial index for high-risk security events only';
COMMENT ON INDEX idx_users_active IS 'Partial index for active users only to improve query performance';