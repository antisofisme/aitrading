/**
 * Contract: Configuration Response from Central Hub
 * Direction: Central Hub → OANDA Collector
 * Protocol: HTTP REST
 * Endpoint: GET /config/{service_name}
 */

const Joi = require('joi');

const ConfigurationResponseSchema = Joi.object({
    // Response metadata
    config_version: Joi.string().required(),
    service_name: Joi.string().required(),
    timestamp: Joi.number().integer().required(),

    // Configuration sections
    configuration: Joi.object({
        // OANDA API settings
        oanda: Joi.object({
            environment: Joi.string().valid('practice', 'live').required(),
            api_version: Joi.string().default('v3'),
            timeout: Joi.number().integer().min(10).max(120).default(30),
            max_retries: Joi.number().integer().min(1).max(10).default(3),

            rate_limits: Joi.object({
                max_streams_per_ip: Joi.number().integer().default(20),
                max_requests_per_second: Joi.number().integer().default(120)
            })
        }),

        // Streaming configuration
        streaming: Joi.object({
            instruments: Joi.object().pattern(
                Joi.string(), // instrument category (forex, commodities, etc.)
                Joi.array().items(Joi.string())
            ).required(),
            heartbeat_interval: Joi.number().integer().default(5),
            reconnect_delay: Joi.number().integer().default(5),
            max_reconnect_attempts: Joi.number().integer().default(10)
        }),

        // NATS messaging
        nats: Joi.object({
            url: Joi.string().uri().required(),
            cluster_id: Joi.string().required(),
            subjects: Joi.object({
                pricing: Joi.string().required(),
                candles: Joi.string().required(),
                heartbeat: Joi.string().required()
            }).required()
        }),

        // Failover settings
        failover: Joi.object({
            enabled: Joi.boolean().default(true),
            health_check_interval: Joi.number().integer().default(60),
            max_failures_before_switch: Joi.number().integer().default(3),
            cooldown_period: Joi.number().integer().default(300)
        })
    }).required(),

    // Update instructions
    update_instructions: Joi.object({
        requires_restart: Joi.boolean().default(false),
        priority: Joi.string().valid('low', 'medium', 'high').default('medium'),
        apply_immediately: Joi.boolean().default(true)
    }).optional()
});

/**
 * Process configuration response from Central Hub
 */
function processConfigurationResponse(inputData, context = {}) {
    // Validate input
    const { error, value } = ConfigurationResponseSchema.validate(inputData);
    if (error) {
        throw new Error(`Contract validation failed: ${error.details[0].message}`);
    }

    // Extract and prepare configuration
    const configData = {
        ...value,
        received_at: Date.now(),
        applied: false
    };

    return {
        type: 'configuration_response',
        data: configData,
        routing_targets: ['config-manager'],
        requires_restart: value.update_instructions?.requires_restart || false
    };
}

module.exports = {
    schema: ConfigurationResponseSchema,
    process: processConfigurationResponse,
    contractName: 'configuration-response',
    direction: 'from-central-hub',
    protocol: 'http-rest'
};
