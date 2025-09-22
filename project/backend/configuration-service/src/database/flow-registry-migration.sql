-- Flow Registry Database Migration Script
-- This script creates all necessary tables and indexes for the FlowRegistry service
-- PostgreSQL database schema for flow-aware debugging

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Flow definitions table - Core flow definition storage
CREATE TABLE IF NOT EXISTS flow_definitions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('langgraph_workflow', 'ai_brain_validation', 'chain_mapping', 'custom')),
    version VARCHAR(20) NOT NULL,
    description TEXT,
    definition_json JSONB NOT NULL,
    parameters_json JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'deprecated', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    tags TEXT[],
    metadata_json JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT unique_flow_name_version UNIQUE(name, version),
    CONSTRAINT valid_flow_id CHECK (id ~ '^[a-zA-Z0-9_-]+$'),
    CONSTRAINT valid_version CHECK (version ~ '^\d+\.\d+\.\d+$')
);

-- Flow dependencies tracking - Manages flow dependencies and relationships
CREATE TABLE IF NOT EXISTS flow_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) NOT NULL REFERENCES flow_definitions(id) ON DELETE CASCADE,
    depends_on_flow_id VARCHAR(50) NOT NULL REFERENCES flow_definitions(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL CHECK (dependency_type IN ('prerequisite', 'parallel', 'conditional')),
    condition_json JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_flow_dependency UNIQUE(flow_id, depends_on_flow_id),
    CONSTRAINT no_self_dependency CHECK (flow_id != depends_on_flow_id)
);

-- Flow executions table - Tracks execution history and performance
CREATE TABLE IF NOT EXISTS flow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) NOT NULL REFERENCES flow_definitions(id) ON DELETE CASCADE,
    execution_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    parameters_json JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result_json JSONB,
    error_message TEXT,
    triggered_by VARCHAR(100),
    execution_context JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT unique_execution_id UNIQUE(execution_id),
    CONSTRAINT valid_completion_time CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- Flow credentials table - Maps flows to required credentials
CREATE TABLE IF NOT EXISTS flow_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) NOT NULL REFERENCES flow_definitions(id) ON DELETE CASCADE,
    credential_key VARCHAR(100) NOT NULL,
    credential_type VARCHAR(50) NOT NULL CHECK (credential_type IN ('api_key', 'token', 'secret', 'oauth')),
    is_required BOOLEAN DEFAULT true,
    scope VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_flow_credential UNIQUE(flow_id, credential_key)
);

-- Flow execution metrics - Aggregated performance metrics for reporting
CREATE TABLE IF NOT EXISTS flow_execution_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) NOT NULL REFERENCES flow_definitions(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    avg_duration_seconds NUMERIC(10,2),
    min_duration_seconds NUMERIC(10,2),
    max_duration_seconds NUMERIC(10,2),
    error_rate NUMERIC(5,2), -- Percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_flow_metrics_date UNIQUE(flow_id, metric_date),
    CONSTRAINT valid_execution_counts CHECK (
        total_executions >= 0 AND
        successful_executions >= 0 AND
        failed_executions >= 0 AND
        successful_executions + failed_executions <= total_executions
    )
);

-- Flow audit log - Track all changes to flow definitions
CREATE TABLE IF NOT EXISTS flow_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN ('created', 'updated', 'archived', 'restored', 'executed')),
    changed_by VARCHAR(100) NOT NULL,
    changes_json JSONB,
    old_values_json JSONB,
    new_values_json JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,

    -- Note: No foreign key to flow_definitions to preserve audit trail even after deletion
    CONSTRAINT valid_audit_action CHECK (action IS NOT NULL AND action != '')
);

-- Performance indexes for query optimization
-- Primary performance indexes
CREATE INDEX IF NOT EXISTS idx_flow_definitions_type ON flow_definitions(type);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_status ON flow_definitions(status);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_created_by ON flow_definitions(created_by);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_created_at ON flow_definitions(created_at);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_updated_at ON flow_definitions(updated_at);

-- Tag search optimization
CREATE INDEX IF NOT EXISTS idx_flow_definitions_tags ON flow_definitions USING GIN(tags);

-- JSON search optimization
CREATE INDEX IF NOT EXISTS idx_flow_definitions_definition ON flow_definitions USING GIN(definition_json);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_metadata ON flow_definitions USING GIN(metadata_json);

-- Flow execution indexes
CREATE INDEX IF NOT EXISTS idx_flow_executions_flow_id ON flow_executions(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_executions_status ON flow_executions(status);
CREATE INDEX IF NOT EXISTS idx_flow_executions_started_at ON flow_executions(started_at);
CREATE INDEX IF NOT EXISTS idx_flow_executions_completed_at ON flow_executions(completed_at);
CREATE INDEX IF NOT EXISTS idx_flow_executions_triggered_by ON flow_executions(triggered_by);
CREATE INDEX IF NOT EXISTS idx_flow_executions_execution_id ON flow_executions(execution_id);

-- Execution performance analysis
CREATE INDEX IF NOT EXISTS idx_flow_executions_duration ON flow_executions((EXTRACT(EPOCH FROM (completed_at - started_at)))) WHERE completed_at IS NOT NULL;

-- Flow dependency indexes
CREATE INDEX IF NOT EXISTS idx_flow_dependencies_flow_id ON flow_dependencies(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_dependencies_depends_on ON flow_dependencies(depends_on_flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_dependencies_type ON flow_dependencies(dependency_type);

-- Compound index for dependency resolution
CREATE INDEX IF NOT EXISTS idx_flow_dependencies_flow_type ON flow_dependencies(flow_id, dependency_type);

-- Flow credentials indexes
CREATE INDEX IF NOT EXISTS idx_flow_credentials_flow_id ON flow_credentials(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_credentials_type ON flow_credentials(credential_type);
CREATE INDEX IF NOT EXISTS idx_flow_credentials_required ON flow_credentials(is_required);

-- Metrics indexes
CREATE INDEX IF NOT EXISTS idx_flow_metrics_flow_id ON flow_execution_metrics(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_metrics_date ON flow_execution_metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_flow_metrics_updated ON flow_execution_metrics(updated_at);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_flow_audit_flow_id ON flow_audit_log(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_audit_action ON flow_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_flow_audit_timestamp ON flow_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_flow_audit_changed_by ON flow_audit_log(changed_by);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_flow_definitions_type_status ON flow_definitions(type, status);
CREATE INDEX IF NOT EXISTS idx_flow_executions_flow_status ON flow_executions(flow_id, status);
CREATE INDEX IF NOT EXISTS idx_flow_executions_status_started ON flow_executions(status, started_at);

-- Partial indexes for active flows (most commonly queried)
CREATE INDEX IF NOT EXISTS idx_flow_definitions_active ON flow_definitions(created_at, updated_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_flow_executions_recent ON flow_executions(flow_id, started_at DESC) WHERE started_at > CURRENT_TIMESTAMP - INTERVAL '30 days';

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_flow_definitions_updated_at
    BEFORE UPDATE ON flow_definitions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flow_metrics_updated_at
    BEFORE UPDATE ON flow_execution_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically update execution metrics
CREATE OR REPLACE FUNCTION update_flow_execution_metrics()
RETURNS TRIGGER AS $$
DECLARE
    duration_seconds NUMERIC;
BEGIN
    -- Only process completed or failed executions
    IF NEW.status IN ('completed', 'failed') AND OLD.status = 'running' THEN
        -- Calculate duration
        duration_seconds := EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at));

        -- Insert or update metrics
        INSERT INTO flow_execution_metrics (
            flow_id,
            metric_date,
            total_executions,
            successful_executions,
            failed_executions,
            avg_duration_seconds,
            min_duration_seconds,
            max_duration_seconds,
            error_rate
        )
        VALUES (
            NEW.flow_id,
            CURRENT_DATE,
            1,
            CASE WHEN NEW.status = 'completed' THEN 1 ELSE 0 END,
            CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
            duration_seconds,
            duration_seconds,
            duration_seconds,
            CASE WHEN NEW.status = 'failed' THEN 100.0 ELSE 0.0 END
        )
        ON CONFLICT (flow_id, metric_date) DO UPDATE SET
            total_executions = flow_execution_metrics.total_executions + 1,
            successful_executions = flow_execution_metrics.successful_executions +
                CASE WHEN NEW.status = 'completed' THEN 1 ELSE 0 END,
            failed_executions = flow_execution_metrics.failed_executions +
                CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
            avg_duration_seconds = (
                (flow_execution_metrics.avg_duration_seconds * flow_execution_metrics.total_executions + duration_seconds) /
                (flow_execution_metrics.total_executions + 1)
            ),
            min_duration_seconds = LEAST(flow_execution_metrics.min_duration_seconds, duration_seconds),
            max_duration_seconds = GREATEST(flow_execution_metrics.max_duration_seconds, duration_seconds),
            error_rate = (
                flow_execution_metrics.failed_executions + CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END
            ) * 100.0 / (flow_execution_metrics.total_executions + 1),
            updated_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update execution metrics
CREATE TRIGGER update_execution_metrics_trigger
    AFTER UPDATE ON flow_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_flow_execution_metrics();

-- Function to log flow definition changes
CREATE OR REPLACE FUNCTION log_flow_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO flow_audit_log (flow_id, action, changed_by, new_values_json)
        VALUES (NEW.id, 'created', NEW.created_by, row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO flow_audit_log (flow_id, action, changed_by, old_values_json, new_values_json, changes_json)
        VALUES (
            NEW.id,
            'updated',
            NEW.created_by,
            row_to_json(OLD),
            row_to_json(NEW),
            json_build_object(
                'status_changed', OLD.status != NEW.status,
                'definition_changed', OLD.definition_json != NEW.definition_json,
                'parameters_changed', OLD.parameters_json != NEW.parameters_json
            )
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO flow_audit_log (flow_id, action, changed_by, old_values_json)
        VALUES (OLD.id, 'deleted', 'system', row_to_json(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to log flow changes
CREATE TRIGGER log_flow_definition_changes
    AFTER INSERT OR UPDATE OR DELETE ON flow_definitions
    FOR EACH ROW
    EXECUTE FUNCTION log_flow_changes();

-- Views for common queries and reporting

-- Active flows with execution summary
CREATE OR REPLACE VIEW active_flows_summary AS
SELECT
    fd.id,
    fd.name,
    fd.type,
    fd.version,
    fd.description,
    fd.created_at,
    fd.updated_at,
    fd.tags,
    COUNT(fe.id) as total_executions,
    COUNT(CASE WHEN fe.status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN fe.status = 'failed' THEN 1 END) as failed_executions,
    COUNT(CASE WHEN fe.status = 'running' THEN 1 END) as running_executions,
    MAX(fe.started_at) as last_execution,
    AVG(EXTRACT(EPOCH FROM (fe.completed_at - fe.started_at))) as avg_duration_seconds
FROM flow_definitions fd
LEFT JOIN flow_executions fe ON fd.id = fe.flow_id
WHERE fd.status = 'active'
GROUP BY fd.id, fd.name, fd.type, fd.version, fd.description, fd.created_at, fd.updated_at, fd.tags;

-- Flow dependency tree view
CREATE OR REPLACE VIEW flow_dependency_tree AS
WITH RECURSIVE dependency_tree AS (
    -- Base case: flows with no dependencies
    SELECT
        fd.id,
        fd.name,
        fd.type,
        0 as depth,
        ARRAY[fd.id] as path,
        NULL::VARCHAR as parent_id
    FROM flow_definitions fd
    WHERE fd.status = 'active'
    AND NOT EXISTS (
        SELECT 1 FROM flow_dependencies dep
        WHERE dep.flow_id = fd.id
    )

    UNION ALL

    -- Recursive case: flows with dependencies
    SELECT
        fd.id,
        fd.name,
        fd.type,
        dt.depth + 1,
        dt.path || fd.id,
        dt.id as parent_id
    FROM flow_definitions fd
    JOIN flow_dependencies dep ON fd.id = dep.flow_id
    JOIN dependency_tree dt ON dep.depends_on_flow_id = dt.id
    WHERE fd.status = 'active'
    AND NOT (fd.id = ANY(dt.path)) -- Prevent infinite recursion
)
SELECT * FROM dependency_tree;

-- Recent execution performance view
CREATE OR REPLACE VIEW recent_execution_performance AS
SELECT
    fd.id as flow_id,
    fd.name as flow_name,
    fd.type as flow_type,
    COUNT(fe.id) as executions_last_24h,
    COUNT(CASE WHEN fe.status = 'completed' THEN 1 END) as successful_last_24h,
    COUNT(CASE WHEN fe.status = 'failed' THEN 1 END) as failed_last_24h,
    AVG(EXTRACT(EPOCH FROM (fe.completed_at - fe.started_at))) as avg_duration_last_24h,
    MAX(fe.started_at) as last_execution_time,
    CASE
        WHEN COUNT(fe.id) > 0 THEN
            (COUNT(CASE WHEN fe.status = 'completed' THEN 1 END) * 100.0 / COUNT(fe.id))
        ELSE 0
    END as success_rate_last_24h
FROM flow_definitions fd
LEFT JOIN flow_executions fe ON fd.id = fe.flow_id
    AND fe.started_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
WHERE fd.status = 'active'
GROUP BY fd.id, fd.name, fd.type
ORDER BY executions_last_24h DESC;

-- Flow credential requirements view
CREATE OR REPLACE VIEW flow_credential_requirements AS
SELECT
    fd.id as flow_id,
    fd.name as flow_name,
    fd.type as flow_type,
    fc.credential_key,
    fc.credential_type,
    fc.is_required,
    fc.scope,
    COUNT(fe.id) as recent_executions
FROM flow_definitions fd
JOIN flow_credentials fc ON fd.id = fc.flow_id
LEFT JOIN flow_executions fe ON fd.id = fe.flow_id
    AND fe.started_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
WHERE fd.status = 'active'
GROUP BY fd.id, fd.name, fd.type, fc.credential_key, fc.credential_type, fc.is_required, fc.scope
ORDER BY fd.name, fc.credential_type, fc.credential_key;

-- Comments for documentation
COMMENT ON TABLE flow_definitions IS 'Core flow definition storage with unified schema for all flow types';
COMMENT ON TABLE flow_dependencies IS 'Flow dependency tracking and relationship management';
COMMENT ON TABLE flow_executions IS 'Execution history and performance tracking for all flows';
COMMENT ON TABLE flow_credentials IS 'Credential requirements mapping for flows';
COMMENT ON TABLE flow_execution_metrics IS 'Aggregated performance metrics for reporting and monitoring';
COMMENT ON TABLE flow_audit_log IS 'Audit trail for all flow definition changes';

COMMENT ON VIEW active_flows_summary IS 'Summary of active flows with execution statistics';
COMMENT ON VIEW flow_dependency_tree IS 'Hierarchical view of flow dependencies';
COMMENT ON VIEW recent_execution_performance IS 'Recent execution performance metrics for monitoring';
COMMENT ON VIEW flow_credential_requirements IS 'Credential requirements for active flows';

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO flow_registry_user;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA public TO flow_registry_readonly;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO flow_registry_user;

-- Insert default flow types for validation
-- This can be used by applications for reference
CREATE TABLE IF NOT EXISTS flow_type_definitions (
    type VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    default_parameters JSONB DEFAULT '{}',
    required_credentials TEXT[],
    example_definition JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO flow_type_definitions (type, display_name, description, default_parameters, required_credentials, example_definition) VALUES
('langgraph_workflow', 'LangGraph Workflow', 'AI orchestration workflows using LangGraph framework', '{"timeout": 300, "retry_count": 3}', ARRAY['openai_api_key'], '{"nodes": [], "edges": []}'),
('ai_brain_validation', 'AI Brain Validation', 'Architecture validation flows for AI brain systems', '{"validation_level": "strict"}', ARRAY[], '{"validation_rules": [], "validator_type": "ai_brain"}'),
('chain_mapping', 'Chain Mapping', 'Blockchain and system integration chain mappings', '{"chain_timeout": 60}', ARRAY['rpc_endpoint'], '{"nodes": [], "edges": [], "chain_config": {}}'),
('custom', 'Custom Flow', 'User-defined custom flows', '{}', ARRAY[], '{"nodes": [], "edges": []}')
ON CONFLICT (type) DO NOTHING;

-- Migration completion log
INSERT INTO flow_audit_log (flow_id, action, changed_by, changes_json) VALUES
('system', 'migration', 'system', '{"action": "flow_registry_tables_created", "timestamp": "' || CURRENT_TIMESTAMP || '"}');

-- Success message
SELECT 'Flow Registry database migration completed successfully' as status;