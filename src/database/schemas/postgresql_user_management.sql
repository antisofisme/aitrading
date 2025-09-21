-- =====================================================
-- PostgreSQL User Management and Authentication Schema
-- Phase 1 Infrastructure Migration
-- Zero-Trust Security Model Implementation
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- =====================================================
-- 1. USER MANAGEMENT CORE TABLES
-- =====================================================

-- Users table with enhanced security
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email CITEXT UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- bcrypt hash
    full_name VARCHAR(255),
    phone VARCHAR(20),
    country VARCHAR(2) DEFAULT 'ID', -- ISO country code
    language VARCHAR(5) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'Asia/Jakarta',

    -- Account status and verification
    is_active BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    phone_verified_at TIMESTAMP WITH TIME ZONE,

    -- Security fields
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(32),
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,

    -- Soft delete
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_login ON users(last_login_at);

-- =====================================================
-- 2. SUBSCRIPTION MANAGEMENT
-- =====================================================

-- Subscription tiers with probabilistic features
CREATE TABLE subscription_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Pricing
    price_monthly DECIMAL(10,2) NOT NULL,
    price_annual DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',

    -- Features and limits
    features JSONB NOT NULL DEFAULT '{}',
    api_requests_per_hour INTEGER DEFAULT 100,
    max_trading_accounts INTEGER DEFAULT 1,
    max_strategies INTEGER DEFAULT 5,

    -- Probabilistic features
    probability_updates_per_hour INTEGER DEFAULT 24,
    confidence_scoring BOOLEAN DEFAULT FALSE,
    advanced_analytics BOOLEAN DEFAULT FALSE,
    custom_models BOOLEAN DEFAULT FALSE,

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default subscription tiers
INSERT INTO subscription_tiers (name, display_name, description, price_monthly, price_annual, features, api_requests_per_hour, max_trading_accounts, max_strategies, probability_updates_per_hour, confidence_scoring, advanced_analytics, custom_models, sort_order) VALUES
('free', 'Free', 'Basic access with limited features', 0.00, 0.00, '{"basic_signals": true, "email_alerts": true}', 50, 1, 1, 6, false, false, false, 1),
('basic', 'Basic', 'Enhanced trading with probability awareness', 49.00, 490.00, '{"probability_scores": true, "telegram_alerts": true, "basic_analytics": true}', 200, 1, 3, 24, true, false, false, 2),
('professional', 'Professional', 'Real-time probability with multi-timeframe analysis', 199.00, 1990.00, '{"realtime_probability": true, "multi_timeframe": true, "cross_asset_correlation": true, "risk_management": true}', 1000, 3, 10, 144, true, true, false, 3),
('enterprise', 'Enterprise', 'Custom probability models and white-label access', 499.00, 4990.00, '{"custom_models": true, "api_access": true, "dedicated_support": true, "collaborative_learning": true}', 5000, 10, 50, 288, true, true, true, 4);

-- User subscriptions
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier_id UUID NOT NULL REFERENCES subscription_tiers(id),

    -- Subscription details
    status VARCHAR(20) DEFAULT 'pending', -- pending, active, suspended, cancelled, expired
    billing_cycle VARCHAR(20) DEFAULT 'monthly', -- monthly, annual

    -- Dates
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    current_period_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    current_period_end TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 month',
    cancelled_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Payment
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),

    -- Usage tracking
    usage_current_period JSONB DEFAULT '{}',
    usage_limits JSONB DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for subscription queries
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_user_subscriptions_period_end ON user_subscriptions(current_period_end);
CREATE UNIQUE INDEX idx_user_subscriptions_active ON user_subscriptions(user_id) WHERE status = 'active';

-- =====================================================
-- 3. AUTHENTICATION AND SESSIONS
-- =====================================================

-- JWT refresh tokens
CREATE TABLE user_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL, -- SHA-256 hash of refresh token
    token_type VARCHAR(20) DEFAULT 'refresh', -- refresh, verification, reset

    -- Token details
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,

    -- Security context
    ip_address INET,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for token management
CREATE INDEX idx_user_tokens_user_id ON user_tokens(user_id);
CREATE INDEX idx_user_tokens_hash ON user_tokens(token_hash);
CREATE INDEX idx_user_tokens_expires ON user_tokens(expires_at);
CREATE INDEX idx_user_tokens_type ON user_tokens(token_type);

-- User sessions for tracking active sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,

    -- Session details
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_info JSONB DEFAULT '{}',
    location JSONB DEFAULT '{}', -- GeoIP data

    -- Session status
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '7 days',

    -- Security flags
    is_suspicious BOOLEAN DEFAULT FALSE,
    risk_score INTEGER DEFAULT 0, -- 0-100

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for session management
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active, last_activity);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);

-- =====================================================
-- 4. TRADING ACCOUNTS AND CONFIGURATIONS
-- =====================================================

-- MT5 trading accounts (encrypted credentials)
CREATE TABLE trading_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Account identification
    account_name VARCHAR(100) NOT NULL,
    broker_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) DEFAULT 'demo', -- demo, live

    -- Encrypted credentials (using pgcrypto)
    login_encrypted BYTEA NOT NULL, -- Encrypted MT5 login
    password_encrypted BYTEA NOT NULL, -- Encrypted MT5 password
    server_encrypted BYTEA NOT NULL, -- Encrypted MT5 server

    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_connected_at TIMESTAMP WITH TIME ZONE,
    connection_status VARCHAR(20) DEFAULT 'disconnected',

    -- Risk management settings
    max_risk_per_trade DECIMAL(5,2) DEFAULT 2.00, -- percentage
    max_daily_loss DECIMAL(10,2) DEFAULT 100.00,
    max_drawdown DECIMAL(5,2) DEFAULT 10.00,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for trading accounts
CREATE INDEX idx_trading_accounts_user_id ON trading_accounts(user_id);
CREATE INDEX idx_trading_accounts_active ON trading_accounts(is_active);
CREATE INDEX idx_trading_accounts_type ON trading_accounts(account_type);

-- =====================================================
-- 5. USER PREFERENCES AND CONFIGURATIONS
-- =====================================================

-- User trading preferences with probabilistic settings
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Trading preferences
    preferred_symbols TEXT[] DEFAULT '{"EURUSD", "GBPUSD", "USDJPY", "XAUUSD"}',
    preferred_timeframes TEXT[] DEFAULT '{"M15", "H1", "H4", "D1"}',
    risk_tolerance VARCHAR(20) DEFAULT 'medium', -- low, medium, high

    -- Probabilistic AI preferences
    probability_threshold DECIMAL(5,2) DEFAULT 70.00, -- minimum confidence level
    enable_confidence_filtering BOOLEAN DEFAULT TRUE,
    enable_regime_awareness BOOLEAN DEFAULT TRUE,
    enable_correlation_analysis BOOLEAN DEFAULT FALSE,

    -- Notification preferences
    telegram_notifications BOOLEAN DEFAULT TRUE,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT FALSE,
    notification_frequency VARCHAR(20) DEFAULT 'realtime', -- realtime, hourly, daily

    -- UI preferences
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(5) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'Asia/Jakarta',
    currency_display VARCHAR(3) DEFAULT 'USD',

    -- Advanced settings (JSONB for flexibility)
    advanced_settings JSONB DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint and indexes
CREATE UNIQUE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- =====================================================
-- 6. SECURITY AND AUDIT LOGGING
-- =====================================================

-- Security events and audit trail
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Event details
    event_type VARCHAR(50) NOT NULL, -- login, logout, password_change, suspicious_activity, etc.
    event_category VARCHAR(20) DEFAULT 'security', -- security, authentication, authorization
    severity VARCHAR(10) DEFAULT 'info', -- info, warning, error, critical

    -- Event data
    description TEXT,
    details JSONB DEFAULT '{}',

    -- Context
    ip_address INET,
    user_agent TEXT,
    session_id UUID,

    -- Risk assessment
    risk_score INTEGER DEFAULT 0, -- 0-100
    is_suspicious BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for security monitoring
CREATE INDEX idx_security_events_user_id ON security_events(user_id);
CREATE INDEX idx_security_events_type ON security_events(event_type);
CREATE INDEX idx_security_events_severity ON security_events(severity);
CREATE INDEX idx_security_events_created_at ON security_events(created_at);
CREATE INDEX idx_security_events_suspicious ON security_events(is_suspicious) WHERE is_suspicious = TRUE;

-- =====================================================
-- 7. ROW LEVEL SECURITY (RLS) FOR MULTI-TENANCY
-- =====================================================

-- Enable RLS on user tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- RLS policies for user data isolation
CREATE POLICY user_isolation_policy ON users
    FOR ALL TO authenticated_users
    USING (id = current_setting('app.current_user_id')::UUID);

CREATE POLICY user_subscriptions_isolation_policy ON user_subscriptions
    FOR ALL TO authenticated_users
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY user_tokens_isolation_policy ON user_tokens
    FOR ALL TO authenticated_users
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY user_sessions_isolation_policy ON user_sessions
    FOR ALL TO authenticated_users
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY trading_accounts_isolation_policy ON trading_accounts
    FOR ALL TO authenticated_users
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY user_preferences_isolation_policy ON user_preferences
    FOR ALL TO authenticated_users
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- =====================================================
-- 8. FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscription_tiers_updated_at BEFORE UPDATE ON subscription_tiers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trading_accounts_updated_at BEFORE UPDATE ON trading_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
    p_user_id UUID,
    p_event_type VARCHAR(50),
    p_description TEXT DEFAULT NULL,
    p_details JSONB DEFAULT '{}',
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_severity VARCHAR(10) DEFAULT 'info'
)
RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO security_events (
        user_id, event_type, description, details,
        ip_address, user_agent, severity
    ) VALUES (
        p_user_id, p_event_type, p_description, p_details,
        p_ip_address, p_user_agent, p_severity
    ) RETURNING id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

-- Function to validate subscription access
CREATE OR REPLACE FUNCTION validate_subscription_feature(
    p_user_id UUID,
    p_feature_name VARCHAR(100)
)
RETURNS BOOLEAN AS $$
DECLARE
    has_feature BOOLEAN := FALSE;
BEGIN
    SELECT
        CASE
            WHEN st.features ? p_feature_name THEN
                (st.features ->> p_feature_name)::BOOLEAN
            ELSE FALSE
        END INTO has_feature
    FROM user_subscriptions us
    JOIN subscription_tiers st ON us.tier_id = st.id
    WHERE us.user_id = p_user_id
        AND us.status = 'active'
        AND us.current_period_end > NOW();

    RETURN COALESCE(has_feature, FALSE);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 9. DATABASE ROLES AND PERMISSIONS
-- =====================================================

-- Create application roles
CREATE ROLE authenticated_users;
CREATE ROLE api_service;
CREATE ROLE admin_service;

-- Grant permissions to authenticated_users role
GRANT SELECT, INSERT, UPDATE ON users TO authenticated_users;
GRANT SELECT ON subscription_tiers TO authenticated_users;
GRANT SELECT, INSERT, UPDATE ON user_subscriptions TO authenticated_users;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_tokens TO authenticated_users;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO authenticated_users;
GRANT SELECT, INSERT, UPDATE, DELETE ON trading_accounts TO authenticated_users;
GRANT SELECT, INSERT, UPDATE ON user_preferences TO authenticated_users;
GRANT INSERT ON security_events TO authenticated_users;

-- Grant permissions to api_service role
GRANT authenticated_users TO api_service;
GRANT SELECT ON security_events TO api_service;

-- Grant permissions to admin_service role
GRANT authenticated_users TO admin_service;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_service;

-- =====================================================
-- 10. PERFORMANCE OPTIMIZATION
-- =====================================================

-- Partial indexes for common queries
CREATE INDEX idx_users_active_verified ON users(id) WHERE is_active = TRUE AND is_verified = TRUE;
CREATE INDEX idx_subscriptions_active ON user_subscriptions(user_id, tier_id) WHERE status = 'active';
CREATE INDEX idx_sessions_active_recent ON user_sessions(user_id) WHERE is_active = TRUE AND last_activity > NOW() - INTERVAL '1 day';

-- Composite indexes for complex queries
CREATE INDEX idx_users_email_status ON users(email, is_active, is_verified) WHERE deleted_at IS NULL;
CREATE INDEX idx_subscriptions_user_status_period ON user_subscriptions(user_id, status, current_period_end);

-- =====================================================
-- 11. INITIAL DATA AND CONFIGURATION
-- =====================================================

-- Create default admin user (password: admin123)
INSERT INTO users (
    id, email, username, password_hash, full_name,
    is_active, is_verified, email_verified_at
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@aitrading.local',
    'admin',
    '$2b$12$LQv3c1yqBtnS6V69SrUuM.P9QEjX6J8KzNJJJfR3KR5yHFz1K6iOK', -- admin123
    'System Administrator',
    TRUE,
    TRUE,
    NOW()
);

-- Assign enterprise subscription to admin
INSERT INTO user_subscriptions (
    user_id, tier_id, status, amount, current_period_end
) SELECT
    '00000000-0000-0000-0000-000000000001',
    id,
    'active',
    0.00,
    NOW() + INTERVAL '1 year'
FROM subscription_tiers WHERE name = 'enterprise';

-- Create default preferences for admin
INSERT INTO user_preferences (user_id) VALUES ('00000000-0000-0000-0000-000000000001');

-- =====================================================
-- SCHEMA COMPLETE
-- =====================================================

COMMENT ON SCHEMA public IS 'PostgreSQL User Management and Authentication Schema for AI Trading Platform - Phase 1 Implementation with Zero-Trust Security Model';