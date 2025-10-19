-- =====================================================================
-- SERVICE CONFIGURATION MANAGEMENT - CENTRALIZED CONFIG TABLES
-- =====================================================================
-- Purpose: Store and manage operational configurations for all microservices
-- Created: 2025-10-19
-- Pattern: Centralized configuration management with audit trail
--
-- Tables:
--   - service_configs: Current configuration for each service
--   - config_audit_log: Complete history of configuration changes
--
-- Security:
--   - Row-level security for multi-tenant support (future)
--   - Audit trail for compliance and debugging
-- =====================================================================

\c suho_trading;

-- Set search path
SET search_path TO public;

-- =====================================================================
-- SERVICE CONFIGS TABLE
-- =====================================================================
-- Stores current operational configuration for each microservice
-- Uses JSONB for flexible schema-less config storage

CREATE TABLE IF NOT EXISTS service_configs (
    -- Primary identifier
    service_name VARCHAR(100) PRIMARY KEY,

    -- Configuration data (flexible JSONB structure)
    config_json JSONB NOT NULL,

    -- Version tracking
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    updated_by VARCHAR(100) DEFAULT 'system',

    -- Metadata
    description TEXT,
    tags TEXT[], -- For categorization (e.g., ['data-ingestion', 'historical'])

    -- Validation
    schema_version VARCHAR(20) DEFAULT '1.0.0',
    validated BOOLEAN DEFAULT true,

    -- Status
    active BOOLEAN DEFAULT true,

    -- Constraints
    CONSTRAINT valid_service_name CHECK (service_name ~ '^[a-z0-9-]+$'),
    CONSTRAINT valid_config_json CHECK (jsonb_typeof(config_json) = 'object')
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_service_configs_updated_at
ON service_configs(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_service_configs_active
ON service_configs(active) WHERE active = true;

CREATE INDEX IF NOT EXISTS idx_service_configs_tags
ON service_configs USING GIN(tags);

-- JSONB indexes for config queries
CREATE INDEX IF NOT EXISTS idx_service_configs_config_json
ON service_configs USING GIN(config_json);

-- Comment on table
COMMENT ON TABLE service_configs IS 'Centralized storage for microservice operational configurations';
COMMENT ON COLUMN service_configs.service_name IS 'Unique service identifier (e.g., polygon-historical-downloader)';
COMMENT ON COLUMN service_configs.config_json IS 'JSONB configuration data with flexible schema';
COMMENT ON COLUMN service_configs.version IS 'Semantic version of configuration (e.g., 1.2.3)';
COMMENT ON COLUMN service_configs.tags IS 'Tags for categorization and filtering';

-- =====================================================================
-- CONFIG AUDIT LOG TABLE
-- =====================================================================
-- Complete audit trail of all configuration changes
-- Enables debugging, rollback, and compliance

CREATE TABLE IF NOT EXISTS config_audit_log (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,

    -- Service reference
    service_name VARCHAR(100) NOT NULL,

    -- Configuration snapshot
    config_json JSONB NOT NULL,
    version VARCHAR(20) NOT NULL,

    -- Change metadata
    action VARCHAR(20) NOT NULL, -- 'created', 'updated', 'deleted', 'rollback'
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Change details
    change_reason TEXT,
    change_diff JSONB, -- JSON diff of what changed

    -- Request metadata
    request_ip INET,
    request_user_agent TEXT,

    -- Correlation
    correlation_id UUID,

    -- Constraints
    CONSTRAINT valid_action CHECK (action IN ('created', 'updated', 'deleted', 'rollback'))
);

-- Indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_config_audit_service
ON config_audit_log(service_name, changed_at DESC);

CREATE INDEX IF NOT EXISTS idx_config_audit_changed_at
ON config_audit_log(changed_at DESC);

CREATE INDEX IF NOT EXISTS idx_config_audit_changed_by
ON config_audit_log(changed_by, changed_at DESC);

CREATE INDEX IF NOT EXISTS idx_config_audit_action
ON config_audit_log(action, changed_at DESC);

CREATE INDEX IF NOT EXISTS idx_config_audit_correlation
ON config_audit_log(correlation_id) WHERE correlation_id IS NOT NULL;

-- Comment on table
COMMENT ON TABLE config_audit_log IS 'Complete audit trail of all configuration changes';
COMMENT ON COLUMN config_audit_log.change_diff IS 'JSON diff showing exactly what changed';
COMMENT ON COLUMN config_audit_log.correlation_id IS 'Links related changes across multiple services';

-- =====================================================================
-- TRIGGER FUNCTION - AUTO UPDATE TIMESTAMP
-- =====================================================================
-- Automatically update updated_at timestamp on row modification

CREATE OR REPLACE FUNCTION update_service_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_service_configs_updated_at
BEFORE UPDATE ON service_configs
FOR EACH ROW
EXECUTE FUNCTION update_service_config_timestamp();

-- =====================================================================
-- TRIGGER FUNCTION - AUTO AUDIT LOG
-- =====================================================================
-- Automatically log all configuration changes to audit table

CREATE OR REPLACE FUNCTION log_service_config_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Log INSERT
    IF TG_OP = 'INSERT' THEN
        INSERT INTO config_audit_log (
            service_name,
            config_json,
            version,
            action,
            changed_by,
            change_reason
        ) VALUES (
            NEW.service_name,
            NEW.config_json,
            NEW.version,
            'created',
            NEW.created_by,
            'Initial configuration'
        );
        RETURN NEW;
    END IF;

    -- Log UPDATE
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO config_audit_log (
            service_name,
            config_json,
            version,
            action,
            changed_by,
            change_reason
        ) VALUES (
            NEW.service_name,
            NEW.config_json,
            NEW.version,
            'updated',
            NEW.updated_by,
            'Configuration updated'
        );
        RETURN NEW;
    END IF;

    -- Log DELETE
    IF TG_OP = 'DELETE' THEN
        INSERT INTO config_audit_log (
            service_name,
            config_json,
            version,
            action,
            changed_by,
            change_reason
        ) VALUES (
            OLD.service_name,
            OLD.config_json,
            OLD.version,
            'deleted',
            OLD.updated_by,
            'Configuration deleted'
        );
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_service_configs_audit
AFTER INSERT OR UPDATE OR DELETE ON service_configs
FOR EACH ROW
EXECUTE FUNCTION log_service_config_change();

-- =====================================================================
-- HELPER FUNCTIONS
-- =====================================================================

-- Get config history for a service
CREATE OR REPLACE FUNCTION get_config_history(
    p_service_name VARCHAR(100),
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    version VARCHAR(20),
    action VARCHAR(20),
    changed_by VARCHAR(100),
    changed_at TIMESTAMPTZ,
    config_json JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cal.version,
        cal.action,
        cal.changed_by,
        cal.changed_at,
        cal.config_json
    FROM config_audit_log cal
    WHERE cal.service_name = p_service_name
    ORDER BY cal.changed_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_config_history IS 'Retrieve configuration change history for a service';

-- Rollback to previous config version
CREATE OR REPLACE FUNCTION rollback_config(
    p_service_name VARCHAR(100),
    p_version VARCHAR(20),
    p_rolled_back_by VARCHAR(100) DEFAULT 'system'
)
RETURNS BOOLEAN AS $$
DECLARE
    v_config_json JSONB;
    v_found BOOLEAN;
BEGIN
    -- Find the target version in history
    SELECT config_json INTO v_config_json
    FROM config_audit_log
    WHERE service_name = p_service_name
      AND version = p_version
    ORDER BY changed_at DESC
    LIMIT 1;

    GET DIAGNOSTICS v_found = ROW_COUNT;

    IF NOT v_found THEN
        RAISE EXCEPTION 'Version % not found for service %', p_version, p_service_name;
    END IF;

    -- Update current config with historical version
    UPDATE service_configs
    SET
        config_json = v_config_json,
        version = p_version || '-rollback',
        updated_by = p_rolled_back_by
    WHERE service_name = p_service_name;

    -- Log rollback action
    INSERT INTO config_audit_log (
        service_name,
        config_json,
        version,
        action,
        changed_by,
        change_reason
    ) VALUES (
        p_service_name,
        v_config_json,
        p_version || '-rollback',
        'rollback',
        p_rolled_back_by,
        'Rolled back to version ' || p_version
    );

    RETURN true;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION rollback_config IS 'Rollback service configuration to a previous version';

-- =====================================================================
-- SEED DATA - INITIAL CONFIGURATIONS
-- =====================================================================
-- Default configurations for pilot services

-- Polygon Historical Downloader
INSERT INTO service_configs (service_name, config_json, version, description, tags, created_by)
VALUES (
    'polygon-historical-downloader',
    '{
        "operational": {
            "gap_check_interval_hours": 1,
            "batch_size": 100,
            "max_retries": 3,
            "retry_delay_seconds": 10,
            "verification_enabled": true
        },
        "download": {
            "start_date": "today-7days",
            "end_date": "today",
            "granularity": {
                "trading_pairs": {"timeframe": "minute", "multiplier": 5},
                "analysis_pairs": {"timeframe": "minute", "multiplier": 5},
                "confirmation_pairs": {"timeframe": "minute", "multiplier": 5}
            }
        },
        "features": {
            "enable_gap_verification": true,
            "enable_period_tracker": true,
            "enable_auto_backfill": true
        }
    }'::jsonb,
    '1.0.0',
    'Polygon.io historical data downloader with gap filling',
    ARRAY['data-ingestion', 'historical', 'polygon'],
    'system'
) ON CONFLICT (service_name) DO NOTHING;

-- Tick Aggregator
INSERT INTO service_configs (service_name, config_json, version, description, tags, created_by)
VALUES (
    'tick-aggregator',
    '{
        "aggregation": {
            "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "min_ticks_per_candle": 1,
            "publish_interval_seconds": 1
        },
        "processing": {
            "batch_size": 1000,
            "buffer_timeout_seconds": 5,
            "max_concurrent_symbols": 50
        },
        "features": {
            "enable_volume_profile": true,
            "enable_imbalance_detection": true,
            "enable_liquidity_heatmap": false
        }
    }'::jsonb,
    '1.0.0',
    'Real-time tick aggregation to OHLCV candles',
    ARRAY['data-processing', 'real-time', 'aggregation'],
    'system'
) ON CONFLICT (service_name) DO NOTHING;

-- Data Bridge
INSERT INTO service_configs (service_name, config_json, version, description, tags, created_by)
VALUES (
    'data-bridge',
    '{
        "processing": {
            "batch_size": 1000,
            "buffer_timeout_seconds": 5,
            "max_concurrent_workers": 10
        },
        "validation": {
            "strict_mode": true,
            "drop_invalid_data": false,
            "log_validation_errors": true
        },
        "clickhouse": {
            "insert_batch_size": 10000,
            "insert_timeout_seconds": 30,
            "max_retries": 3
        },
        "features": {
            "enable_deduplication": true,
            "enable_compression": true,
            "enable_metrics": true
        }
    }'::jsonb,
    '1.0.0',
    'Data bridge between NATS and ClickHouse',
    ARRAY['data-processing', 'bridge', 'clickhouse'],
    'system'
) ON CONFLICT (service_name) DO NOTHING;

-- =====================================================================
-- PERMISSIONS
-- =====================================================================

-- Grant permissions to service role
GRANT SELECT, INSERT, UPDATE, DELETE ON service_configs TO suho_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON config_audit_log TO suho_service;
GRANT USAGE ON SEQUENCE config_audit_log_id_seq TO suho_service;

-- Grant read-only access
GRANT SELECT ON service_configs TO suho_readonly;
GRANT SELECT ON config_audit_log TO suho_readonly;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION get_config_history(VARCHAR, INTEGER) TO suho_service;
GRANT EXECUTE ON FUNCTION rollback_config(VARCHAR, VARCHAR, VARCHAR) TO suho_service;
GRANT EXECUTE ON FUNCTION get_config_history(VARCHAR, INTEGER) TO suho_readonly;

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================

-- Verify tables created
DO $$
BEGIN
    RAISE NOTICE '=== Service Config Tables Created ===';
    RAISE NOTICE 'service_configs: % rows', (SELECT COUNT(*) FROM service_configs);
    RAISE NOTICE 'config_audit_log: % rows', (SELECT COUNT(*) FROM config_audit_log);
    RAISE NOTICE '=== Seed Data Loaded ===';
    RAISE NOTICE 'Pilot services: %', (SELECT array_agg(service_name) FROM service_configs);
END $$;

COMMIT;
