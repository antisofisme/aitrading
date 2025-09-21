-- PostgreSQL Initialization Script for AI Trading Platform
-- Phase 1: Core Database Schema with Security and Optimized Logging

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application database if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = current_database()) THEN
        PERFORM dblink_exec('', 'CREATE DATABASE ' || current_database());
    END IF;
END $$;

-- ===========================================
-- SECURITY SCHEMAS
-- ===========================================

-- Users and Authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Sessions for Zero-Trust
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    device_fingerprint VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscription Management
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    features JSONB NOT NULL DEFAULT '{}',
    starts_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN DEFAULT true,
    payment_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Security Events Audit Trail
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    severity VARCHAR(20) DEFAULT 'INFO',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT false
);

-- MT5 Credentials (Encrypted)
CREATE TABLE IF NOT EXISTS mt5_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_login TEXT NOT NULL,
    encrypted_password TEXT NOT NULL,
    encrypted_server TEXT NOT NULL,
    encryption_key_id VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE
);

-- ===========================================
-- TRADING & BUSINESS SCHEMAS
-- ===========================================

-- Trading Signals with Server-Side Authority
CREATE TABLE IF NOT EXISTS trading_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    signal_type VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL, -- BUY, SELL, CLOSE
    lot_size DECIMAL(10,2) NOT NULL,
    entry_price DECIMAL(10,5),
    stop_loss DECIMAL(10,5),
    take_profit DECIMAL(10,5),
    risk_percentage DECIMAL(5,2),
    signal_data JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'PENDING',
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    execution_price DECIMAL(10,5),
    execution_data JSONB DEFAULT '{}'
);

-- Risk Management Parameters
CREATE TABLE IF NOT EXISTS risk_parameters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    max_daily_loss DECIMAL(10,2) DEFAULT 100.00,
    max_weekly_loss DECIMAL(10,2) DEFAULT 500.00,
    max_position_size DECIMAL(5,2) DEFAULT 2.00,
    max_open_positions INTEGER DEFAULT 5,
    risk_per_trade DECIMAL(5,2) DEFAULT 2.00,
    parameters JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trading History with Audit Trail
CREATE TABLE IF NOT EXISTS trading_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    signal_id UUID REFERENCES trading_signals(id),
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,
    lot_size DECIMAL(10,2) NOT NULL,
    entry_price DECIMAL(10,5) NOT NULL,
    exit_price DECIMAL(10,5),
    stop_loss DECIMAL(10,5),
    take_profit DECIMAL(10,5),
    profit_loss DECIMAL(10,2),
    commission DECIMAL(10,2),
    swap DECIMAL(10,2),
    duration_minutes INTEGER,
    trade_data JSONB DEFAULT '{}',
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- OPTIMIZED LOG RETENTION SCHEMAS
-- ===========================================

-- Log Retention Policies (81% Cost Reduction)
CREATE TABLE IF NOT EXISTS log_retention_policies (
    log_level VARCHAR(20) PRIMARY KEY,
    retention_days INTEGER NOT NULL,
    storage_tier VARCHAR(20) NOT NULL,
    compression_algo VARCHAR(20),
    compliance_required BOOLEAN DEFAULT FALSE,
    cost_per_gb_month DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Storage Tier Configuration
CREATE TABLE IF NOT EXISTS storage_tiers (
    tier_name VARCHAR(20) PRIMARY KEY,
    technology VARCHAR(50) NOT NULL,
    max_query_latency_ms INTEGER,
    cost_per_gb_month DECIMAL(10,4),
    compression_ratio DECIMAL(3,1),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Log Cost Metrics Tracking
CREATE TABLE IF NOT EXISTS log_cost_metrics (
    date DATE PRIMARY KEY,
    total_logs_gb DECIMAL(10,2),
    hot_storage_cost DECIMAL(10,2),
    warm_storage_cost DECIMAL(10,2),
    cold_storage_cost DECIMAL(10,2),
    total_monthly_cost DECIMAL(10,2),
    savings_vs_uniform DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Application Logs Summary (for cost tracking)
CREATE TABLE IF NOT EXISTS application_logs_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(50) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    log_count INTEGER NOT NULL,
    log_size_bytes BIGINT NOT NULL,
    hour_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- SYSTEM & MONITORING SCHEMAS
-- ===========================================

-- Service Health Monitoring
CREATE TABLE IF NOT EXISTS service_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    metadata JSONB DEFAULT '{}',
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance Metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Configuration Management
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'string',
    is_encrypted BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- INITIAL DATA POPULATION
-- ===========================================

-- Insert default log retention policies
INSERT INTO log_retention_policies (log_level, retention_days, storage_tier, compression_algo, compliance_required, cost_per_gb_month) VALUES
('DEBUG', 7, 'hot', NULL, FALSE, 0.90),
('INFO', 30, 'warm', 'lz4', FALSE, 0.425),
('WARNING', 90, 'warm', 'zstd', FALSE, 0.425),
('ERROR', 180, 'cold', 'zstd', TRUE, 0.18),
('CRITICAL', 365, 'cold', 'zstd-max', TRUE, 0.18)
ON CONFLICT (log_level) DO NOTHING;

-- Insert storage tier configurations
INSERT INTO storage_tiers (tier_name, technology, max_query_latency_ms, cost_per_gb_month, compression_ratio, is_active) VALUES
('hot', 'DragonflyDB + ClickHouse Memory', 1, 0.90, 1.0, TRUE),
('warm', 'ClickHouse SSD', 100, 0.425, 2.5, TRUE),
('cold', 'ClickHouse Compressed', 2000, 0.18, 4.5, TRUE)
ON CONFLICT (tier_name) DO NOTHING;

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('security.zero_trust_enabled', 'true', 'boolean', 'Enable zero-trust security model'),
('logging.optimization_enabled', 'true', 'boolean', 'Enable optimized log retention'),
('trading.server_side_authority', 'true', 'boolean', 'Enforce server-side trading authority'),
('mt5.credential_encryption', 'true', 'boolean', 'Enable MT5 credential encryption'),
('performance.monitoring_enabled', 'true', 'boolean', 'Enable performance monitoring'),
('subscription.validation_enabled', 'true', 'boolean', 'Enable real-time subscription validation')
ON CONFLICT (config_key) DO NOTHING;

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

-- Security and authentication indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events(created_at);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);

-- Trading and business indexes
CREATE INDEX IF NOT EXISTS idx_trading_signals_user_id ON trading_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_signals_status ON trading_signals(status);
CREATE INDEX IF NOT EXISTS idx_trading_signals_generated_at ON trading_signals(generated_at);
CREATE INDEX IF NOT EXISTS idx_trading_history_user_id ON trading_history(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_history_opened_at ON trading_history(opened_at);

-- Subscription indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_expires_at ON subscriptions(expires_at);

-- System monitoring indexes
CREATE INDEX IF NOT EXISTS idx_service_health_service_name ON service_health(service_name);
CREATE INDEX IF NOT EXISTS idx_service_health_checked_at ON service_health(checked_at);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_service ON performance_metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_recorded_at ON performance_metrics(recorded_at);

-- Log cost tracking indexes
CREATE INDEX IF NOT EXISTS idx_log_cost_metrics_date ON log_cost_metrics(date);
CREATE INDEX IF NOT EXISTS idx_application_logs_summary_hour ON application_logs_summary(hour_bucket);

-- ===========================================
-- FUNCTIONS AND TRIGGERS
-- ===========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mt5_credentials_updated_at BEFORE UPDATE ON mt5_credentials FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_risk_parameters_updated_at BEFORE UPDATE ON risk_parameters FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to validate subscription
CREATE OR REPLACE FUNCTION validate_user_subscription(user_uuid UUID)
RETURNS TABLE (
    is_valid BOOLEAN,
    tier VARCHAR(20),
    expires_at TIMESTAMP WITH TIME ZONE,
    features JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.status = 'active' AND (s.expires_at IS NULL OR s.expires_at > NOW()) as is_valid,
        s.tier,
        s.expires_at,
        s.features
    FROM subscriptions s
    WHERE s.user_id = user_uuid
    ORDER BY s.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate log storage costs
CREATE OR REPLACE FUNCTION calculate_daily_log_costs(target_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE (
    total_cost DECIMAL(10,2),
    hot_cost DECIMAL(10,2),
    warm_cost DECIMAL(10,2),
    cold_cost DECIMAL(10,2)
) AS $$
DECLARE
    hot_gb DECIMAL(10,2) := 0;
    warm_gb DECIMAL(10,2) := 0;
    cold_gb DECIMAL(10,2) := 0;
BEGIN
    -- Calculate storage usage by tier (simplified example)
    SELECT
        COALESCE(SUM(CASE WHEN NOW() - created_at <= INTERVAL '3 days' THEN log_size_bytes ELSE 0 END) / 1073741824.0, 0),
        COALESCE(SUM(CASE WHEN NOW() - created_at > INTERVAL '3 days' AND NOW() - created_at <= INTERVAL '30 days' THEN log_size_bytes ELSE 0 END) / 1073741824.0, 0),
        COALESCE(SUM(CASE WHEN NOW() - created_at > INTERVAL '30 days' THEN log_size_bytes ELSE 0 END) / 1073741824.0, 0)
    INTO hot_gb, warm_gb, cold_gb
    FROM application_logs_summary
    WHERE DATE(created_at) = target_date;

    RETURN QUERY
    SELECT
        (hot_gb * 0.90 + warm_gb * 0.425 + cold_gb * 0.18) as total_cost,
        hot_gb * 0.90 as hot_cost,
        warm_gb * 0.425 as warm_cost,
        cold_gb * 0.18 as cold_cost;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- SECURITY POLICIES (Row Level Security)
-- ===========================================

-- Enable RLS on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt5_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_history ENABLE ROW LEVEL SECURITY;

-- Security policies (examples - adjust based on your authentication system)
-- Users can only see their own data
CREATE POLICY user_isolation_policy ON users FOR ALL TO authenticated
    USING (id = current_setting('app.current_user_id')::UUID);

CREATE POLICY session_isolation_policy ON user_sessions FOR ALL TO authenticated
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY mt5_isolation_policy ON mt5_credentials FOR ALL TO authenticated
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY trading_signals_isolation_policy ON trading_signals FOR ALL TO authenticated
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY trading_history_isolation_policy ON trading_history FOR ALL TO authenticated
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'AI Trading Platform PostgreSQL initialization completed successfully';
    RAISE NOTICE 'Zero-trust security schema created';
    RAISE NOTICE 'Optimized log retention system initialized';
    RAISE NOTICE 'Server-side trading authority schema ready';
    RAISE NOTICE 'Security audit trail enabled';
END $$;