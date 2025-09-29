/**
 * Central Hub Contract: Configuration Request (Inbound)
 * Pattern: many-to-one (services → central-hub)
 * Transport: HTTP REST
 *
 * Services request configuration data dari Central Hub
 */

const Joi = require('joi');

/**
 * Input validation schema untuk configuration request
 */
const ConfigurationRequestSchema = Joi.object({
    // Configuration request parameters
    service_name: Joi.string().required(),
    config_scope: Joi.string().valid('service-specific', 'shared', 'environment', 'all').default('service-specific'),
    environment: Joi.string().valid('development', 'staging', 'production').required(),

    // Specific configuration keys (optional)
    config_keys: Joi.array().items(Joi.string()).optional(),

    // Request metadata
    version: Joi.string().default('latest'),
    format: Joi.string().valid('json', 'yaml', 'env').default('json'),
    include_secrets: Joi.boolean().default(false) // Requires special authorization
});

/**
 * Process configuration request
 */
function processConfigurationRequest(inputData, context = {}) {
    // Validate input
    const { error, value } = ConfigurationRequestSchema.validate(inputData);
    if (error) {
        throw new Error(`Configuration request validation failed: ${error.details[0].message}`);
    }

    const configRequest = value;

    // Add system metadata
    configRequest.request_id = `config-${Date.now()}`;
    configRequest.requested_at = Date.now();

    // Security check for secrets
    if (configRequest.include_secrets && !context.authorized_for_secrets) {
        throw new Error('Unauthorized to access configuration secrets');
    }

    return {
        type: 'configuration_request',
        data: configRequest,
        routing_targets: ['config-manager'], // Route to configuration manager
        response_format: 'configuration_response',
        metadata: {
            source_contract: 'configuration-request-to-central-hub',
            processing_time: Date.now(),
            correlation_id: context.correlationId || configRequest.request_id,
            cache_duration: 300000 // 5 minutes cache for config
        }
    };
}

const contractInfo = {
    name: 'configuration-request-to-central-hub',
    version: '1.0.0',
    description: 'Handles configuration requests from all services to Central Hub',
    transport_method: 'http-rest',
    direction: 'inbound',
    pattern: 'many-to-one',
    endpoints: {
        primary: 'GET /config/services/{service_name}',
        shared: 'GET /config/shared',
        environment: 'GET /config/environment/{env}'
    }
};

module.exports = {
    processConfigurationRequest,
    ConfigurationRequestSchema,
    contractInfo
};