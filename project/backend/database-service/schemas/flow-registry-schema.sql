-- Flow Registry Database Schema
-- Based on Flow Registry Integration Design documentation
-- PostgreSQL schema for centralized flow management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Flow definitions table
CREATE TABLE IF NOT EXISTS flow_definitions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('langgraph_workflow', 'ai_brain_validation', 'chain_mapping', 'custom')),
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    description TEXT,
    definition_json JSONB NOT NULL,
    parameters_json JSONB DEFAULT '{}',
    credentials_json JSONB DEFAULT '{}',
    environment_json JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'deprecated', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    tenant_id VARCHAR(50),
    category VARCHAR(50),
    tags TEXT[],
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),

    -- Constraints
    UNIQUE(name, version, tenant_id),
    CONSTRAINT flow_definition_valid_json CHECK (jsonb_typeof(definition_json) = 'object')
);

-- Flow dependencies tracking
CREATE TABLE IF NOT EXISTS flow_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    depends_on_flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL CHECK (dependency_type IN ('prerequisite', 'parallel', 'conditional', 'chain')),
    condition_expression TEXT,
    timeout_ms INTEGER DEFAULT 30000,
    retry_policy JSONB DEFAULT '{"maxRetries": 3, "backoffMs": 1000}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    -- Constraints
    UNIQUE(flow_id, depends_on_flow_id),
    CONSTRAINT no_self_dependency CHECK (flow_id != depends_on_flow_id)
);

-- Flow execution history
CREATE TABLE IF NOT EXISTS flow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    execution_id VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'timeout')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    input_parameters JSONB DEFAULT '{}',
    execution_context JSONB DEFAULT '{}',
    result_json JSONB,
    error_message TEXT,
    error_stack TEXT,
    triggered_by VARCHAR(100),
    execution_node VARCHAR(100),
    resource_usage JSONB DEFAULT '{}',

    -- Performance metrics
    cpu_time_ms INTEGER,
    memory_peak_mb INTEGER,
    io_operations INTEGER,

    CONSTRAINT valid_duration CHECK (
        (status IN ('completed', 'failed', 'cancelled', 'timeout') AND completed_at IS NOT NULL AND duration_ms IS NOT NULL) OR
        (status IN ('pending', 'running') AND completed_at IS NULL)
    )
);

-- Flow credential mappings
CREATE TABLE IF NOT EXISTS flow_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    credential_key VARCHAR(100) NOT NULL,
    credential_type VARCHAR(50) NOT NULL CHECK (credential_type IN ('api_key', 'token', 'secret', 'certificate', 'oauth')),
    is_required BOOLEAN DEFAULT true,
    is_encrypted BOOLEAN DEFAULT true,
    rotation_policy JSONB DEFAULT '{"enabled": false, "intervalDays": 90}',
    last_rotation TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    UNIQUE(flow_id, credential_key)
);

-- Flow performance metrics (aggregated)
CREATE TABLE IF NOT EXISTS flow_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    metric_date DATE DEFAULT CURRENT_DATE,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    avg_duration_ms FLOAT DEFAULT 0,
    p95_duration_ms FLOAT DEFAULT 0,
    p99_duration_ms FLOAT DEFAULT 0,
    min_duration_ms INTEGER DEFAULT 0,
    max_duration_ms INTEGER DEFAULT 0,
    avg_cpu_time_ms FLOAT DEFAULT 0,
    avg_memory_mb FLOAT DEFAULT 0,
    error_rate FLOAT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(flow_id, metric_date)
);

-- Flow chain mappings (for Chain Mapping flows)
CREATE TABLE IF NOT EXISTS flow_chains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    chain_id VARCHAR(50) NOT NULL,
    chain_name VARCHAR(255) NOT NULL,
    chain_category VARCHAR(50) CHECK (chain_category IN ('data_flow', 'service_communication', 'user_experience', 'ai_ml_processing', 'infrastructure')),
    nodes_json JSONB NOT NULL,
    edges_json JSONB NOT NULL,
    health_status VARCHAR(20) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'failed', 'unknown')),
    last_health_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(flow_id, chain_id),
    CONSTRAINT chain_valid_json CHECK (
        jsonb_typeof(nodes_json) = 'array' AND
        jsonb_typeof(edges_json) = 'array'
    )
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_flow_definitions_type ON flow_definitions(type);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_status ON flow_definitions(status);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_created_by ON flow_definitions(created_by);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_tenant_id ON flow_definitions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_category ON flow_definitions(category);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_tags ON flow_definitions USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_flow_definitions_created_at ON flow_definitions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_flow_dependencies_flow_id ON flow_dependencies(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_dependencies_depends_on ON flow_dependencies(depends_on_flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_dependencies_type ON flow_dependencies(dependency_type);

CREATE INDEX IF NOT EXISTS idx_flow_executions_flow_id ON flow_executions(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_executions_status ON flow_executions(status);
CREATE INDEX IF NOT EXISTS idx_flow_executions_started_at ON flow_executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_flow_executions_execution_id ON flow_executions(execution_id);
CREATE INDEX IF NOT EXISTS idx_flow_executions_triggered_by ON flow_executions(triggered_by);

CREATE INDEX IF NOT EXISTS idx_flow_credentials_flow_id ON flow_credentials(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_credentials_type ON flow_credentials(credential_type);

CREATE INDEX IF NOT EXISTS idx_flow_metrics_flow_id ON flow_metrics(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_metrics_date ON flow_metrics(metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_flow_chains_flow_id ON flow_chains(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_chains_category ON flow_chains(chain_category);
CREATE INDEX IF NOT EXISTS idx_flow_chains_health ON flow_chains(health_status);

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_flow_definitions_updated_at ON flow_definitions;
CREATE TRIGGER update_flow_definitions_updated_at
    BEFORE UPDATE ON flow_definitions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Trigger for automatic metrics calculation
CREATE OR REPLACE FUNCTION update_flow_metrics()
RETURNS TRIGGER AS $$
DECLARE
    flow_id_var VARCHAR(50);
    metric_date_var DATE;
BEGIN
    -- Get flow_id and date from the execution
    IF TG_OP = 'INSERT' THEN
        flow_id_var := NEW.flow_id;
        metric_date_var := DATE(NEW.started_at);
    ELSIF TG_OP = 'UPDATE' THEN
        flow_id_var := NEW.flow_id;
        metric_date_var := DATE(NEW.started_at);
    END IF;

    -- Update or insert metrics
    INSERT INTO flow_metrics (
        flow_id,
        metric_date,
        total_executions,
        successful_executions,
        failed_executions,
        avg_duration_ms,
        p95_duration_ms,
        p99_duration_ms,
        min_duration_ms,
        max_duration_ms,
        error_rate
    )
    SELECT
        flow_id_var,
        metric_date_var,
        COUNT(*) as total_executions,
        COUNT(*) FILTER (WHERE status = 'completed') as successful_executions,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_executions,
        AVG(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as avg_duration_ms,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as p95_duration_ms,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as p99_duration_ms,
        MIN(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as min_duration_ms,
        MAX(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as max_duration_ms,
        (COUNT(*) FILTER (WHERE status = 'failed')::FLOAT / COUNT(*)) as error_rate
    FROM flow_executions
    WHERE flow_id = flow_id_var
        AND DATE(started_at) = metric_date_var
    ON CONFLICT (flow_id, metric_date)
    DO UPDATE SET
        total_executions = EXCLUDED.total_executions,
        successful_executions = EXCLUDED.successful_executions,
        failed_executions = EXCLUDED.failed_executions,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        p95_duration_ms = EXCLUDED.p95_duration_ms,
        p99_duration_ms = EXCLUDED.p99_duration_ms,
        min_duration_ms = EXCLUDED.min_duration_ms,
        max_duration_ms = EXCLUDED.max_duration_ms,
        error_rate = EXCLUDED.error_rate,
        last_updated = CURRENT_TIMESTAMP;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_flow_metrics_trigger ON flow_executions;
CREATE TRIGGER update_flow_metrics_trigger
    AFTER INSERT OR UPDATE ON flow_executions
    FOR EACH ROW
    WHEN (NEW.status IN ('completed', 'failed', 'cancelled', 'timeout'))
    EXECUTE FUNCTION update_flow_metrics();

-- Views for common queries
CREATE OR REPLACE VIEW flow_summary AS
SELECT
    fd.id,
    fd.name,
    fd.type,
    fd.status,
    fd.created_at,
    fd.created_by,
    fd.tenant_id,
    fd.category,
    COALESCE(fm.total_executions, 0) as total_executions,
    COALESCE(fm.successful_executions, 0) as successful_executions,
    COALESCE(fm.failed_executions, 0) as failed_executions,
    COALESCE(fm.error_rate, 0) as error_rate,
    COALESCE(fm.avg_duration_ms, 0) as avg_duration_ms,
    (SELECT COUNT(*) FROM flow_dependencies WHERE flow_id = fd.id) as dependency_count,
    (SELECT COUNT(*) FROM flow_dependencies WHERE depends_on_flow_id = fd.id) as dependent_count
FROM flow_definitions fd
LEFT JOIN flow_metrics fm ON fd.id = fm.flow_id AND fm.metric_date = CURRENT_DATE;

CREATE OR REPLACE VIEW flow_health_status AS
SELECT
    fd.id,
    fd.name,
    fd.type,
    fd.status,
    CASE
        WHEN fm.error_rate > 0.1 THEN 'critical'
        WHEN fm.error_rate > 0.05 THEN 'warning'
        WHEN fm.avg_duration_ms > 10000 THEN 'slow'
        WHEN COALESCE(fm.total_executions, 0) = 0 THEN 'inactive'
        ELSE 'healthy'
    END as health_status,
    fm.error_rate,
    fm.avg_duration_ms,
    fm.total_executions,
    fm.last_updated
FROM flow_definitions fd
LEFT JOIN flow_metrics fm ON fd.id = fm.flow_id AND fm.metric_date = CURRENT_DATE
WHERE fd.status = 'active';

-- Create a function to detect circular dependencies
CREATE OR REPLACE FUNCTION has_circular_dependency(p_flow_id VARCHAR, p_depends_on_flow_id VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    visited VARCHAR[];
    current_id VARCHAR;
    dep_record RECORD;
BEGIN
    -- Initialize with the starting flow
    visited := ARRAY[p_flow_id];
    current_id := p_depends_on_flow_id;

    -- Follow dependency chain
    LOOP
        -- Check if we've seen this flow before (circular dependency)
        IF current_id = ANY(visited) THEN
            RETURN TRUE;
        END IF;

        -- Add current flow to visited list
        visited := array_append(visited, current_id);

        -- Find next dependency
        SELECT depends_on_flow_id INTO current_id
        FROM flow_dependencies
        WHERE flow_id = current_id
        LIMIT 1;

        -- If no more dependencies, no circle found
        IF current_id IS NULL THEN
            EXIT;
        END IF;

        -- Safety check: prevent infinite loops
        IF array_length(visited, 1) > 100 THEN
            EXIT;
        END IF;
    END LOOP;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Add constraint to prevent circular dependencies
ALTER TABLE flow_dependencies
ADD CONSTRAINT no_circular_dependency
CHECK (NOT has_circular_dependency(flow_id, depends_on_flow_id));

-- Initial data: Create built-in flow types
INSERT INTO flow_definitions (
    id,
    name,
    type,
    description,
    definition_json,
    status,
    created_by,
    category
) VALUES
(
    'builtin-langgraph-template',
    'LangGraph Workflow Template',
    'langgraph_workflow',
    'Default template for LangGraph workflow creation',
    '{"template": true, "nodes": [], "edges": [], "requirements": ["langgraph"]}',
    'active',
    'system',
    'template'
),
(
    'builtin-ai-brain-template',
    'AI Brain Validation Template',
    'ai_brain_validation',
    'Default template for AI Brain validation flows',
    '{"template": true, "validation_rules": [], "validator_type": "ai_brain"}',
    'active',
    'system',
    'template'
),
(
    'builtin-chain-mapping-template',
    'Chain Mapping Template',
    'chain_mapping',
    'Default template for chain mapping flows',
    '{"template": true, "chains": [], "mappings": []}',
    'active',
    'system',
    'template'
)
ON CONFLICT (id) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO flow_registry_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO flow_registry_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO flow_registry_user;

-- Performance analysis query examples (for monitoring)
/*
-- Top 10 slowest flows
SELECT fd.name, fm.avg_duration_ms, fm.p99_duration_ms, fm.total_executions
FROM flow_definitions fd
JOIN flow_metrics fm ON fd.id = fm.flow_id
WHERE fm.metric_date = CURRENT_DATE
ORDER BY fm.avg_duration_ms DESC
LIMIT 10;

-- Flows with high error rates
SELECT fd.name, fm.error_rate, fm.failed_executions, fm.total_executions
FROM flow_definitions fd
JOIN flow_metrics fm ON fd.id = fm.flow_id
WHERE fm.metric_date = CURRENT_DATE AND fm.error_rate > 0.05
ORDER BY fm.error_rate DESC;

-- Dependency chain analysis
WITH RECURSIVE dependency_chain AS (
    -- Base case: flows with no dependencies
    SELECT fd.id, fd.name, 0 as depth, ARRAY[fd.id] as path
    FROM flow_definitions fd
    WHERE NOT EXISTS (
        SELECT 1 FROM flow_dependencies WHERE flow_id = fd.id
    )

    UNION ALL

    -- Recursive case: flows with dependencies
    SELECT fd.id, fd.name, dc.depth + 1, dc.path || fd.id
    FROM flow_definitions fd
    JOIN flow_dependencies fdep ON fd.id = fdep.flow_id
    JOIN dependency_chain dc ON fdep.depends_on_flow_id = dc.id
    WHERE NOT (fd.id = ANY(dc.path)) -- Prevent cycles
)
SELECT * FROM dependency_chain ORDER BY depth, name;
*/

COMMIT;