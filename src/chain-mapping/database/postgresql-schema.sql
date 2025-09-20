-- ================================================================
-- Embedded Chain Mapping System - PostgreSQL Schema
-- ================================================================
-- This schema supports the storage of chain definitions, configuration,
-- and metadata for the embedded chain mapping system.
--
-- Schema Design Principles:
-- - Normalized structure for efficient storage and querying
-- - JSONB for flexible metadata storage
-- - Proper indexes for performance
-- - Foreign key constraints for data integrity
-- - Audit trails for change tracking
-- ================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ================================================================
-- Core Tables
-- ================================================================

-- Chain definitions and metadata
CREATE TABLE chain_definitions (
    id VARCHAR(10) PRIMARY KEY,              -- A1, B1, C1, etc.
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (
        category IN (
            'data_flow',
            'service_communication',
            'user_experience',
            'ai_ml_processing',
            'infrastructure'
        )
    ),
    description TEXT,
    status VARCHAR(20) DEFAULT 'unknown' CHECK (
        status IN ('healthy', 'degraded', 'failed', 'unknown')
    ),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    version INTEGER DEFAULT 1,

    -- Constraints
    CONSTRAINT chain_id_format CHECK (id ~ '^[A-E][1-9][0-9]*$'),
    CONSTRAINT name_not_empty CHECK (LENGTH(TRIM(name)) > 0)
);

-- Add comments for documentation
COMMENT ON TABLE chain_definitions IS 'Main chain definitions with metadata and status';
COMMENT ON COLUMN chain_definitions.id IS 'Chain identifier following pattern [A-E][1-9]+';
COMMENT ON COLUMN chain_definitions.category IS 'Chain category for classification';
COMMENT ON COLUMN chain_definitions.metadata IS 'Flexible JSON storage for additional chain properties';

-- Chain nodes (components/services within a chain)
CREATE TABLE chain_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id VARCHAR(10) NOT NULL REFERENCES chain_definitions(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    node_type VARCHAR(50) NOT NULL CHECK (
        node_type IN (
            'service',
            'api_endpoint',
            'database',
            'cache',
            'queue',
            'ai_model',
            'websocket',
            'external_api'
        )
    ),
    service_name VARCHAR(100),
    component_name VARCHAR(200),
    config JSONB DEFAULT '{}',
    position JSONB DEFAULT '{}',
    health_check_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_node_per_chain UNIQUE(chain_id, node_id),
    CONSTRAINT node_id_not_empty CHECK (LENGTH(TRIM(node_id)) > 0),
    CONSTRAINT service_name_not_empty CHECK (
        service_name IS NULL OR LENGTH(TRIM(service_name)) > 0
    )
);

COMMENT ON TABLE chain_nodes IS 'Individual nodes/components within chains';
COMMENT ON COLUMN chain_nodes.node_id IS 'Unique identifier within the chain';
COMMENT ON COLUMN chain_nodes.config IS 'Node-specific configuration as JSON';
COMMENT ON COLUMN chain_nodes.position IS 'UI positioning information for graph visualization';
COMMENT ON COLUMN chain_nodes.health_check_config IS 'Health check configuration for this node';

-- Chain edges (connections between nodes)
CREATE TABLE chain_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id VARCHAR(10) NOT NULL REFERENCES chain_definitions(id) ON DELETE CASCADE,
    edge_id VARCHAR(100) NOT NULL,
    source_node VARCHAR(100) NOT NULL,
    target_node VARCHAR(100) NOT NULL,
    edge_type VARCHAR(50) NOT NULL CHECK (
        edge_type IN (
            'http_request',
            'websocket_message',
            'database_query',
            'cache_operation',
            'event_publish',
            'ai_inference'
        )
    ),
    condition_expr TEXT,
    latency_sla INTEGER CHECK (latency_sla > 0),
    retry_policy JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_edge_per_chain UNIQUE(chain_id, edge_id),
    CONSTRAINT edge_id_not_empty CHECK (LENGTH(TRIM(edge_id)) > 0),
    CONSTRAINT source_target_different CHECK (source_node != target_node),

    -- Foreign key constraints to ensure nodes exist
    CONSTRAINT fk_source_node
        FOREIGN KEY (chain_id, source_node)
        REFERENCES chain_nodes(chain_id, node_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_target_node
        FOREIGN KEY (chain_id, target_node)
        REFERENCES chain_nodes(chain_id, node_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE chain_edges IS 'Connections between nodes in chains';
COMMENT ON COLUMN chain_edges.latency_sla IS 'Expected latency in milliseconds';
COMMENT ON COLUMN chain_edges.retry_policy IS 'Retry configuration as JSON';
COMMENT ON COLUMN chain_edges.condition_expr IS 'Optional condition for edge execution';

-- Chain dependencies (external dependencies)
CREATE TABLE chain_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id VARCHAR(10) NOT NULL REFERENCES chain_definitions(id) ON DELETE CASCADE,
    dependency_id VARCHAR(100) NOT NULL,
    dependency_type VARCHAR(50) NOT NULL CHECK (
        dependency_type IN (
            'service',
            'database',
            'external_api',
            'cache',
            'queue',
            'configuration'
        )
    ),
    target_identifier VARCHAR(200) NOT NULL,
    criticality VARCHAR(20) DEFAULT 'medium' CHECK (
        criticality IN ('critical', 'high', 'medium', 'low')
    ),
    fallback_strategy TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_dependency_per_chain UNIQUE(chain_id, dependency_id),
    CONSTRAINT dependency_id_not_empty CHECK (LENGTH(TRIM(dependency_id)) > 0),
    CONSTRAINT target_not_empty CHECK (LENGTH(TRIM(target_identifier)) > 0)
);

COMMENT ON TABLE chain_dependencies IS 'External dependencies for chains';
COMMENT ON COLUMN chain_dependencies.target_identifier IS 'Identifier for the dependency target';
COMMENT ON COLUMN chain_dependencies.fallback_strategy IS 'Strategy to handle dependency failures';

-- ================================================================
-- Monitoring and Health Tables
-- ================================================================

-- Chain health monitoring configuration
CREATE TABLE chain_monitoring_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id VARCHAR(10) NOT NULL REFERENCES chain_definitions(id) ON DELETE CASCADE,
    monitoring_enabled BOOLEAN DEFAULT true,
    check_interval INTEGER DEFAULT 60 CHECK (check_interval BETWEEN 10 AND 3600),
    alert_thresholds JSONB DEFAULT '{}',
    notification_config JSONB DEFAULT '{}',
    escalation_rules JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_monitoring_per_chain UNIQUE(chain_id)
);

COMMENT ON TABLE chain_monitoring_config IS 'Monitoring configuration for each chain';
COMMENT ON COLUMN chain_monitoring_config.check_interval IS 'Health check interval in seconds';
COMMENT ON COLUMN chain_monitoring_config.alert_thresholds IS 'Alerting thresholds as JSON';
COMMENT ON COLUMN chain_monitoring_config.notification_config IS 'Notification settings as JSON';

-- Chain discovery results
CREATE TABLE chain_discovery_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discovery_method VARCHAR(50) NOT NULL CHECK (
        discovery_method IN ('ast_parser', 'runtime_trace', 'service_mesh', 'manual')
    ),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_name VARCHAR(100),
    discovery_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0.00 AND 1.00),
    reviewed BOOLEAN DEFAULT false,
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (
        review_status IN ('pending', 'approved', 'rejected', 'needs_modification')
    ),
    chain_id VARCHAR(10) REFERENCES chain_definitions(id) ON DELETE SET NULL,
    reviewer VARCHAR(100),
    review_notes TEXT,
    reviewed_at TIMESTAMP
);

COMMENT ON TABLE chain_discovery_results IS 'Results from automated chain discovery processes';
COMMENT ON COLUMN chain_discovery_results.confidence_score IS 'Confidence in discovery accuracy (0.00-1.00)';
COMMENT ON COLUMN chain_discovery_results.discovery_data IS 'Detailed discovery data as JSON';

-- Chain change history for audit trail
CREATE TABLE chain_change_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id VARCHAR(10) NOT NULL REFERENCES chain_definitions(id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL CHECK (
        change_type IN (
            'created', 'updated', 'deleted', 'status_changed',
            'nodes_modified', 'edges_modified', 'dependencies_modified'
        )
    ),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100),
    change_description TEXT,
    old_values JSONB,
    new_values JSONB,
    version_before INTEGER,
    version_after INTEGER
);

COMMENT ON TABLE chain_change_history IS 'Audit trail of all chain modifications';
COMMENT ON COLUMN chain_change_history.old_values IS 'Previous values before change';
COMMENT ON COLUMN chain_change_history.new_values IS 'New values after change';

-- ================================================================
-- Analysis and Optimization Tables
-- ================================================================

-- Chain analysis results
CREATE TABLE chain_analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id VARCHAR(10) NOT NULL REFERENCES chain_definitions(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL CHECK (
        analysis_type IN (
            'impact_analysis', 'optimization', 'pattern_detection',
            'bottleneck_analysis', 'performance_prediction'
        )
    ),
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0.00 AND 1.00),
    recommendations JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'completed' CHECK (
        status IN ('running', 'completed', 'failed', 'cancelled')
    ),
    execution_time_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE chain_analysis_results IS 'Results from various chain analysis operations';
COMMENT ON COLUMN chain_analysis_results.analysis_data IS 'Detailed analysis results as JSON';
COMMENT ON COLUMN chain_analysis_results.recommendations IS 'Generated recommendations as JSON array';

-- Chain patterns detected across multiple chains
CREATE TABLE chain_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    pattern_type VARCHAR(50) NOT NULL CHECK (
        pattern_type IN ('structural', 'behavioral', 'performance', 'error')
    ),
    frequency INTEGER DEFAULT 1,
    optimization_potential DECIMAL(3,2) CHECK (optimization_potential BETWEEN 0.00 AND 1.00),
    pattern_definition JSONB NOT NULL,
    affected_chains JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chain_patterns IS 'Patterns detected across multiple chains';
COMMENT ON COLUMN chain_patterns.frequency IS 'Number of chains exhibiting this pattern';
COMMENT ON COLUMN chain_patterns.pattern_definition IS 'Technical definition of the pattern';
COMMENT ON COLUMN chain_patterns.affected_chains IS 'Array of chain IDs exhibiting this pattern';

-- ================================================================
-- Indexes for Performance
-- ================================================================

-- Primary query indexes
CREATE INDEX idx_chain_definitions_category ON chain_definitions(category);
CREATE INDEX idx_chain_definitions_status ON chain_definitions(status);
CREATE INDEX idx_chain_definitions_created_at ON chain_definitions(created_at);

-- Node and edge indexes
CREATE INDEX idx_chain_nodes_service ON chain_nodes(service_name);
CREATE INDEX idx_chain_nodes_type ON chain_nodes(node_type);
CREATE INDEX idx_chain_nodes_chain_service ON chain_nodes(chain_id, service_name);

CREATE INDEX idx_chain_edges_type ON chain_edges(edge_type);
CREATE INDEX idx_chain_edges_source_target ON chain_edges(chain_id, source_node, target_node);

-- Dependency indexes
CREATE INDEX idx_chain_dependencies_type ON chain_dependencies(dependency_type);
CREATE INDEX idx_chain_dependencies_criticality ON chain_dependencies(criticality);

-- Discovery and monitoring indexes
CREATE INDEX idx_discovery_results_method ON chain_discovery_results(discovery_method);
CREATE INDEX idx_discovery_results_service ON chain_discovery_results(service_name);
CREATE INDEX idx_discovery_results_status ON chain_discovery_results(review_status);
CREATE INDEX idx_discovery_results_discovered_at ON chain_discovery_results(discovered_at);

CREATE INDEX idx_monitoring_config_enabled ON chain_monitoring_config(monitoring_enabled);

-- History and analysis indexes
CREATE INDEX idx_change_history_chain_time ON chain_change_history(chain_id, changed_at);
CREATE INDEX idx_change_history_type ON chain_change_history(change_type);

CREATE INDEX idx_analysis_results_chain_type ON chain_analysis_results(chain_id, analysis_type);
CREATE INDEX idx_analysis_results_timestamp ON chain_analysis_results(analysis_timestamp);

CREATE INDEX idx_patterns_type ON chain_patterns(pattern_type);
CREATE INDEX idx_patterns_frequency ON chain_patterns(frequency);

-- JSONB indexes for efficient JSON queries
CREATE INDEX idx_chain_definitions_metadata_gin ON chain_definitions USING GIN (metadata);
CREATE INDEX idx_chain_nodes_config_gin ON chain_nodes USING GIN (config);
CREATE INDEX idx_discovery_data_gin ON chain_discovery_results USING GIN (discovery_data);
CREATE INDEX idx_analysis_data_gin ON chain_analysis_results USING GIN (analysis_data);

-- ================================================================
-- Triggers for Automation
-- ================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_chain_definitions_updated_at
    BEFORE UPDATE ON chain_definitions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monitoring_config_updated_at
    BEFORE UPDATE ON chain_monitoring_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically increment version on updates
CREATE OR REPLACE FUNCTION increment_chain_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = COALESCE(OLD.version, 0) + 1;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for version increment
CREATE TRIGGER increment_chain_definitions_version
    BEFORE UPDATE ON chain_definitions
    FOR EACH ROW EXECUTE FUNCTION increment_chain_version();

-- Function to log changes to chain_change_history
CREATE OR REPLACE FUNCTION log_chain_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO chain_change_history (
            chain_id, change_type, change_description,
            new_values, version_after
        ) VALUES (
            NEW.id, 'created', 'Chain definition created',
            to_jsonb(NEW), NEW.version
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO chain_change_history (
            chain_id, change_type, change_description,
            old_values, new_values, version_before, version_after
        ) VALUES (
            NEW.id, 'updated', 'Chain definition updated',
            to_jsonb(OLD), to_jsonb(NEW), OLD.version, NEW.version
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO chain_change_history (
            chain_id, change_type, change_description,
            old_values, version_before
        ) VALUES (
            OLD.id, 'deleted', 'Chain definition deleted',
            to_jsonb(OLD), OLD.version
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Trigger for change logging
CREATE TRIGGER log_chain_definitions_changes
    AFTER INSERT OR UPDATE OR DELETE ON chain_definitions
    FOR EACH ROW EXECUTE FUNCTION log_chain_changes();

-- ================================================================
-- Views for Common Queries
-- ================================================================

-- View for chain overview with node and edge counts
CREATE VIEW chain_overview AS
SELECT
    cd.id,
    cd.name,
    cd.category,
    cd.status,
    cd.created_at,
    cd.updated_at,
    cd.version,
    COUNT(DISTINCT cn.id) as node_count,
    COUNT(DISTINCT ce.id) as edge_count,
    COUNT(DISTINCT cdep.id) as dependency_count,
    CASE
        WHEN cmc.monitoring_enabled THEN 'enabled'
        ELSE 'disabled'
    END as monitoring_status
FROM chain_definitions cd
LEFT JOIN chain_nodes cn ON cd.id = cn.chain_id
LEFT JOIN chain_edges ce ON cd.id = ce.chain_id
LEFT JOIN chain_dependencies cdep ON cd.id = cdep.chain_id
LEFT JOIN chain_monitoring_config cmc ON cd.id = cmc.chain_id
GROUP BY cd.id, cd.name, cd.category, cd.status, cd.created_at,
         cd.updated_at, cd.version, cmc.monitoring_enabled;

COMMENT ON VIEW chain_overview IS 'Overview of all chains with counts and monitoring status';

-- View for chains by service involvement
CREATE VIEW chains_by_service AS
SELECT
    cn.service_name,
    COUNT(DISTINCT cn.chain_id) as chain_count,
    array_agg(DISTINCT cn.chain_id ORDER BY cn.chain_id) as involved_chains,
    array_agg(DISTINCT cd.category) as categories
FROM chain_nodes cn
JOIN chain_definitions cd ON cn.chain_id = cd.id
WHERE cn.service_name IS NOT NULL
GROUP BY cn.service_name
ORDER BY chain_count DESC;

COMMENT ON VIEW chains_by_service IS 'Chains grouped by service involvement';

-- View for unhealthy chains that need attention
CREATE VIEW unhealthy_chains AS
SELECT
    cd.id,
    cd.name,
    cd.category,
    cd.status,
    cd.updated_at,
    cmc.monitoring_enabled,
    cmc.check_interval
FROM chain_definitions cd
LEFT JOIN chain_monitoring_config cmc ON cd.id = cmc.chain_id
WHERE cd.status IN ('degraded', 'failed')
   OR (cmc.monitoring_enabled = false AND cd.status != 'unknown')
ORDER BY
    CASE cd.status
        WHEN 'failed' THEN 1
        WHEN 'degraded' THEN 2
        ELSE 3
    END,
    cd.updated_at DESC;

COMMENT ON VIEW unhealthy_chains IS 'Chains requiring attention due to health or monitoring issues';

-- ================================================================
-- Initial Data Setup
-- ================================================================

-- Insert default monitoring configuration for all existing chains
-- This will be handled by the application layer during migration

-- ================================================================
-- Performance Optimization Settings
-- ================================================================

-- Analyze tables for query planning
ANALYZE chain_definitions;
ANALYZE chain_nodes;
ANALYZE chain_edges;
ANALYZE chain_dependencies;
ANALYZE chain_monitoring_config;
ANALYZE chain_discovery_results;

-- ================================================================
-- Security and Permissions
-- ================================================================

-- Create role for chain mapping service
CREATE ROLE chain_mapping_service;

-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO chain_mapping_service;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO chain_mapping_service;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO chain_mapping_service;

-- Create read-only role for monitoring and reporting
CREATE ROLE chain_mapping_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chain_mapping_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO chain_mapping_reader;

-- ================================================================
-- Maintenance and Monitoring
-- ================================================================

-- Function to clean up old discovery results
CREATE OR REPLACE FUNCTION cleanup_old_discovery_results(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chain_discovery_results
    WHERE discovered_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep
      AND reviewed = true
      AND chain_id IS NOT NULL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old change history
CREATE OR REPLACE FUNCTION cleanup_old_change_history(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chain_change_history
    WHERE changed_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get database statistics
CREATE OR REPLACE FUNCTION get_chain_mapping_stats()
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT,
    table_size TEXT,
    index_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname||'.'||tablename as table_name,
        n_tup_ins + n_tup_upd as row_count,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
        pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size
    FROM pg_stat_user_tables
    WHERE tablename LIKE 'chain_%'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- Schema Validation
-- ================================================================

-- Function to validate chain definition consistency
CREATE OR REPLACE FUNCTION validate_chain_consistency(p_chain_id VARCHAR(10))
RETURNS TABLE (
    validation_type TEXT,
    is_valid BOOLEAN,
    message TEXT
) AS $$
BEGIN
    -- Check if all edge nodes exist
    RETURN QUERY
    SELECT
        'edge_node_existence'::TEXT,
        COUNT(*) = 0,
        CASE WHEN COUNT(*) = 0
            THEN 'All edge nodes exist'
            ELSE 'Found ' || COUNT(*) || ' edges with non-existent nodes'
        END
    FROM chain_edges ce
    LEFT JOIN chain_nodes cn_source ON ce.chain_id = cn_source.chain_id
        AND ce.source_node = cn_source.node_id
    LEFT JOIN chain_nodes cn_target ON ce.chain_id = cn_target.chain_id
        AND ce.target_node = cn_target.node_id
    WHERE ce.chain_id = p_chain_id
      AND (cn_source.id IS NULL OR cn_target.id IS NULL);

    -- Check for isolated nodes (no incoming or outgoing edges)
    RETURN QUERY
    SELECT
        'isolated_nodes'::TEXT,
        COUNT(*) = 0,
        CASE WHEN COUNT(*) = 0
            THEN 'No isolated nodes found'
            ELSE 'Found ' || COUNT(*) || ' isolated nodes'
        END
    FROM chain_nodes cn
    WHERE cn.chain_id = p_chain_id
      AND cn.node_id NOT IN (
          SELECT source_node FROM chain_edges WHERE chain_id = p_chain_id
          UNION
          SELECT target_node FROM chain_edges WHERE chain_id = p_chain_id
      );

    -- Check for circular dependencies
    RETURN QUERY
    WITH RECURSIVE chain_path AS (
        SELECT source_node, target_node, ARRAY[source_node, target_node] as path
        FROM chain_edges
        WHERE chain_id = p_chain_id

        UNION ALL

        SELECT cp.source_node, ce.target_node, cp.path || ce.target_node
        FROM chain_path cp
        JOIN chain_edges ce ON cp.target_node = ce.source_node
        WHERE ce.chain_id = p_chain_id
          AND NOT (ce.target_node = ANY(cp.path))
          AND array_length(cp.path, 1) < 50
    )
    SELECT
        'circular_dependencies'::TEXT,
        COUNT(*) = 0,
        CASE WHEN COUNT(*) = 0
            THEN 'No circular dependencies found'
            ELSE 'Found ' || COUNT(*) || ' potential circular dependencies'
        END
    FROM chain_path
    WHERE target_node = source_node;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- End of Schema Definition
-- ================================================================

-- Add final comment with schema version
COMMENT ON SCHEMA public IS 'Chain Mapping System Schema v1.0.0 - Supports 30 chains across 5 categories';