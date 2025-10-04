/**
 * Contract: OANDA Collector Registration to Central Hub
 * Direction: OANDA Collector → Central Hub
 * Protocol: HTTP REST
 * Endpoint: POST /discovery/register
 */

const Joi = require('joi');

const OandaCollectorRegistrationSchema = Joi.object({
    // Service identification
    service_name: Joi.string().required().pattern(/^oanda-collector-\d+$/),
    host: Joi.string().required(),
    port: Joi.number().integer().min(1).max(65535).required(),
    protocol: Joi.string().valid('http', 'https').default('http'),

    // Service metadata
    version: Joi.string().default('1.0.0'),
    environment: Joi.string().valid('development', 'staging', 'production').required(),
    health_endpoint: Joi.string().default('/health'),

    // Service capabilities
    metadata: Joi.object({
        type: Joi.string().valid('oanda-collector').required(),
        capabilities: Joi.array().items(
            Joi.string().valid(
                'pricing-stream',
                'candles-historical',
                'multi-account',
                'auto-failover'
            )
        ).default(['pricing-stream', 'candles-historical']),

        // OANDA specific metadata
        oanda_config: Joi.object({
            environment: Joi.string().valid('practice', 'live').required(),
            active_accounts: Joi.number().integer().min(1).max(4).required(),
            max_streams: Joi.number().integer().min(1).max(20).default(20),
            instruments: Joi.array().items(Joi.string()).required()
        }).required(),

        max_connections: Joi.number().integer().min(1).default(100)
    }).required()
});

/**
 * Process service registration data
 */
function processOandaCollectorRegistration(inputData, context = {}) {
    // Validate input against contract
    const { error, value } = OandaCollectorRegistrationSchema.validate(inputData);
    if (error) {
        throw new Error(`Contract validation failed: ${error.details[0].message}`);
    }

    // Enrich registration data
    const registrationData = {
        ...value,
        registered_at: Date.now(),
        registration_id: `${value.service_name}-${Date.now()}`,
        url: `${value.protocol}://${value.host}:${value.port}`,
        service_category: 'data-ingestion'
    };

    return {
        type: 'oanda_collector_registration',
        data: registrationData,
        routing_targets: ['service-registry', 'discovery-cache'],
        response_format: 'service_registration_response'
    };
}

module.exports = {
    schema: OandaCollectorRegistrationSchema,
    process: processOandaCollectorRegistration,
    contractName: 'oanda-collector-registration',
    direction: 'to-central-hub',
    protocol: 'http-rest'
};
