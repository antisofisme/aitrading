-- Chain-Aware Debugging System Database Initialization
-- This script creates the basic database structure

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database if it doesn't exist (this line may not work in all setups)
-- CREATE DATABASE aitrading_db;

-- Basic health check function
CREATE OR REPLACE FUNCTION check_database_health()
RETURNS TABLE(
  status TEXT,
  timestamp TIMESTAMP WITH TIME ZONE,
  version TEXT,
  uptime INTERVAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    'healthy'::TEXT as status,
    NOW() as timestamp,
    version() as version,
    (NOW() - pg_postmaster_start_time()) as uptime;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old records
CREATE OR REPLACE FUNCTION cleanup_old_records()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER := 0;
BEGIN
  -- Clean records older than 30 days
  DELETE FROM chain_events WHERE created_at < NOW() - INTERVAL '30 days';
  GET DIAGNOSTICS deleted_count = ROW_COUNT;

  -- Clean old metrics (keep last 7 days)
  DELETE FROM system_metrics WHERE timestamp < NOW() - INTERVAL '7 days';

  -- Clean old anomalies (keep last 90 days)
  DELETE FROM chain_anomalies WHERE timestamp < NOW() - INTERVAL '90 days';

  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a simple function to generate test data (for development)
CREATE OR REPLACE FUNCTION generate_test_chain_events(
  chain_id_param TEXT,
  event_count INTEGER DEFAULT 100
)
RETURNS INTEGER AS $$
DECLARE
  i INTEGER;
  service_names TEXT[] := ARRAY['api-gateway', 'trading-engine', 'user-management', 'payment-service'];
  event_types TEXT[] := ARRAY['request', 'response', 'error', 'timeout'];
  statuses TEXT[] := ARRAY['success', 'error', 'timeout'];
BEGIN
  FOR i IN 1..event_count LOOP
    INSERT INTO chain_events (
      chain_id,
      service_name,
      event_type,
      status,
      duration_ms,
      created_at
    ) VALUES (
      chain_id_param,
      service_names[1 + (random() * (array_length(service_names, 1) - 1))::int],
      event_types[1 + (random() * (array_length(event_types, 1) - 1))::int],
      statuses[1 + (random() * (array_length(statuses, 1) - 1))::int],
      (random() * 5000)::int,
      NOW() - (random() * INTERVAL '1 hour')
    );
  END LOOP;

  RETURN event_count;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for better performance (these will be created by the application too)
-- But having them here ensures they exist from the start

-- Basic user for the application (adjust as needed)
-- CREATE USER chain_debug_user WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE aitrading_db TO chain_debug_user;

-- Grant permissions on all tables (when they're created)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO chain_debug_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO chain_debug_user;

-- Initial configuration data
-- This can be customized based on your service configuration

-- Example service recovery configurations
-- (The table will be created by the application, this is just example data)

-- Performance baseline data can be inserted here if needed

-- Log the initialization
DO $$
BEGIN
  RAISE NOTICE 'Chain-Aware Debugging System database initialized at %', NOW();
END $$;