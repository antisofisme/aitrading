/**
 * Contract: Service Heartbeat Stream to Central Hub
 * Direction: OANDA Collector → Central Hub
 * Protocol: NATS
 * Subject: service.heartbeat.oanda-collector.{instance_id}
 */

const Joi = require('joi');

const HeartbeatStreamSchema = Joi.object({
    // Message routing
    subject: Joi.string().pattern(/^service\.heartbeat\.oanda-collector\..+$/).required(),
    message_id: Joi.string().required(),
    timestamp: Joi.number().integer().required(),

    // Service identification
    service: Joi.object({
        name: Joi.string().required(),
        instance_id: Joi.string().required(),
        version: Joi.string().required(),
        uptime_seconds: Joi.number().integer().min(0).required()
    }).required(),

    // Health status
    health: Joi.object({
        status: Joi.string().valid('healthy', 'degraded', 'unhealthy').required(),

        // Component status
        components: Joi.object({
            oanda_api: Joi.string().valid('up', 'down', 'degraded').required(),
            nats_connection: Joi.string().valid('up', 'down', 'degraded').required(),
            central_hub: Joi.string().valid('up', 'down', 'degraded').required()
        }).required()
    }).required(),

    // Current state
    state: Joi.object({
        active_streams: Joi.number().integer().min(0).required(),
        active_instruments: Joi.array().items(Joi.string()).required(),
        active_account_id: Joi.string().allow(null).required(),
        healthy_accounts: Joi.number().integer().min(0).max(4).required(),
        failed_accounts: Joi.number().integer().min(0).max(4).required(),

        // Performance metrics
        metrics: Joi.object({
            ticks_per_second: Joi.number().min(0).required(),
            total_ticks: Joi.number().integer().min(0).required(),
            reconnection_count: Joi.number().integer().min(0).required(),
            last_failover: Joi.string().isoDate().allow(null).optional()
        }).required()
    }).required(),

    // Resource usage
    resources: Joi.object({
        cpu_percent: Joi.number().min(0).max(100).required(),
        memory_percent: Joi.number().min(0).max(100).required(),
        memory_mb: Joi.number().min(0).required()
    }).optional()
});

/**
 * Process heartbeat stream data
 */
function processHeartbeatStream(inputData, context = {}) {
    // Validate input
    const { error, value } = HeartbeatStreamSchema.validate(inputData);
    if (error) {
        throw new Error(`Contract validation failed: ${error.details[0].message}`);
    }

    // Determine if alert is needed
    const needsAlert =
        value.health.status === 'unhealthy' ||
        value.state.healthy_accounts === 0 ||
        value.resources?.cpu_percent > 90 ||
        value.resources?.memory_percent > 90;

    const heartbeatData = {
        ...value,
        processed_at: Date.now(),
        alert_required: needsAlert
    };

    return {
        type: 'heartbeat_stream',
        data: heartbeatData,
        routing_targets: ['health-monitor', 'metrics-aggregator'],
        subject_pattern: `service.heartbeat.oanda-collector.${value.service.instance_id}`,
        retention_policy: 'workqueue',
        priority: needsAlert ? 'high' : 'normal'
    };
}

/**
 * Generate NATS subject for instance
 */
function generateSubject(instanceId) {
    return `service.heartbeat.oanda-collector.${instanceId}`;
}

module.exports = {
    schema: HeartbeatStreamSchema,
    process: processHeartbeatStream,
    generateSubject: generateSubject,
    contractName: 'heartbeat-stream',
    direction: 'to-central-hub',
    protocol: 'nats',
    subjectPattern: 'service.heartbeat.oanda-collector.{instance_id}'
};
