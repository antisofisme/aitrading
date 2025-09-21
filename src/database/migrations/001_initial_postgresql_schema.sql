-- =====================================================
-- Migration 001: Initial PostgreSQL Schema Setup
-- Version: 1.0.0
-- Created: 2025-09-21
-- Description: Initial user management and authentication schema
-- =====================================================

-- Migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by VARCHAR(100) DEFAULT current_user,
    checksum VARCHAR(64),
    execution_time_ms INTEGER DEFAULT 0
);

-- Record this migration
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('001', 'Initial PostgreSQL schema setup for user management', md5('001_initial_postgresql_schema'));

-- Start transaction for atomic migration
BEGIN;

-- Set execution start time
DO $$
DECLARE
    start_time TIMESTAMP WITH TIME ZONE := NOW();
BEGIN
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    CREATE EXTENSION IF NOT EXISTS "citext";

    -- Execute schema creation
    \i /mnt/f/WINDSURF/neliti_code/aitrading/src/database/schemas/postgresql_user_management.sql

    -- Update execution time
    UPDATE schema_migrations
    SET execution_time_ms = EXTRACT(EPOCH FROM (NOW() - start_time)) * 1000
    WHERE version = '001';
END $$;

-- Verify migration success
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    policy_count INTEGER;
BEGIN
    -- Check tables created
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'users', 'subscription_tiers', 'user_subscriptions',
        'user_tokens', 'user_sessions', 'trading_accounts',
        'user_preferences', 'security_events'
    );

    -- Check indexes created
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%';

    -- Check RLS policies
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public';

    -- Validation
    IF table_count < 8 THEN
        RAISE EXCEPTION 'Migration failed: Expected 8+ tables, found %', table_count;
    END IF;

    IF index_count < 15 THEN
        RAISE EXCEPTION 'Migration failed: Expected 15+ indexes, found %', index_count;
    END IF;

    IF policy_count < 6 THEN
        RAISE EXCEPTION 'Migration failed: Expected 6+ RLS policies, found %', policy_count;
    END IF;

    RAISE NOTICE 'Migration 001 completed successfully: % tables, % indexes, % policies',
                 table_count, index_count, policy_count;
END $$;

-- Commit transaction
COMMIT;

-- Post-migration verification
SELECT
    version,
    description,
    applied_at,
    execution_time_ms || 'ms' as duration
FROM schema_migrations
WHERE version = '001';