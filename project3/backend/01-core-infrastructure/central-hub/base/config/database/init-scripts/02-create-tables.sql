-- Create core tables for Suho Trading Platform
-- Multi-tenant time-series tables optimized for trading data

\c suho_trading;

-- Set search path
SET search_path TO public, tenant_management;

-- Create tenant registry table
CREATE TABLE IF NOT EXISTS tenant_management.tenants (
    tenant_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create tenant configurations table
CREATE TABLE IF NOT EXISTS tenant_management.tenant_configurations (
    tenant_id VARCHAR(50) REFERENCES tenant_management.tenants(tenant_id),
    config_key VARCHAR(100) NOT NULL,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, config_key)
);

-- Create time-series table for trading data (hypertable)
CREATE TABLE IF NOT EXISTS trading_data (
    time TIMESTAMPTZ NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    mt5_account_id BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    bid DECIMAL(10,5),
    ask DECIMAL(10,5),
    volume INTEGER,
    spread DECIMAL(6,2),
    server_time TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('trading_data', 'time', chunk_time_interval => INTERVAL '1 hour');

-- Add dimension for tenant partitioning
SELECT add_dimension('trading_data', 'tenant_id', number_partitions => 4);

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_trading_data_tenant_symbol_time
ON trading_data (tenant_id, symbol, time DESC);

CREATE INDEX IF NOT EXISTS idx_trading_data_user_time
ON trading_data (tenant_id, user_id, time DESC);

-- Create row-level security policy
ALTER TABLE trading_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_trading_data ON trading_data
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Create AI predictions table
CREATE TABLE IF NOT EXISTS ai_predictions (
    time TIMESTAMPTZ NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    model_version VARCHAR(20),
    features JSONB,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('ai_predictions', 'time', chunk_time_interval => INTERVAL '6 hours');

-- Add tenant dimension
SELECT add_dimension('ai_predictions', 'tenant_id', number_partitions => 4);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ai_predictions_tenant_symbol_time
ON ai_predictions (tenant_id, symbol, time DESC);

-- Row-level security
ALTER TABLE ai_predictions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_ai_predictions ON ai_predictions
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- REMOVED: service_registry table
-- Reason: Not used in Docker Compose static topology
-- Services use environment variables instead of dynamic service discovery
-- Date removed: 2025-10-16

-- Create user sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    session_data JSONB DEFAULT '{}'::jsonb
);

-- Create index for session cleanup
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions (expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_tenant_user ON user_sessions (tenant_id, user_id);

-- Row-level security for sessions
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_user_sessions ON user_sessions
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Create notification logs table
CREATE TABLE IF NOT EXISTS notification_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL, -- 'email', 'sms', 'push', 'telegram'
    status VARCHAR(20) DEFAULT 'pending',
    message_data JSONB NOT NULL,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for notification queries
CREATE INDEX IF NOT EXISTS idx_notification_logs_tenant_user_time
ON notification_logs (tenant_id, user_id, created_at DESC);

-- Row-level security
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_notification_logs ON notification_logs
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Grant permissions to service role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO suho_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA tenant_management TO suho_service;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO suho_service;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA tenant_management TO suho_service;

-- Grant read-only access
GRANT SELECT ON ALL TABLES IN SCHEMA public TO suho_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA tenant_management TO suho_readonly;

-- Create function for automatic tenant schema creation
CREATE OR REPLACE FUNCTION create_tenant_schema(p_tenant_id TEXT)
RETURNS VOID AS $$
DECLARE
    schema_name TEXT;
BEGIN
    schema_name := 'tenant_' || p_tenant_id;

    -- Create schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);

    -- Grant permissions
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO suho_service', schema_name);
    EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO suho_readonly', schema_name);

    -- Create tenant-specific tables
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.users (
            user_id VARCHAR(50) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            subscription_tier VARCHAR(20) NOT NULL DEFAULT ''free'',
            subscription_limits JSONB DEFAULT ''{}''::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    ', schema_name);

    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.mt5_accounts (
            account_id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(50) REFERENCES %I.users(user_id),
            account_number VARCHAR(50) NOT NULL,
            broker VARCHAR(100),
            account_type VARCHAR(20) DEFAULT ''demo'',
            balance DECIMAL(15,2),
            equity DECIMAL(15,2),
            margin DECIMAL(15,2),
            status VARCHAR(20) DEFAULT ''active'',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ', schema_name, schema_name);

    -- Grant permissions on new tables
    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO suho_service', schema_name);
    EXECUTE format('GRANT USAGE ON ALL SEQUENCES IN SCHEMA %I TO suho_service', schema_name);

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION create_tenant_schema(TEXT) TO suho_service;

COMMIT;