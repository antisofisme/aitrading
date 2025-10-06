-- ============================================================================
-- MT5 EA Integration - Database Initialization & Migration Script
-- ============================================================================
-- Run this script to set up the complete MT5 integration database
-- Execute in order: This file → 01-mt5-core-tables.sql → 02-mt5-trading-tables.sql → 03-mt5-audit-compliance.sql
-- ============================================================================

-- ============================================================================
-- PREREQUISITES CHECK
-- ============================================================================

-- Verify PostgreSQL version (minimum 14)
DO $$
BEGIN
    IF current_setting('server_version_num')::int < 140000 THEN
        RAISE EXCEPTION 'PostgreSQL 14 or higher required (current: %)', version();
    END IF;
END $$;

-- Verify TimescaleDB extension availability
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'
    ) THEN
        RAISE EXCEPTION 'TimescaleDB extension not available. Install: https://docs.timescale.com/install';
    END IF;
END $$;


-- ============================================================================
-- DATABASE SETUP
-- ============================================================================

-- Create database (if not exists)
-- Note: Must be run as postgres superuser
SELECT 'Creating database suho_trading...' AS status;

-- Create roles (if not exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'suho_service') THEN
        CREATE ROLE suho_service WITH LOGIN PASSWORD 'suho_service_password_change_me';
        RAISE NOTICE 'Created role: suho_service';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'suho_readonly') THEN
        CREATE ROLE suho_readonly WITH LOGIN PASSWORD 'suho_readonly_password_change_me';
        RAISE NOTICE 'Created role: suho_readonly';
    END IF;
END $$;


-- ============================================================================
-- EXTENSIONS
-- ============================================================================

\c suho_trading;

SELECT 'Installing extensions...' AS status;

-- Core extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";          -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";           -- Encryption functions
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query performance monitoring

-- TimescaleDB (must be first in shared_preload_libraries)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- PostGIS (optional, for geographic features)
-- CREATE EXTENSION IF NOT EXISTS postgis;

SELECT 'Extensions installed successfully' AS status;


-- ============================================================================
-- SCHEMAS
-- ============================================================================

-- Create tenant management schema
CREATE SCHEMA IF NOT EXISTS tenant_management;

-- Grant usage
GRANT USAGE ON SCHEMA public TO suho_service;
GRANT USAGE ON SCHEMA tenant_management TO suho_service;
GRANT USAGE ON SCHEMA public TO suho_readonly;
GRANT USAGE ON SCHEMA tenant_management TO suho_readonly;


-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function: Generate secure random token
CREATE OR REPLACE FUNCTION generate_api_key()
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(gen_random_bytes(32), 'hex');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Hash API key (bcrypt)
CREATE OR REPLACE FUNCTION hash_api_key(api_key TEXT)
RETURNS VARCHAR(255) AS $$
BEGIN
    RETURN crypt(api_key, gen_salt('bf', 10));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Verify API key
CREATE OR REPLACE FUNCTION verify_api_key(api_key TEXT, hash TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (crypt(api_key, hash) = hash);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Set tenant context (for RLS)
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id VARCHAR(50))
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', p_tenant_id, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get current tenant context
CREATE OR REPLACE FUNCTION get_current_tenant()
RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN current_setting('app.current_tenant_id', true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION generate_api_key() TO suho_service;
GRANT EXECUTE ON FUNCTION hash_api_key(TEXT) TO suho_service;
GRANT EXECUTE ON FUNCTION verify_api_key(TEXT, TEXT) TO suho_service;
GRANT EXECUTE ON FUNCTION set_tenant_context(VARCHAR) TO suho_service;
GRANT EXECUTE ON FUNCTION get_current_tenant() TO suho_service;


-- ============================================================================
-- PERFORMANCE TUNING
-- ============================================================================

-- TimescaleDB configuration
ALTER SYSTEM SET timescaledb.max_background_workers = 8;
ALTER SYSTEM SET max_worker_processes = 16;
ALTER SYSTEM SET shared_preload_libraries = 'timescaledb';

-- Query optimization
ALTER SYSTEM SET effective_cache_size = '4GB';
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';

-- Connection pooling
ALTER SYSTEM SET max_connections = 200;

-- Write-ahead log
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- Reload configuration (requires superuser)
-- SELECT pg_reload_conf();


-- ============================================================================
-- MONITORING VIEWS
-- ============================================================================

-- View: Hypertable summary
CREATE OR REPLACE VIEW v_hypertable_summary AS
SELECT
    h.schema_name,
    h.table_name,
    h.num_chunks,
    pg_size_pretty(hypertable_size(format('%I.%I', h.schema_name, h.table_name)::regclass)) AS total_size,
    pg_size_pretty(hypertable_index_size(format('%I.%I', h.schema_name, h.table_name)::regclass)) AS index_size
FROM timescaledb_information.hypertables h
ORDER BY hypertable_size(format('%I.%I', h.schema_name, h.table_name)::regclass) DESC;

-- View: Continuous aggregate status
CREATE OR REPLACE VIEW v_continuous_aggregates AS
SELECT
    view_name,
    materialization_hypertable_name,
    refresh_lag,
    last_run_succeeded,
    last_run_status
FROM timescaledb_information.continuous_aggregates;

-- View: Chunk status
CREATE OR REPLACE VIEW v_chunk_summary AS
SELECT
    hypertable_schema,
    hypertable_name,
    COUNT(*) AS chunk_count,
    pg_size_pretty(SUM(total_bytes)) AS total_size,
    MIN(range_start) AS oldest_data,
    MAX(range_end) AS newest_data
FROM timescaledb_information.chunks
GROUP BY hypertable_schema, hypertable_name
ORDER BY SUM(total_bytes) DESC;

-- Grant select on views
GRANT SELECT ON v_hypertable_summary TO suho_service, suho_readonly;
GRANT SELECT ON v_continuous_aggregates TO suho_service, suho_readonly;
GRANT SELECT ON v_chunk_summary TO suho_service, suho_readonly;


-- ============================================================================
-- HEALTH CHECK FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE (
    component VARCHAR,
    status VARCHAR,
    message TEXT
) AS $$
BEGIN
    -- Check database connection
    RETURN QUERY SELECT 'database'::VARCHAR, 'healthy'::VARCHAR, 'Database connection OK'::TEXT;

    -- Check TimescaleDB
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        RETURN QUERY SELECT 'timescaledb'::VARCHAR, 'healthy'::VARCHAR,
            ('TimescaleDB version: ' || extversion)::TEXT
        FROM pg_extension WHERE extname = 'timescaledb';
    ELSE
        RETURN QUERY SELECT 'timescaledb'::VARCHAR, 'error'::VARCHAR, 'TimescaleDB not installed'::TEXT;
    END IF;

    -- Check hypertables
    IF EXISTS (SELECT 1 FROM timescaledb_information.hypertables) THEN
        RETURN QUERY SELECT 'hypertables'::VARCHAR, 'healthy'::VARCHAR,
            (COUNT(*)::TEXT || ' hypertables created')::TEXT
        FROM timescaledb_information.hypertables;
    ELSE
        RETURN QUERY SELECT 'hypertables'::VARCHAR, 'warning'::VARCHAR, 'No hypertables found'::TEXT;
    END IF;

    -- Check continuous aggregates
    IF EXISTS (SELECT 1 FROM timescaledb_information.continuous_aggregates) THEN
        RETURN QUERY SELECT 'continuous_aggregates'::VARCHAR, 'healthy'::VARCHAR,
            (COUNT(*)::TEXT || ' continuous aggregates active')::TEXT
        FROM timescaledb_information.continuous_aggregates;
    END IF;

    RETURN;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION health_check() TO suho_service, suho_readonly;


-- ============================================================================
-- SAMPLE TENANT SETUP (FOR TESTING)
-- ============================================================================

-- Insert sample tenant
INSERT INTO tenant_management.tenants (tenant_id, company_name, subscription_tier, status)
VALUES
    ('tenant_demo', 'Demo Tenant', 'free', 'active'),
    ('tenant_premium', 'Premium Tenant', 'premium', 'active')
ON CONFLICT (tenant_id) DO NOTHING;

-- Insert sample tenant configurations
INSERT INTO tenant_management.tenant_configurations (tenant_id, config_key, config_value)
VALUES
    ('tenant_demo', 'max_accounts', '{"value": 2}'::jsonb),
    ('tenant_demo', 'max_daily_trades', '{"value": 50}'::jsonb),
    ('tenant_premium', 'max_accounts', '{"value": 10}'::jsonb),
    ('tenant_premium', 'max_daily_trades', '{"value": 500}'::jsonb)
ON CONFLICT (tenant_id, config_key) DO NOTHING;


-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Running health check...' AS status;
SELECT * FROM health_check();

SELECT 'Initialization complete!' AS status;
SELECT 'Next steps:' AS step, '1. Run 01-mt5-core-tables.sql' AS instruction
UNION ALL
SELECT '', '2. Run 02-mt5-trading-tables.sql'
UNION ALL
SELECT '', '3. Run 03-mt5-audit-compliance.sql'
UNION ALL
SELECT '', '4. Verify: SELECT * FROM v_hypertable_summary;';

COMMIT;
