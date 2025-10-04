/**
 * Contract: Health Report to Central Hub
 * Direction: OANDA Collector → Central Hub
 * Protocol: HTTP REST
 * Endpoint: POST /health/report
 */

const Joi = require('joi');

const HealthReportSchema = Joi.object({
    // Service identification
    service_name: Joi.string().required(),
    instance_id: Joi.string().required(),
    timestamp: Joi.number().integer().required(),

    // Overall health status
    status: Joi.string().valid('healthy', 'degraded', 'unhealthy').required(),

    // System metrics
    metrics: Joi.object({
        cpu_usage_percent: Joi.number().min(0).max(100).required(),
        memory_usage_percent: Joi.number().min(0).max(100).required(),
        active_streams: Joi.number().integer().min(0).required(),
        active_accounts: Joi.number().integer().min(0).max(4).required(),
        failed_accounts: Joi.number().integer().min(0).max(4).required(),

        // OANDA specific metrics
        oanda_metrics: Joi.object({
            total_ticks_received: Joi.number().integer().min(0).required(),
            ticks_per_second: Joi.number().min(0).required(),
            failed_reconnections: Joi.number().integer().min(0).required(),
            current_failover_account: Joi.string().allow(null).optional(),
            rate_limit_remaining: Joi.number().integer().min(0).optional()
        }).optional()
    }).required(),

    // Component health checks
    checks: Joi.object({
        oanda_connection: Joi.object({
            status: Joi.string().valid('pass', 'fail', 'warn').required(),
            details: Joi.string().optional(),
            response_time_ms: Joi.number().optional()
        }).required(),

        nats_connection: Joi.object({
            status: Joi.string().valid('pass', 'fail', 'warn').required(),
            details: Joi.string().optional()
        }).required(),

        central_hub_connection: Joi.object({
            status: Joi.string().valid('pass', 'fail', 'warn').required(),
            details: Joi.string().optional()
        }).required(),

        account_health: Joi.object({
            status: Joi.string().valid('pass', 'fail', 'warn').required(),
            healthy_accounts: Joi.number().integer().min(0).required(),
            details: Joi.string().optional()
        }).required()
    }).required(),

    // Alerts and warnings
    alerts: Joi.array().items(
        Joi.object({
            severity: Joi.string().valid('info', 'warning', 'error', 'critical').required(),
            message: Joi.string().required(),
            timestamp: Joi.number().integer().required(),
            component: Joi.string().optional()
        })
    ).optional()
});

/**
 * Process health report data
 */
function processHealthReport(inputData, context = {}) {
    // Validate input
    const { error, value } = HealthReportSchema.validate(inputData);
    if (error) {
        throw new Error(`Contract validation failed: ${error.details[0].message}`);
    }

    // Enrich health data
    const healthData = {
        ...value,
        processed_at: Date.now(),
        service_category: 'data-ingestion'
    };

    return {
        type: 'health_report',
        data: healthData,
        routing_targets: ['health-monitor', 'metrics-collector'],
        response_format: 'health_acknowledgment'
    };
}

module.exports = {
    schema: HealthReportSchema,
    process: processHealthReport,
    contractName: 'health-report',
    direction: 'to-central-hub',
    protocol: 'http-rest'
};
