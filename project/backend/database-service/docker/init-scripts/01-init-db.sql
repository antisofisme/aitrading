-- Initialize AI Trading Database
-- This script runs when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application database if not exists
\c postgres;
SELECT 'CREATE DATABASE aitrading'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aitrading')\gexec

-- Connect to aitrading database
\c aitrading;

-- Create schema for application
CREATE SCHEMA IF NOT EXISTS aitrading;

-- Set search path
ALTER DATABASE aitrading SET search_path TO aitrading, public;

-- Create logging table for database operations
CREATE TABLE IF NOT EXISTS db_operation_logs (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    operation_details JSONB,
    execution_time_ms INTEGER,
    user_context VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_db_operation_logs_created_at ON db_operation_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_db_operation_logs_operation_type ON db_operation_logs(operation_type);

-- Create function to log database operations
CREATE OR REPLACE FUNCTION log_db_operation(
    p_operation_type VARCHAR(50),
    p_table_name VARCHAR(100),
    p_operation_details JSONB DEFAULT NULL,
    p_execution_time_ms INTEGER DEFAULT NULL,
    p_user_context VARCHAR(255) DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO db_operation_logs (
        operation_type,
        table_name,
        operation_details,
        execution_time_ms,
        user_context
    ) VALUES (
        p_operation_type,
        p_table_name,
        p_operation_details,
        p_execution_time_ms,
        p_user_context
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Log error but don't fail the main operation
        RAISE WARNING 'Failed to log database operation: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Create performance monitoring view
CREATE OR REPLACE VIEW performance_stats AS
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname IN ('public', 'aitrading')
ORDER BY schemaname, tablename, attname;

-- Create database size monitoring function
CREATE OR REPLACE FUNCTION get_database_size_info()
RETURNS TABLE(
    database_name TEXT,
    size_bytes BIGINT,
    size_pretty TEXT,
    table_count BIGINT,
    index_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        current_database()::TEXT,
        pg_database_size(current_database()),
        pg_size_pretty(pg_database_size(current_database())),
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')),
        (SELECT COUNT(*) FROM pg_indexes WHERE schemaname NOT IN ('information_schema', 'pg_catalog'))
    ;
END;
$$ LANGUAGE plpgsql;

-- Create connection monitoring function
CREATE OR REPLACE FUNCTION get_connection_info()
RETURNS TABLE(
    active_connections INTEGER,
    idle_connections INTEGER,
    total_connections INTEGER,
    max_connections INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER FILTER (WHERE state = 'active'),
        COUNT(*)::INTEGER FILTER (WHERE state = 'idle'),
        COUNT(*)::INTEGER,
        (SELECT setting::INTEGER FROM pg_settings WHERE name = 'max_connections')
    FROM pg_stat_activity
    WHERE datname = current_database();
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT USAGE ON SCHEMA aitrading TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA aitrading TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA aitrading TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA aitrading TO postgres;

-- Set up automatic cleanup job for old logs (if supported)
-- Note: This would typically be handled by the application or external cron job
COMMENT ON TABLE db_operation_logs IS 'Database operation logs - cleanup old entries periodically';

-- Log initialization
SELECT log_db_operation('INIT', 'database', '{"action": "database_initialized", "timestamp": "' || NOW() || '"}');