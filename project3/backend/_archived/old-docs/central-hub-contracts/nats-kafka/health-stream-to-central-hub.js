/**
 * Central Hub Contract: Health Stream (Inbound)
 * Pattern: many-to-one (services → central-hub)
 * Transport: NATS+Kafka
 *
 * Continuous health data streaming dari services ke Central Hub
 */

const Joi = require('joi');

/**
 * Input validation schema untuk health stream data
 */
const HealthStreamSchema = Joi.object({
    // Service identification
    service_name: Joi.string().required(),
    instance_id: Joi.string().required(),

    // Stream metadata
    sequence_number: Joi.number().integer().min(0).required(),
    batch_size: Joi.number().integer().min(1).max(100).default(1),

    // Real-time metrics
    metrics: Joi.object({
        // High-frequency metrics
        timestamp: Joi.number().required(),
        cpu_usage: Joi.number().min(0).max(100).required(),
        memory_usage: Joi.number().min(0).max(100).required(),

        // Network metrics
        network_in_bytes: Joi.number().min(0).optional(),
        network_out_bytes: Joi.number().min(0).optional(),

        // Application metrics
        active_connections: Joi.number().min(0).required(),
        requests_current: Joi.number().min(0).optional(),

        // Performance metrics
        response_time_ms: Joi.number().min(0).optional(),
        queue_depth: Joi.number().min(0).optional(),

        // Error tracking
        errors_last_minute: Joi.number().min(0).optional(),
        warnings_last_minute: Joi.number().min(0).optional()
    }).required(),

    // Health indicators
    health_indicators: Joi.array().items(
        Joi.object({
            name: Joi.string().required(),
            value: Joi.number().required(),
            threshold: Joi.number().optional(),
            status: Joi.string().valid('normal', 'warning', 'critical').required()
        })
    ).optional(),

    // Environment
    environment: Joi.string().valid('development', 'staging', 'production').required()
});

/**
 * Process health stream data
 */
function processHealthStream(streamData, context = {}) {
    // Validate input
    const { error, value } = HealthStreamSchema.validate(streamData);
    if (error) {
        throw new Error(`Health stream validation failed: ${error.details[0].message}`);
    }

    const healthData = value;

    // Add processing metadata
    healthData.stream_id = `health-stream-${healthData.service_name}-${healthData.sequence_number}`;
    healthData.processed_at = Date.now();

    // Detect anomalies in real-time
    const anomalies = detectAnomalies(healthData.metrics);

    // Determine processing priority
    const priority = calculatePriority(healthData.metrics, anomalies);

    // Route based on anomalies and patterns
    const routingTargets = ['health-aggregator'];

    if (anomalies.length > 0) {
        routingTargets.push('anomaly-detector', 'alert-manager');
    }

    if (priority === 'high') {
        routingTargets.push('scaling-coordinator');
    }

    return {
        type: 'health_stream',
        data: healthData,
        routing_targets: routingTargets,
        response_format: 'health_stream_acknowledgment',
        metadata: {
            source_contract: 'health-stream-to-central-hub',
            processing_time: Date.now(),
            correlation_id: context.correlationId || healthData.stream_id,
            priority: priority,
            anomalies: anomalies,
            stream_position: healthData.sequence_number
        }
    };
}

/**
 * Detect anomalies in health metrics
 */
function detectAnomalies(metrics) {
    const anomalies = [];

    // CPU spike detection
    if (metrics.cpu_usage > 95) {
        anomalies.push({
            type: 'cpu_spike',
            value: metrics.cpu_usage,
            severity: 'critical',
            message: 'CPU usage critically high'
        });
    } else if (metrics.cpu_usage > 80) {
        anomalies.push({
            type: 'cpu_high',
            value: metrics.cpu_usage,
            severity: 'warning',
            message: 'CPU usage elevated'
        });
    }

    // Memory leak detection
    if (metrics.memory_usage > 90) {
        anomalies.push({
            type: 'memory_critical',
            value: metrics.memory_usage,
            severity: 'critical',
            message: 'Memory usage critically high'
        });
    }

    // Response time degradation
    if (metrics.response_time_ms && metrics.response_time_ms > 5000) {
        anomalies.push({
            type: 'response_slow',
            value: metrics.response_time_ms,
            severity: 'warning',
            message: 'Response time degraded'
        });
    }

    // Error rate spike
    if (metrics.errors_last_minute && metrics.errors_last_minute > 10) {
        anomalies.push({
            type: 'error_spike',
            value: metrics.errors_last_minute,
            severity: 'critical',
            message: 'High error rate detected'
        });
    }

    return anomalies;
}

/**
 * Calculate processing priority
 */
function calculatePriority(metrics, anomalies) {
    // Critical conditions
    if (anomalies.some(a => a.severity === 'critical')) {
        return 'critical';
    }

    // High load conditions
    if (metrics.cpu_usage > 70 || metrics.memory_usage > 75 ||
        (metrics.active_connections && metrics.active_connections > 800)) {
        return 'high';
    }

    // Warning conditions
    if (anomalies.some(a => a.severity === 'warning')) {
        return 'medium';
    }

    return 'low';
}

/**
 * Aggregate stream data for batch processing
 */
function aggregateStreamBatch(streamDataArray) {
    if (!streamDataArray.length) return null;

    const first = streamDataArray[0];
    const last = streamDataArray[streamDataArray.length - 1];

    return {
        service_name: first.service_name,
        instance_id: first.instance_id,
        batch_start: first.metrics.timestamp,
        batch_end: last.metrics.timestamp,
        sample_count: streamDataArray.length,

        // Aggregated metrics
        avg_cpu: streamDataArray.reduce((sum, d) => sum + d.metrics.cpu_usage, 0) / streamDataArray.length,
        max_cpu: Math.max(...streamDataArray.map(d => d.metrics.cpu_usage)),
        avg_memory: streamDataArray.reduce((sum, d) => sum + d.metrics.memory_usage, 0) / streamDataArray.length,
        max_memory: Math.max(...streamDataArray.map(d => d.metrics.memory_usage)),

        // Connection patterns
        avg_connections: streamDataArray.reduce((sum, d) => sum + d.metrics.active_connections, 0) / streamDataArray.length,
        max_connections: Math.max(...streamDataArray.map(d => d.metrics.active_connections)),

        // Total anomalies in batch
        total_anomalies: streamDataArray.reduce((sum, d) => sum + (d.anomalies || []).length, 0)
    };
}

const contractInfo = {
    name: 'health-stream-to-central-hub',
    version: '1.0.0',
    description: 'High-frequency health data streaming from services to Central Hub via NATS+Kafka',
    transport_method: 'nats-kafka',
    direction: 'inbound',
    pattern: 'many-to-one',
    nats_subject: 'health.stream.{service_name}',
    kafka_topic: 'health-stream-data',
    streaming: true,
    expected_frequency: 'every 5-30 seconds'
};

module.exports = {
    processHealthStream,
    detectAnomalies,
    calculatePriority,
    aggregateStreamBatch,
    HealthStreamSchema,
    contractInfo
};