-- PostgreSQL initialization script for Suho Trading Platform
-- Creates TimescaleDB extensions and multi-tenant setup

-- Connect to the main database
\c suho_trading;

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create extension for row-level security
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create roles for different access levels
-- Note: Passwords should be set via environment variables during deployment
-- This template should be processed by the application with actual passwords
CREATE ROLE suho_admin WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD '${POSTGRES_ADMIN_PASSWORD}';
CREATE ROLE suho_service WITH LOGIN PASSWORD '${POSTGRES_SERVICE_PASSWORD}';
CREATE ROLE suho_readonly WITH LOGIN PASSWORD '${POSTGRES_READONLY_PASSWORD}';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE suho_trading TO suho_admin;
GRANT CONNECT ON DATABASE suho_trading TO suho_service;
GRANT CONNECT ON DATABASE suho_trading TO suho_readonly;

-- Create tenant management schema
CREATE SCHEMA IF NOT EXISTS tenant_management;
GRANT USAGE ON SCHEMA tenant_management TO suho_service;
GRANT SELECT ON ALL TABLES IN SCHEMA tenant_management TO suho_readonly;

-- Create public schema permissions
GRANT USAGE ON SCHEMA public TO suho_service;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO suho_readonly;

-- Create function to set tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_id, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION set_tenant_context(TEXT) TO suho_service;

COMMIT;