-- ================================================================
-- Embedded Chain Mapping System - ClickHouse Schema
-- ================================================================
-- This schema supports high-frequency time-series data storage for
-- chain metrics, execution traces, and performance monitoring.
--
-- Schema Design Principles:
-- - Optimized for write-heavy workloads
-- - Efficient time-based partitioning
-- - Automatic data retention via TTL
-- - Materialized views for aggregations
-- - Optimized for analytical queries
-- ================================================================

-- ================================================================
-- Time-Series Data Tables
-- ================================================================

-- Chain health metrics (high-frequency data)
-- Stores real-time health metrics for each chain node
CREATE TABLE chain_health_metrics (
    timestamp DateTime64(3) CODEC(DoubleDelta),
    chain_id LowCardinality(String),
    node_id String,
    metric_type LowCardinality(String),              -- latency, error_rate, throughput, cpu_usage, memory_usage
    metric_value Float64 CODEC(Gorilla),
    metric_unit LowCardinality(String),              -- ms, percent, rps, mb, etc.
    status LowCardinality(String),                   -- healthy, degraded, failed
    service_name LowCardinality(String),
    component_name String,
    tags Map(String, String),                        -- Additional metadata tags
    metadata String                                  -- JSON string for additional data
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, node_id, metric_type, timestamp)
TTL timestamp + INTERVAL 90 DAY DELETE
SETTINGS index_granularity = 8192;

-- Add table comment
ALTER TABLE chain_health_metrics COMMENT 'Real-time health metrics for chain nodes';

-- Chain execution traces
-- Stores detailed execution traces for debugging and analysis
CREATE TABLE chain_execution_traces (
    trace_id String,
    span_id String,
    parent_span_id String,
    chain_id LowCardinality(String),
    node_id String,
    timestamp DateTime64(3) CODEC(DoubleDelta),
    execution_start DateTime64(3) CODEC(DoubleDelta),
    execution_end DateTime64(3) CODEC(DoubleDelta),
    duration_ms UInt32 CODEC(Gorilla),
    status LowCardinality(String),                   -- success, error, timeout
    error_code String,
    error_message String,
    input_size UInt32,
    output_size UInt32,
    service_name LowCardinality(String),
    operation_name String,
    user_id String,
    session_id String,
    tags Map(String, String),
    metadata String                                  -- JSON string with detailed trace data
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, timestamp, trace_id, span_id)
TTL timestamp + INTERVAL 30 DAY DELETE
SETTINGS index_granularity = 8192;

ALTER TABLE chain_execution_traces COMMENT 'Detailed execution traces for chains and nodes';

-- Chain performance events
-- Stores significant performance events and alerts
CREATE TABLE chain_performance_events (
    event_id String,
    timestamp DateTime64(3) CODEC(DoubleDelta),
    chain_id LowCardinality(String),
    node_id String,
    event_type LowCardinality(String),              -- threshold_breach, sla_violation, anomaly_detected, recovery
    severity LowCardinality(String),                -- low, medium, high, critical
    metric_name LowCardinality(String),
    threshold_value Float64,
    actual_value Float64,
    deviation_percent Float32,
    duration_ms UInt32,
    affected_components Array(String),
    impact_score Float32,                           -- 0.0 to 1.0
    resolution_status LowCardinality(String),       -- open, investigating, resolved, ignored
    tags Map(String, String),
    metadata String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, event_type, timestamp)
TTL timestamp + INTERVAL 180 DAY DELETE
SETTINGS index_granularity = 8192;

ALTER TABLE chain_performance_events COMMENT 'Significant performance events and alerts';

-- Chain network flows
-- Stores network communication patterns between services
CREATE TABLE chain_network_flows (
    timestamp DateTime64(3) CODEC(DoubleDelta),
    chain_id LowCardinality(String),
    source_node String,
    target_node String,
    source_service LowCardinality(String),
    target_service LowCardinality(String),
    flow_type LowCardinality(String),               -- http, websocket, grpc, database, cache
    protocol String,
    request_count UInt64 CODEC(Gorilla),
    bytes_sent UInt64 CODEC(Gorilla),
    bytes_received UInt64 CODEC(Gorilla),
    avg_latency_ms Float32 CODEC(Gorilla),
    error_count UInt32,
    status_codes Array(UInt16),
    connection_pool_size UInt16,
    tags Map(String, String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, source_service, target_service, timestamp)
TTL timestamp + INTERVAL 60 DAY DELETE
SETTINGS index_granularity = 8192;

ALTER TABLE chain_network_flows COMMENT 'Network communication flows between chain components';

-- Chain resource utilization
-- Stores resource usage metrics for capacity planning
CREATE TABLE chain_resource_utilization (
    timestamp DateTime64(3) CODEC(DoubleDelta),
    chain_id LowCardinality(String),
    node_id String,
    service_name LowCardinality(String),
    resource_type LowCardinality(String),           -- cpu, memory, disk, network, connections
    current_usage Float64 CODEC(Gorilla),
    max_capacity Float64,
    utilization_percent Float32 CODEC(Gorilla),
    allocation_unit LowCardinality(String),         -- cores, gb, mb/s, connections
    container_id String,
    pod_name String,
    namespace String,
    tags Map(String, String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, service_name, resource_type, timestamp)
TTL timestamp + INTERVAL 60 DAY DELETE
SETTINGS index_granularity = 8192;

ALTER TABLE chain_resource_utilization COMMENT 'Resource utilization metrics for chain components';

-- ================================================================
-- Analysis and Impact Tables
-- ================================================================

-- Chain impact analysis results
-- Stores results from impact analysis operations
CREATE TABLE chain_impact_analyses (
    analysis_id String,
    chain_id LowCardinality(String),
    timestamp DateTime64(3) CODEC(DoubleDelta),
    change_type LowCardinality(String),             -- service_update, node_modification, dependency_change
    target_component String,
    impact_score Float32,                           -- 0.0 to 10.0
    risk_level LowCardinality(String),              -- low, medium, high, critical
    affected_chains Array(String),
    cascade_depth UInt8,
    prediction_confidence Float32,
    analysis_duration_ms UInt32,
    model_version String,
    analysis_data String,                           -- JSON string with detailed results
    tags Map(String, String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, change_type, timestamp)
TTL timestamp + INTERVAL 180 DAY DELETE
SETTINGS index_granularity = 8192;

ALTER TABLE chain_impact_analyses COMMENT 'Impact analysis results for chain changes';

-- Chain optimization recommendations
-- Stores AI-generated optimization recommendations
CREATE TABLE chain_optimization_recommendations (
    recommendation_id String,
    chain_id LowCardinality(String),
    timestamp DateTime64(3) CODEC(DoubleDelta),
    optimization_type LowCardinality(String),       -- performance, reliability, cost, scalability
    target_node String,
    recommendation_title String,
    recommendation_description String,
    expected_improvement_percent Float32,
    implementation_effort LowCardinality(String),   -- low, medium, high
    priority LowCardinality(String),                -- low, medium, high, critical
    confidence_score Float32,
    prerequisites Array(String),
    estimated_impact_score Float32,
    cost_benefit_ratio Float32,
    implementation_status LowCardinality(String),   -- pending, in_progress, completed, rejected
    tags Map(String, String),
    metadata String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, optimization_type, priority, timestamp)
TTL timestamp + INTERVAL 365 DAY DELETE
SETTINGS index_granularity = 8192;

ALTER TABLE chain_optimization_recommendations COMMENT 'AI-generated optimization recommendations';

-- Chain pattern detection results
-- Stores detected patterns across chains
CREATE TABLE chain_pattern_detections (
    detection_id String,
    pattern_id String,
    timestamp DateTime64(3) CODEC(DoubleDelta),
    affected_chains Array(String),
    pattern_type LowCardinality(String),            -- structural, behavioral, performance, error
    confidence_score Float32,
    frequency UInt32,
    optimization_potential Float32,
    pattern_signature String,                       -- Hash of pattern characteristics
    detection_method LowCardinality(String),        -- ml_model, rule_based, statistical
    model_version String,
    tags Map(String, String),
    metadata String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (pattern_id, pattern_type, timestamp)
TTL timestamp + INTERVAL 365 DAY DELETE
SETTINGS index_granularity = 8192;

ALTER TABLE chain_pattern_detections COMMENT 'Detected patterns across multiple chains';

-- ================================================================
-- Materialized Views for Real-time Aggregations
-- ================================================================

-- Hourly chain performance summary
-- Provides hourly aggregated metrics for dashboards
CREATE MATERIALIZED VIEW chain_performance_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (chain_id, node_id, metric_type, hour)
POPULATE
AS SELECT
    toStartOfHour(timestamp) as hour,
    chain_id,
    node_id,
    metric_type,
    service_name,
    avg(metric_value) as avg_value,
    quantile(0.50)(metric_value) as p50_value,
    quantile(0.95)(metric_value) as p95_value,
    quantile(0.99)(metric_value) as p99_value,
    min(metric_value) as min_value,
    max(metric_value) as max_value,
    count() as sample_count,
    sum(case when status = 'failed' then 1 else 0 end) as error_count,
    sum(case when status = 'degraded' then 1 else 0 end) as degraded_count
FROM chain_health_metrics
GROUP BY hour, chain_id, node_id, metric_type, service_name;

-- Daily chain availability summary
-- Tracks daily availability and SLA compliance
CREATE MATERIALIZED VIEW chain_availability_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (chain_id, day)
POPULATE
AS SELECT
    toStartOfDay(timestamp) as day,
    chain_id,
    countIf(status = 'healthy') as healthy_count,
    countIf(status = 'degraded') as degraded_count,
    countIf(status = 'failed') as failed_count,
    count() as total_count,
    countIf(status = 'healthy') / count() as availability_ratio,
    uniq(node_id) as active_nodes,
    avg(metric_value) as avg_response_time
FROM chain_health_metrics
WHERE metric_type = 'latency'
GROUP BY day, chain_id;

-- Chain error rate summary (5-minute intervals)
-- Provides near real-time error tracking
CREATE MATERIALIZED VIEW chain_error_rate_5min
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(interval_start)
ORDER BY (chain_id, node_id, interval_start)
POPULATE
AS SELECT
    toStartOfFiveMinutes(timestamp) as interval_start,
    chain_id,
    node_id,
    service_name,
    countIf(status = 'failed') as error_count,
    count() as total_count,
    countIf(status = 'failed') / count() as error_rate,
    quantile(0.95)(metric_value) as p95_latency
FROM chain_health_metrics
WHERE metric_type = 'latency'
GROUP BY interval_start, chain_id, node_id, service_name;

-- Service communication flow summary
-- Aggregates network flows between services
CREATE MATERIALIZED VIEW service_flow_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (source_service, target_service, flow_type, hour)
POPULATE
AS SELECT
    toStartOfHour(timestamp) as hour,
    source_service,
    target_service,
    flow_type,
    sum(request_count) as total_requests,
    sum(bytes_sent) as total_bytes_sent,
    sum(bytes_received) as total_bytes_received,
    avg(avg_latency_ms) as avg_latency,
    sum(error_count) as total_errors,
    uniq(chain_id) as chain_count
FROM chain_network_flows
GROUP BY hour, source_service, target_service, flow_type;

-- ================================================================
-- Indexes for Query Optimization
-- ================================================================

-- Additional indexes for common query patterns
-- Note: ClickHouse uses different indexing strategies

-- Skip indexes for better performance on filtered queries
ALTER TABLE chain_health_metrics
ADD INDEX idx_status status TYPE set(100) GRANULARITY 1;

ALTER TABLE chain_health_metrics
ADD INDEX idx_metric_type metric_type TYPE set(50) GRANULARITY 1;

ALTER TABLE chain_execution_traces
ADD INDEX idx_status status TYPE set(10) GRANULARITY 1;

ALTER TABLE chain_execution_traces
ADD INDEX idx_duration duration_ms TYPE minmax GRANULARITY 1;

ALTER TABLE chain_performance_events
ADD INDEX idx_severity severity TYPE set(10) GRANULARITY 1;

ALTER TABLE chain_performance_events
ADD INDEX idx_event_type event_type TYPE set(50) GRANULARITY 1;

-- ================================================================
-- Dictionary Tables for Efficient Lookups
-- ================================================================

-- Dictionary for chain metadata (loaded from PostgreSQL)
CREATE DICTIONARY chain_metadata_dict (
    chain_id String,
    name String,
    category String,
    status String
)
PRIMARY KEY chain_id
SOURCE(POSTGRESQL(
    host 'database-service'
    port 5432
    user 'clickhouse_reader'
    password 'your_password'
    db 'ai_trading'
    table 'chain_definitions'
))
LIFETIME(MIN 300 MAX 600)
LAYOUT(FLAT());

-- Dictionary for service information
CREATE DICTIONARY service_metadata_dict (
    service_name String,
    port UInt16,
    health_endpoint String,
    category String
)
PRIMARY KEY service_name
SOURCE(POSTGRESQL(
    host 'database-service'
    port 5432
    user 'clickhouse_reader'
    password 'your_password'
    db 'ai_trading'
    table 'service_registry'
))
LIFETIME(MIN 600 MAX 1200)
LAYOUT(FLAT());

-- ================================================================
-- Functions for Common Calculations
-- ================================================================

-- Function to calculate SLA compliance
CREATE FUNCTION sla_compliance(uptime_ratio Float64, latency_p95 Float64, error_rate Float64)
RETURNS Float64
LANGUAGE SQL
AS 'SELECT if(uptime_ratio >= 0.999 AND latency_p95 <= 100 AND error_rate <= 0.001, 1.0,
              if(uptime_ratio >= 0.99 AND latency_p95 <= 200 AND error_rate <= 0.01, 0.8,
                 if(uptime_ratio >= 0.95 AND latency_p95 <= 500 AND error_rate <= 0.05, 0.6, 0.0)))';

-- Function to calculate health score
CREATE FUNCTION health_score(availability Float64, avg_latency Float64, error_rate Float64)
RETURNS Float64
LANGUAGE SQL
AS 'SELECT (availability * 0.4 + (1 - least(avg_latency / 1000, 1)) * 0.3 + (1 - least(error_rate * 10, 1)) * 0.3) * 100';

-- ================================================================
-- Data Quality and Monitoring
-- ================================================================

-- Function to detect anomalies in metrics
CREATE FUNCTION detect_anomaly(current_value Float64, historical_avg Float64, historical_stddev Float64)
RETURNS UInt8
LANGUAGE SQL
AS 'SELECT if(abs(current_value - historical_avg) > 3 * historical_stddev, 1, 0)';

-- ================================================================
-- Retention and Cleanup Policies
-- ================================================================

-- Automatic cleanup for old partitions
-- This is handled by TTL settings in table definitions above

-- System for archiving important events before deletion
CREATE TABLE chain_archived_events (
    archive_date Date,
    event_type LowCardinality(String),
    chain_id LowCardinality(String),
    event_data String,
    event_count UInt64
) ENGINE = MergeTree()
ORDER BY (archive_date, event_type, chain_id);

-- ================================================================
-- Performance Optimization Settings
-- ================================================================

-- Optimize tables for better compression and query performance
OPTIMIZE TABLE chain_health_metrics FINAL;
OPTIMIZE TABLE chain_execution_traces FINAL;
OPTIMIZE TABLE chain_performance_events FINAL;
OPTIMIZE TABLE chain_network_flows FINAL;
OPTIMIZE TABLE chain_resource_utilization FINAL;

-- ================================================================
-- Monitoring Queries for Operations
-- ================================================================

-- Create a view for real-time chain health dashboard
CREATE VIEW real_time_chain_health AS
SELECT
    chain_id,
    dictGet('chain_metadata_dict', 'name', chain_id) as chain_name,
    dictGet('chain_metadata_dict', 'category', chain_id) as category,
    count(DISTINCT node_id) as active_nodes,
    avg(metric_value) as avg_latency,
    quantile(0.95)(metric_value) as p95_latency,
    countIf(status = 'failed') / count() as error_rate,
    countIf(status = 'healthy') / count() as availability,
    health_score(
        countIf(status = 'healthy') / count(),
        avg(metric_value),
        countIf(status = 'failed') / count()
    ) as health_score,
    max(timestamp) as last_update
FROM chain_health_metrics
WHERE timestamp >= now() - INTERVAL 5 MINUTE
  AND metric_type = 'latency'
GROUP BY chain_id
ORDER BY health_score ASC;

-- Create a view for service performance overview
CREATE VIEW service_performance_overview AS
SELECT
    service_name,
    count(DISTINCT chain_id) as chain_count,
    count(DISTINCT node_id) as node_count,
    avg(metric_value) as avg_response_time,
    quantile(0.95)(metric_value) as p95_response_time,
    countIf(status = 'failed') / count() as error_rate,
    max(timestamp) as last_seen
FROM chain_health_metrics
WHERE timestamp >= now() - INTERVAL 15 MINUTE
  AND metric_type = 'latency'
GROUP BY service_name
ORDER BY error_rate DESC, p95_response_time DESC;

-- ================================================================
-- End of Schema Definition
-- ================================================================

-- Add final system comment
SELECT 'ClickHouse Chain Mapping Schema v1.0.0 initialized successfully' as status;