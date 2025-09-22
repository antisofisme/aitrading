-- ClickHouse Schema for Chain Debug System
-- Time-series data for chain health metrics and execution traces
-- Based on Chain-Aware Debugging Procedures documentation

-- Chain health metrics (high-frequency data)
CREATE TABLE IF NOT EXISTS chain_health_metrics (
    timestamp DateTime64(3),
    chain_id String,
    service_name String,
    node_id String,
    metric_type LowCardinality(String),  -- latency, error_rate, throughput, cpu, memory, etc.
    metric_value Float64,
    status LowCardinality(String),       -- healthy, degraded, failed, unknown
    request_id String,
    flow_id String,
    metadata String,  -- JSON string for additional data

    -- Additional fields for enhanced monitoring
    source_service String,
    target_service String,
    operation_type LowCardinality(String),  -- http_request, db_query, ai_inference, etc.
    user_id String,
    tenant_id String,
    environment LowCardinality(String),     -- development, staging, production
    region LowCardinality(String),

    -- Performance metrics
    duration_ms UInt32,
    queue_time_ms UInt32,
    processing_time_ms UInt32,
    response_size_bytes UInt32,
    error_code String,
    retry_count UInt8,

    -- Resource utilization
    cpu_usage_percent Float32,
    memory_usage_mb Float32,
    disk_io_mb Float32,
    network_io_mb Float32

) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, service_name, timestamp)
TTL timestamp + INTERVAL 90 DAY DELETE
SETTINGS index_granularity = 8192;

-- Chain execution traces with detailed step tracking
CREATE TABLE IF NOT EXISTS chain_execution_traces (
    trace_id String,
    chain_id String,
    flow_id String,
    execution_id String,
    step_id String,
    parent_step_id String,

    -- Timing information
    timestamp DateTime64(3),
    execution_start DateTime64(3),
    execution_end DateTime64(3),
    duration_ms UInt32,
    queue_duration_ms UInt32,

    -- Step information
    step_name String,
    step_type LowCardinality(String),  -- api_call, db_query, computation, ai_inference
    service_name String,
    node_id String,
    operation_name String,

    -- Status and results
    status LowCardinality(String),     -- pending, running, completed, failed, timeout
    status_code UInt16,
    error_message String,
    error_type LowCardinality(String), -- validation, network, timeout, service, data

    -- Data flow information
    input_size_bytes UInt32,
    output_size_bytes UInt32,
    input_hash String,
    output_hash String,

    -- Context information
    user_id String,
    tenant_id String,
    session_id String,
    correlation_id String,

    -- Resource usage
    cpu_time_ms UInt32,
    memory_peak_mb UInt32,
    io_operations UInt32,
    network_calls UInt16,
    cache_hits UInt16,
    cache_misses UInt16,

    -- Additional metadata
    metadata String,  -- JSON string
    tags Array(String),
    labels Map(String, String)

) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, trace_id, timestamp)
TTL timestamp + INTERVAL 30 DAY DELETE
SETTINGS index_granularity = 8192;

-- Chain dependency events for impact analysis
CREATE TABLE IF NOT EXISTS chain_dependency_events (
    event_id String,
    timestamp DateTime64(3),
    event_type LowCardinality(String),  -- dependency_call, dependency_failure, dependency_timeout

    -- Source and target information
    source_chain_id String,
    source_service String,
    source_node String,
    target_chain_id String,
    target_service String,
    target_node String,

    -- Dependency details
    dependency_type LowCardinality(String),  -- http, database, cache, queue, ai_service
    dependency_name String,
    operation String,

    -- Status and performance
    status LowCardinality(String),
    response_time_ms UInt32,
    retry_count UInt8,
    circuit_breaker_state LowCardinality(String),  -- closed, open, half_open

    -- Error information
    error_code String,
    error_message String,
    error_category LowCardinality(String),

    -- Context
    flow_id String,
    execution_id String,
    user_id String,
    tenant_id String,

    -- Impact metrics
    affected_requests UInt32,
    cascaded_failures UInt16,
    recovery_time_ms UInt32,

    metadata String  -- JSON string

) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (source_chain_id, target_chain_id, timestamp)
TTL timestamp + INTERVAL 60 DAY DELETE
SETTINGS index_granularity = 8192;

-- Chain anomaly detections
CREATE TABLE IF NOT EXISTS chain_anomalies (
    anomaly_id String,
    detection_timestamp DateTime64(3),
    chain_id String,
    service_name String,

    -- Anomaly details
    anomaly_type LowCardinality(String),  -- performance, error_spike, resource, pattern
    severity LowCardinality(String),      -- low, medium, high, critical
    confidence_score Float32,

    -- Affected metrics
    metric_name String,
    current_value Float64,
    baseline_value Float64,
    threshold_value Float64,
    deviation_score Float32,

    -- Detection method
    detector_type LowCardinality(String),  -- statistical, ml_model, rule_based
    detector_version String,

    -- Time window
    window_start DateTime64(3),
    window_end DateTime64(3),
    data_points UInt32,

    -- Context
    flow_id String,
    affected_users UInt32,
    business_impact_score Float32,

    -- Resolution
    resolution_status LowCardinality(String),  -- open, acknowledged, resolved, false_positive
    resolution_timestamp Nullable(DateTime64(3)),
    resolution_actions Array(String),

    metadata String  -- JSON string with additional details

) ENGINE = MergeTree()
PARTITION BY toYYYYMM(detection_timestamp)
ORDER BY (chain_id, detection_timestamp)
TTL detection_timestamp + INTERVAL 180 DAY DELETE
SETTINGS index_granularity = 8192;

-- Chain recovery actions
CREATE TABLE IF NOT EXISTS chain_recovery_actions (
    action_id String,
    timestamp DateTime64(3),
    chain_id String,
    service_name String,

    -- Trigger information
    trigger_type LowCardinality(String),   -- anomaly, manual, scheduled, cascade
    trigger_id String,
    triggered_by String,

    -- Action details
    action_type LowCardinality(String),    -- restart, scale, circuit_break, traffic_shift
    action_name String,
    action_parameters String,  -- JSON string

    -- Execution
    execution_status LowCardinality(String),  -- pending, running, completed, failed
    execution_start DateTime64(3),
    execution_end Nullable(DateTime64(3)),
    execution_duration_ms Nullable(UInt32),

    -- Results
    success_rate Float32,
    affected_instances UInt16,
    recovered_instances UInt16,
    error_message String,

    -- Impact
    downtime_ms UInt32,
    requests_affected UInt32,
    users_affected UInt32,
    business_impact_score Float32,

    -- Verification
    verification_checks Array(String),
    verification_results Map(String, String),
    health_check_passed Bool,

    metadata String  -- JSON string

) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, timestamp)
TTL timestamp + INTERVAL 90 DAY DELETE
SETTINGS index_granularity = 8192;

-- Materialized views for real-time aggregations

-- Chain performance aggregates (1-minute windows)
CREATE MATERIALIZED VIEW IF NOT EXISTS chain_performance_1m
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, service_name, timestamp)
AS SELECT
    toStartOfMinute(timestamp) as timestamp,
    chain_id,
    service_name,
    node_id,
    metric_type,

    -- Performance metrics
    avg(metric_value) as avg_value,
    min(metric_value) as min_value,
    max(metric_value) as max_value,
    quantile(0.50)(metric_value) as p50_value,
    quantile(0.95)(metric_value) as p95_value,
    quantile(0.99)(metric_value) as p99_value,

    -- Counters
    count() as sample_count,
    countIf(status = 'failed') as error_count,
    countIf(status = 'healthy') as success_count,
    countIf(status = 'degraded') as degraded_count,

    -- Resource utilization
    avg(cpu_usage_percent) as avg_cpu_usage,
    avg(memory_usage_mb) as avg_memory_usage,
    sum(network_io_mb) as total_network_io,

    -- Error rate
    (countIf(status = 'failed') / count()) * 100 as error_rate_percent

FROM chain_health_metrics
WHERE timestamp >= now() - INTERVAL 2 HOUR  -- Only process recent data
GROUP BY
    toStartOfMinute(timestamp),
    chain_id,
    service_name,
    node_id,
    metric_type;

-- Chain execution summary (5-minute windows)
CREATE MATERIALIZED VIEW IF NOT EXISTS chain_execution_summary_5m
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (chain_id, timestamp)
AS SELECT
    toStartOfInterval(timestamp, INTERVAL 5 MINUTE) as timestamp,
    chain_id,
    service_name,
    step_type,

    -- Execution statistics
    count() as total_executions,
    countIf(status = 'completed') as completed_count,
    countIf(status = 'failed') as failed_count,
    countIf(status = 'timeout') as timeout_count,

    -- Performance metrics
    avg(duration_ms) as avg_duration_ms,
    quantile(0.95)(duration_ms) as p95_duration_ms,
    quantile(0.99)(duration_ms) as p99_duration_ms,
    min(duration_ms) as min_duration_ms,
    max(duration_ms) as max_duration_ms,

    -- Resource usage
    avg(cpu_time_ms) as avg_cpu_time_ms,
    avg(memory_peak_mb) as avg_memory_mb,
    sum(io_operations) as total_io_operations,

    -- Data flow
    avg(input_size_bytes) as avg_input_size,
    avg(output_size_bytes) as avg_output_size,
    sum(input_size_bytes) as total_input_bytes,
    sum(output_size_bytes) as total_output_bytes,

    -- Cache performance
    sum(cache_hits) as total_cache_hits,
    sum(cache_misses) as total_cache_misses,
    (sum(cache_hits) / (sum(cache_hits) + sum(cache_misses))) * 100 as cache_hit_rate_percent

FROM chain_execution_traces
WHERE timestamp >= now() - INTERVAL 6 HOUR  -- Only process recent data
GROUP BY
    toStartOfInterval(timestamp, INTERVAL 5 MINUTE),
    chain_id,
    service_name,
    step_type;

-- Daily chain statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS chain_daily_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (chain_id, date)
AS SELECT
    toDate(timestamp) as date,
    chain_id,
    service_name,

    -- Daily counts
    count() as total_requests,
    countIf(status = 'completed') as successful_requests,
    countIf(status = 'failed') as failed_requests,
    countDistinct(user_id) as unique_users,
    countDistinct(session_id) as unique_sessions,

    -- Daily performance
    avg(duration_ms) as avg_duration_ms,
    quantile(0.95)(duration_ms) as p95_duration_ms,
    min(duration_ms) as min_duration_ms,
    max(duration_ms) as max_duration_ms,

    -- Daily error rate
    (countIf(status = 'failed') / count()) * 100 as daily_error_rate_percent,

    -- Daily resource usage
    avg(cpu_time_ms) as avg_cpu_time_ms,
    avg(memory_peak_mb) as avg_memory_mb,
    sum(input_size_bytes + output_size_bytes) as total_data_bytes

FROM chain_execution_traces
GROUP BY
    toDate(timestamp),
    chain_id,
    service_name;

-- Create indexes for better query performance
-- Note: ClickHouse doesn't have traditional indexes, but we optimize with projections

-- Projection for chain health analysis
ALTER TABLE chain_health_metrics ADD PROJECTION chain_health_by_service
(
    SELECT
        service_name,
        metric_type,
        timestamp,
        avg(metric_value),
        quantile(0.95)(metric_value),
        count()
    GROUP BY service_name, metric_type, toStartOfMinute(timestamp)
);

-- Projection for execution trace analysis
ALTER TABLE chain_execution_traces ADD PROJECTION trace_by_chain_and_status
(
    SELECT
        chain_id,
        status,
        step_type,
        timestamp,
        count(),
        avg(duration_ms),
        sum(cpu_time_ms)
    GROUP BY chain_id, status, step_type, toStartOfHour(timestamp)
);

-- Common query examples for monitoring and alerting
/*
-- Current chain health status (last 5 minutes)
SELECT
    chain_id,
    service_name,
    avg(metric_value) as avg_latency,
    quantile(0.95)(metric_value) as p95_latency,
    countIf(status = 'failed') / count() * 100 as error_rate
FROM chain_health_metrics
WHERE timestamp >= now() - INTERVAL 5 MINUTE
    AND metric_type = 'latency'
GROUP BY chain_id, service_name
ORDER BY error_rate DESC, p95_latency DESC;

-- Chains with anomalies in the last hour
SELECT
    chain_id,
    service_name,
    anomaly_type,
    severity,
    confidence_score,
    current_value,
    baseline_value
FROM chain_anomalies
WHERE detection_timestamp >= now() - INTERVAL 1 HOUR
    AND resolution_status = 'open'
ORDER BY confidence_score DESC, severity DESC;

-- Top 10 slowest chain executions today
SELECT
    chain_id,
    service_name,
    step_name,
    max(duration_ms) as max_duration,
    avg(duration_ms) as avg_duration,
    count() as execution_count
FROM chain_execution_traces
WHERE toDate(timestamp) = today()
    AND status = 'completed'
GROUP BY chain_id, service_name, step_name
ORDER BY max_duration DESC
LIMIT 10;

-- Dependency failure analysis
SELECT
    source_service,
    target_service,
    dependency_type,
    count() as failure_count,
    avg(response_time_ms) as avg_response_time,
    countDistinct(source_chain_id) as affected_chains
FROM chain_dependency_events
WHERE timestamp >= now() - INTERVAL 1 HOUR
    AND status = 'failed'
GROUP BY source_service, target_service, dependency_type
ORDER BY failure_count DESC;
*/