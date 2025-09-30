/**
 * Central Hub Contract: Health Report (Inbound)
 * Pattern: many-to-one (services → central-hub)
 * Transport: gRPC
 *
 * Services send health reports ke Central Hub untuk monitoring
 */

const Joi = require('joi');

/**
 * Input validation schema untuk health report
 */
const HealthReportSchema = Joi.object({
    // Service identification
    service_name: Joi.string().required(),
    instance_id: Joi.string().optional(),

    // Health status
    status: Joi.string().valid('healthy', 'degraded', 'unhealthy', 'critical').required(),

    // Health metrics
    metrics: Joi.object({
        // System metrics
        cpu_usage: Joi.number().min(0).max(100).required(),
        memory_usage: Joi.number().min(0).max(100).required(),
        disk_usage: Joi.number().min(0).max(100).optional(),

        // Application metrics
        uptime_seconds: Joi.number().min(0).required(),
        active_connections: Joi.number().min(0).required(),
        requests_per_minute: Joi.number().min(0).optional(),
        error_rate: Joi.number().min(0).max(100).optional(),

        // Response times
        avg_response_time_ms: Joi.number().min(0).optional(),
        p95_response_time_ms: Joi.number().min(0).optional(),

        // Custom service metrics
        custom_metrics: Joi.object().optional()
    }).required(),

    // Health details
    checks: Joi.array().items(
        Joi.object({
            name: Joi.string().required(),
            status: Joi.string().valid('pass', 'warn', 'fail').required(),
            message: Joi.string().optional(),
            details: Joi.object().optional()
        })
    ).optional(),

    // Timestamp
    timestamp: Joi.number().default(() => Date.now()),

    // Environment context
    environment: Joi.string().valid('development', 'staging', 'production').required()
});

/**
 * Process health report
 */
function processHealthReport(inputData, context = {}) {
    // Validate input
    const { error, value } = HealthReportSchema.validate(inputData);
    if (error) {
        throw new Error(`Health report validation failed: ${error.details[0].message}`);
    }

    const healthReport = value;

    // Add system metadata
    healthReport.report_id = `health-${healthReport.service_name}-${Date.now()}`;
    healthReport.received_at = Date.now();

    // Determine if this requires immediate attention
    const criticalStatus = ['unhealthy', 'critical'].includes(healthReport.status);
    const highResourceUsage = healthReport.metrics.cpu_usage > 90 || healthReport.metrics.memory_usage > 90;
    const highErrorRate = (healthReport.metrics.error_rate || 0) > 10;

    const requiresAttention = criticalStatus || highResourceUsage || highErrorRate;

    // Determine routing targets
    const routingTargets = ['health-monitor'];
    if (requiresAttention) {
        routingTargets.push('alert-manager', 'scaling-coordinator');
    }

    return {
        type: 'health_report',
        data: healthReport,
        routing_targets: routingTargets,
        response_format: 'health_report_acknowledgment',
        metadata: {
            source_contract: 'health-report-to-central-hub',
            processing_time: Date.now(),
            correlation_id: context.correlationId || healthReport.report_id,
            priority: requiresAttention ? 'high' : 'normal',
            requires_attention: requiresAttention
        }
    };
}

/**
 * Analyze health trends
 */
function analyzeHealthTrends(currentReport, historicalReports = []) {
    const trends = {
        cpu_trend: 'stable',
        memory_trend: 'stable',
        response_time_trend: 'stable',
        status_changes: []
    };

    if (historicalReports.length > 0) {
        const lastReport = historicalReports[historicalReports.length - 1];

        // CPU trend
        const cpuDiff = currentReport.metrics.cpu_usage - lastReport.metrics.cpu_usage;
        if (cpuDiff > 10) trends.cpu_trend = 'increasing';
        else if (cpuDiff < -10) trends.cpu_trend = 'decreasing';

        // Memory trend
        const memDiff = currentReport.metrics.memory_usage - lastReport.metrics.memory_usage;
        if (memDiff > 10) trends.memory_trend = 'increasing';
        else if (memDiff < -10) trends.memory_trend = 'decreasing';

        // Status changes
        if (currentReport.status !== lastReport.status) {
            trends.status_changes.push({
                from: lastReport.status,
                to: currentReport.status,
                timestamp: currentReport.timestamp
            });
        }
    }

    return trends;
}

const contractInfo = {
    name: 'health-report-to-central-hub',
    version: '1.0.0',
    description: 'Health reports sent from services to Central Hub via gRPC streaming',
    transport_method: 'grpc',
    direction: 'inbound',
    pattern: 'many-to-one',
    grpc_service: 'HealthMonitoring',
    grpc_method: 'ReportHealth',
    streaming: true
};

module.exports = {
    processHealthReport,
    analyzeHealthTrends,
    HealthReportSchema,
    contractInfo
};